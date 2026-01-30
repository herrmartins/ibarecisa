from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, BasePermission
from django.shortcuts import get_object_or_404
from django.db.models import Q, Sum, F, DecimalField
from django.db.models.functions import Coalesce
from django.utils import timezone
from decimal import Decimal

# Try to import DjangoFilterBackend, fall back to search filter if not available
try:
    from django_filters.rest_framework import DjangoFilterBackend
    HAS_DJANGO_FILTERS = True
except ImportError:
    from rest_framework.filters import SearchFilter as DjangoFilterBackend
    HAS_DJANGO_FILTERS = False

from treasury.models import (
    AccountingPeriod,
    TransactionModel,
    ReversalTransaction,
    CategoryModel,
)
from treasury.serializers import (
    AccountingPeriodSerializer,
    AccountingPeriodCloseSerializer,
    TransactionSerializer,
    TransactionListSerializer,
    TransactionCreateSerializer,
    TransactionUpdateSerializer,
    ReversalTransactionSerializer,
    ReversalCreateSerializer,
    CategorySerializer,
    CategoryDetailSerializer,
)
from treasury.services.period_service import PeriodService
from treasury.services.transaction_service import TransactionService


class IsTreasuryUser(BasePermission):
    """
    Permissão para usuários do departamento de tesouraria.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_treasurer or
            request.user.is_secretary or
            request.user.is_pastor or
            request.user.is_staff
        )


class IsAdminUser(BasePermission):
    """
    Permissão para administradores.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_staff or
            request.user.is_superuser or
            request.user.is_pastor
        )


class CategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar categorias de transações.

    * list: Lista todas as categorias
    * retrieve: Detalhes de uma categoria
    * create: Criar nova categoria (admin)
    * update: Atualizar categoria (admin)
    * destroy: Excluir categoria (admin)
    """
    queryset = CategoryModel.objects.all().order_by('name')
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

    def get_filter_backends(self):
        if HAS_DJANGO_FILTERS:
            return [DjangoFilterBackend, filters.SearchFilter]
        return [filters.SearchFilter]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return CategoryDetailSerializer
        return CategorySerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsAdminUser()]
        return [IsAuthenticated()]

    @action(detail=True, methods=['get'])
    def transactions(self, request, pk=None):
        """Lista todas as transações de uma categoria."""
        category = self.get_object()
        transactions = category.transactions.select_related(
            'user', 'category', 'accounting_period'
        ).order_by('-date', '-created_at')

        # Paginação
        page = self.paginate_queryset(transactions)
        if page is not None:
            serializer = TransactionListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = TransactionListSerializer(transactions, many=True)
        return Response(serializer.data)


class AccountingPeriodViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para visualizar períodos contábeis.

    * list: Lista todos os períodos
    * retrieve: Detalhes de um período
    """
    queryset = AccountingPeriod.objects.all().order_by('-month')
    serializer_class = AccountingPeriodSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    filterset_fields = ['status', 'year']
    ordering_fields = ['month', 'created_at']
    ordering = ['-month']

    def get_filter_backends(self):
        backends = [filters.OrderingFilter]
        if HAS_DJANGO_FILTERS:
            backends.insert(0, DjangoFilterBackend)
        return backends

    @action(detail=True, methods=['get'])
    def transactions(self, request, pk=None):
        """Lista todas as transações de um período."""
        period = self.get_object()
        transactions = period.transactions.select_related(
            'user', 'category', 'created_by'
        ).filter(transaction_type='original').order_by('-date', '-created_at')

        # Paginação
        page = self.paginate_queryset(transactions)
        if page is not None:
            serializer = TransactionListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = TransactionListSerializer(transactions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        """Fecha um período contábil."""
        period = self.get_object()

        if not period.can_be_closed:
            return Response(
                {'error': 'Apenas períodos abertos podem ser fechados.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = AccountingPeriodCloseSerializer(
            data=request.data,
            context={'period': period}
        )
        serializer.is_valid(raise_exception=True)

        try:
            notes = serializer.validated_data.get('notes', '')
            final_balance = period.close(user=request.user, notes=notes)

            return Response({
                'message': 'Período fechado com sucesso.',
                'closing_balance': float(final_balance),
                'period': AccountingPeriodSerializer(period).data,
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def reopen(self, request, pk=None):
        """Reabre um período fechado."""
        period = self.get_object()

        if not period.can_be_reopened:
            return Response(
                {'error': 'Este período não pode ser reaberto.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verificar permissão
        if not request.user.is_staff and not request.user.is_pastor:
            return Response(
                {'error': 'Você não tem permissão para reabrir períodos.'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            period.reopen(user=request.user)
            return Response({
                'message': 'Período reaberto com sucesso.',
                'period': AccountingPeriodSerializer(period).data,
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """Arquiva um período fechado."""
        period = self.get_object()

        if period.status != 'closed':
            return Response(
                {'error': 'Apenas períodos fechados podem ser arquivados.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verificar permissão
        if not request.user.is_staff and not request.user.is_pastor:
            return Response(
                {'error': 'Você não tem permissão para arquivar períodos.'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            period.archive()
            return Response({
                'message': 'Período arquivado com sucesso.',
                'period': AccountingPeriodSerializer(period).data,
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def current(self, request):
        """Retorna o período atual (mês corrente)."""
        today = timezone.now().date()
        current_month = today.replace(day=1)

        try:
            period = AccountingPeriod.objects.get(month=current_month)
            serializer = AccountingPeriodSerializer(period)
            return Response(serializer.data)
        except AccountingPeriod.DoesNotExist:
            return Response(
                {'error': 'Período atual não encontrado.'},
                status=status.HTTP_404_NOT_FOUND
            )


class TransactionViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar transações.

    * list: Lista transações com filtros
    * retrieve: Detalhes de uma transação
    * create: Criar nova transação
    * update: Atualizar transação (apenas período aberto)
    * destroy: Excluir transação (apenas período aberto)
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_positive', 'accounting_period', 'transaction_type']
    search_fields = ['description']
    ordering_fields = ['date', 'amount', 'created_at']
    ordering = ['-date', '-created_at']

    def get_filter_backends(self):
        backends = [filters.SearchFilter, filters.OrderingFilter]
        if HAS_DJANGO_FILTERS:
            backends.insert(0, DjangoFilterBackend)
        return backends

    def get_queryset(self):
        """Retorna queryset de transações com filtros adicionais."""
        queryset = TransactionModel.objects.select_related(
            'user', 'category', 'accounting_period', 'created_by'
        ).prefetch_related('reversals')

        # Filtro por período
        period_id = self.request.query_params.get('period_id')
        if period_id:
            queryset = queryset.filter(accounting_period_id=period_id)

        # Filtro por data (início e fim)
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)

        # Filtro por tipo (excluir reversals por padrão)
        show_reversals = self.request.query_params.get('show_reversals', 'false') == 'true'
        if not show_reversals:
            queryset = queryset.filter(transaction_type='original')

        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return TransactionListSerializer
        elif self.action == 'create':
            return TransactionCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return TransactionUpdateSerializer
        return TransactionSerializer

    def perform_create(self, serializer):
        """Define o criador da transação."""
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['get'])
    def reversals(self, request, pk=None):
        """Lista os estornos de uma transação."""
        transaction = self.get_object()
        reversals = transaction.reversals.select_related(
            'original_transaction',
            'reversal_transaction',
            'created_by',
            'authorized_by'
        ).order_by('-created_at')

        serializer = ReversalTransactionSerializer(reversals, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Retorna um resumo das transações com base nos filtros."""
        queryset = self.get_queryset()
        queryset = queryset.filter(transaction_type='original')

        # Calcular totais
        positive = queryset.filter(is_positive=True).aggregate(
            total=Coalesce(Sum('amount'), Decimal('0.00'), output_field=DecimalField())
        )['total']

        negative = queryset.filter(is_positive=False).aggregate(
            total=Coalesce(Sum('amount'), Decimal('0.00'), output_field=DecimalField())
        )['total']

        count = queryset.count()

        return Response({
            'total_positive': float(positive),
            'total_negative': float(negative),
            'net': float(positive - negative),
            'count': count,
        })


class ReversalViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para visualizar estornos.

    * list: Lista todos os estornos
    * retrieve: Detalhes de um estorno
    """
    queryset = ReversalTransaction.objects.select_related(
        'original_transaction',
        'reversal_transaction',
        'created_by',
        'authorized_by'
    ).order_by('-created_at')
    serializer_class = ReversalTransactionSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['original_transaction', 'reversal_transaction']

    def get_filter_backends(self):
        if HAS_DJANGO_FILTERS:
            return [DjangoFilterBackend]
        return []


class ReversalCreateView(APIView):
    """
    API para criar estornos de transações.

    POST /api/treasury/reversals/
    """
    permission_classes = [IsAuthenticated, IsTreasuryUser]

    def post(self, request):
        """Cria um novo estorno."""
        serializer = ReversalCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        try:
            reversal = serializer.save()
            response_serializer = ReversalTransactionSerializer(reversal)
            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class PeriodBalanceView(APIView):
    """
    API para consultar o saldo de um período específico.

    GET /api/treasury/reports/balance/<year>/<month>/
    """

    def get(self, request, year, month):
        """Retorna o saldo do período especificado."""
        try:
            from datetime import datetime
            month_date = datetime(year, month, 1).date()

            period = get_object_or_404(
                AccountingPeriod,
                month=month_date
            )

            service = PeriodService()
            balance = service.get_balance_at_date(period.last_day)

            return Response({
                'period': AccountingPeriodSerializer(period).data,
                'balance': float(balance),
                'opening_balance': float(period.opening_balance),
                'closing_balance': float(period.closing_balance) if period.closing_balance else None,
            })
        except ValueError:
            return Response(
                {'error': 'Data inválida.'},
                status=status.HTTP_400_BAD_REQUEST
            )


class MonthlyReportView(APIView):
    """
    API para gerar relatório mensal.

    GET /api/treasury/reports/monthly/<year>/<month>/
    """

    def get(self, request, year, month):
        """Gera relatório mensal detalhado."""
        try:
            from datetime import datetime
            month_date = datetime(year, month, 1).date()

            period = get_object_or_404(
                AccountingPeriod,
                month=month_date
            )

            service = TransactionService()
            summary = period.get_transactions_summary()

            # Transações por categoria
            transactions = period.transactions.filter(transaction_type='original')
            categories = {}
            for transaction in transactions:
                cat_name = transaction.category.name if transaction.category else 'Sem categoria'
                if cat_name not in categories:
                    categories[cat_name] = {
                        'positive': Decimal('0.00'),
                        'negative': Decimal('0.00'),
                        'count': 0,
                    }

                if transaction.is_positive:
                    categories[cat_name]['positive'] += transaction.amount
                else:
                    categories[cat_name]['negative'] += transaction.amount
                categories[cat_name]['count'] += 1

            # Formatar categorias para resposta
            categories_list = []
            for name, data in categories.items():
                categories_list.append({
                    'name': name,
                    'total_positive': float(data['positive']),
                    'total_negative': float(data['negative']),
                    'net': float(data['positive'] - data['negative']),
                    'count': data['count'],
                })

            return Response({
                'period': AccountingPeriodSerializer(period).data,
                'summary': {
                    'opening_balance': float(period.opening_balance),
                    'total_positive': float(summary['total_positive']),
                    'total_negative': float(summary['total_negative']),
                    'net': float(summary['net']),
                    'closing_balance': float(period.closing_balance) if period.closing_balance else None,
                    'transaction_count': summary['count'],
                },
                'by_category': categories_list,
            })
        except ValueError:
            return Response(
                {'error': 'Data inválida.'},
                status=status.HTTP_400_BAD_REQUEST
            )


class CurrentBalanceView(APIView):
    """
    API para consultar o saldo atual.

    GET /api/treasury/reports/current-balance/
    """

    def get(self, request):
        """Retorna o saldo atual."""
        service = PeriodService()
        balance = service.get_current_balance()

        # Período atual
        today = timezone.now().date()
        current_month = today.replace(day=1)
        try:
            current_period = AccountingPeriod.objects.get(month=current_month)
            period_data = AccountingPeriodSerializer(current_period).data
        except AccountingPeriod.DoesNotExist:
            period_data = None

        return Response({
            'current_balance': float(balance),
            'current_period': period_data,
        })
