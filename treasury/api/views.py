from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.db.models import Q, Sum, F, DecimalField, Count, Case, When, Value
from django.db.models.functions import Coalesce, TruncMonth
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, timedelta
from calendar import month_name, monthrange
import locale

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
    AuditLog,
    PeriodSnapshot,
    FrozenReport,
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

            # Salvar valores antigos para auditoria
            old_values = {
                'status': period.status,
                'closing_balance': None,
            }

            final_balance = period.close(user=request.user, notes=notes)

            # Log de auditoria
            AuditLog.log(
                action='period_closed',
                entity_type='AccountingPeriod',
                entity_id=period.id,
                user=request.user,
                old_values=old_values,
                new_values={
                    'status': period.status,
                    'closing_balance': float(final_balance),
                    'notes': notes,
                },
                description=f'Período {period.month_name}/{period.year} fechado. Saldo final: R$ {final_balance:.2f}',
                period_id=period.id,
                request=request,
            )

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
    @transaction.atomic
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
            # Salvar valores antigos para auditoria
            old_values = {
                'status': period.status,
                'closing_balance': float(period.closing_balance) if period.closing_balance else None,
                'closed_at': period.closed_at.isoformat() if period.closed_at else None,
                'closed_by': period.closed_by_id,
            }

            # Criar snapshot antes de reabrir
            service = PeriodService()
            reason = request.data.get('reason', f'Reabertura do período {period.month_name}/{period.year}')
            result = service.reopen_period_with_snapshot(
                period_id=period.id,
                user_id=request.user.id,
                reason=reason
            )

            # Log de auditoria
            AuditLog.log(
                action='period_reopened',
                entity_type='AccountingPeriod',
                entity_id=period.id,
                user=request.user,
                old_values=old_values,
                new_values={
                    'status': period.status,
                    'closing_balance': None,
                },
                description=f'Período {period.month_name}/{period.year} reaberto. Snapshot criado: {result["snapshot"].id}',
                snapshot_id=result['snapshot'].id,
                period_id=period.id,
                request=request,
            )

            return Response({
                'message': 'Período reaberto com sucesso.',
                'period': AccountingPeriodSerializer(period).data,
                'snapshot_id': str(result['snapshot'].id),
                'old_closing_balance': float(result['old_closing_balance']) if result['old_closing_balance'] else None,
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
            # Salvar valores antigos para auditoria
            old_values = {
                'status': period.status,
            }

            period.archive()

            # Log de auditoria
            AuditLog.log(
                action='period_archived',
                entity_type='AccountingPeriod',
                entity_id=period.id,
                user=request.user,
                old_values=old_values,
                new_values={
                    'status': period.status,
                },
                description=f'Período {period.month_name}/{period.year} arquivado',
                period_id=period.id,
                request=request,
            )

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

        # Filtro por período (aceita ambos: period_id e accounting_period)
        period_id = self.request.query_params.get('period_id') or self.request.query_params.get('accounting_period')
        if period_id:
            queryset = queryset.filter(accounting_period_id=period_id)

        # Filtro por data (início e fim)
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)

        # Filtro por tipo (excluir reversals por padrão, exceto para action summary)
        show_reversals = self.request.query_params.get('show_reversals', 'false') == 'true'
        is_summary_action = self.action == 'summary'
        if not show_reversals and not is_summary_action:
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

    def perform_destroy(self, instance):
        """Registra log de auditoria antes de deletar transação."""
        # Salvar valores para auditoria
        old_values = {
            'description': instance.description,
            'amount': float(instance.amount),
            'is_positive': instance.is_positive,
            'date': str(instance.date),
            'category_id': instance.category_id,
        }

        period_id = instance.accounting_period.id if instance.accounting_period else None

        # Log de auditoria
        AuditLog.log(
            action='transaction_deleted',
            entity_type='TransactionModel',
            entity_id=instance.id,
            user=self.request.user,
            old_values=old_values,
            new_values=None,
            description=f'Transação deletada: {instance.description}',
            period_id=period_id,
            request=self.request,
        )

        # Deletar a transação
        instance.delete()

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

        # Calcular totais
        positive = queryset.filter(is_positive=True).aggregate(
            total=Coalesce(Sum('amount'), Decimal('0.00'), output_field=DecimalField())
        )['total']

        negative = queryset.filter(is_positive=False).aggregate(
            total=Coalesce(Sum('amount'), Decimal('0.00'), output_field=DecimalField())
        )['total']

        # Net: positivas + negativas (negative já é negativo)
        net = positive + negative

        count = queryset.count()

        return Response({
            'total_positive': float(positive),
            'total_negative': float(negative),
            'net': float(net),
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

            # Buscar período, ou retornar dados vazios se não existir
            try:
                period = AccountingPeriod.objects.get(month=month_date)
            except AccountingPeriod.DoesNotExist:
                # Retornar dados vazios com valores zero
                return Response({
                    'period': None,
                    'summary': {
                        'opening_balance': 0.0,
                        'total_positive': 0.0,
                        'total_negative': 0.0,
                        'net': 0.0,
                        'closing_balance': None,
                        'transaction_count': 0,
                    },
                    'by_category': [],
                })

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
                    'net': float(data['positive'] + data['negative']),  # negative já é negativo
                    'count': data['count'],
                })

            # Calcular saldo inicial acumulado (soma de todos os períodos anteriores)
            accumulated_balance = float(period.opening_balance)
            # Nota: O opening_balance do período já deve herdar do período anterior
            # quando é criado automaticamente pelo TransactionCreateSerializer

            return Response({
                'period': AccountingPeriodSerializer(period).data,
                'summary': {
                    'opening_balance': float(accumulated_balance),
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


class AccumulatedBalanceBeforeView(APIView):
    """
    API para consultar o saldo acumulado antes de um período.

    GET /api/treasury/reports/accumulated-balance-before/<year>/<month>/
    """

    def get(self, request, year, month):
        """Retorna o saldo acumulado antes do período especificado."""
        from datetime import date

        target_month = date(year, month, 1)

        # Buscar todos os períodos anteriores ao mês alvo
        previous_periods = AccountingPeriod.objects.filter(
            month__lt=target_month
        ).order_by('month')

        # Calcular saldo acumulado
        accumulated = Decimal('0.00')
        for period in previous_periods:
            summary = period.get_transactions_summary()
            total_pos = Decimal(str(summary.get('total_positive', 0)))
            total_neg = Decimal(str(summary.get('total_negative', 0)))
            net = total_pos + total_neg
            # Se tem closing_balance, usa ele
            if period.closing_balance is not None:
                accumulated = period.closing_balance
            else:
                accumulated += net

        return Response({
            'accumulated_balance': float(accumulated),
        })


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para visualizar logs de auditoria.

    * list: Lista todos os logs com filtros
    * retrieve: Detalhes de um log
    """
    queryset = AuditLog.objects.all().order_by('-timestamp')
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination

    def get_queryset(self):
        """Retorna queryset com filtros."""
        queryset = AuditLog.objects.all().order_by('-timestamp')

        # Filtro por ação
        action = self.request.query_params.get('action')
        if action:
            queryset = queryset.filter(action=action)

        # Filtro por tipo de entidade
        entity_type = self.request.query_params.get('entity_type')
        if entity_type:
            queryset = queryset.filter(entity_type=entity_type)

        # Filtro por usuário (user_id)
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)

        # Filtro por período
        period_id = self.request.query_params.get('period_id')
        if period_id:
            queryset = queryset.filter(period_id=period_id)

        # Filtro por data (início)
        date_from = self.request.query_params.get('date_from')
        if date_from:
            queryset = queryset.filter(timestamp__gte=date_from)

        # Filtro por data (fim)
        date_to = self.request.query_params.get('date_to')
        if date_to:
            queryset = queryset.filter(timestamp__lte=date_to)

        return queryset

    def list(self, request, *args, **kwargs):
        """Retorna lista de logs formatada com paginação."""
        queryset = self.get_queryset()

        # Configurar paginação
        paginator = PageNumberPagination()
        paginator.page_size = 20  # 20 logs por página
        paginator.page_size_query_param = 'page_size'

        # Paginar queryset
        page = paginator.paginate_queryset(queryset, request)

        # Formatar dados manualmente
        logs = []
        for log in page:
            logs.append({
                'id': str(log.id),
                'timestamp': log.timestamp.isoformat(),
                'user_name': log.user_name or 'Sistema',
                'action': log.action,
                'action_label': log.get_action_display(),
                'entity_type': log.entity_type,
                'entity_type_label': log.get_entity_type_display(),
                'entity_id': log.entity_id,
                'description': log.description,
                'old_values': log.old_values,
                'new_values': log.new_values,
                'period_id': log.period_id,
                'snapshot_id': str(log.snapshot_id) if log.snapshot_id else None,
                'ip_address': log.ip_address,
            })

        return paginator.get_paginated_response(logs)


class FrozenReportViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para FrozenReports (relatórios congelados).

    Apenas leitura - relatórios não podem ser alterados ou deletados.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = None  # Usaremos formatação manual

    def get_queryset(self):
        """Retorna FrozenReports filtráveis."""
        queryset = FrozenReport.objects.select_related('period', 'created_by').all()

        # Filtros
        period_id = self.request.query_params.get('period_id')
        report_type = self.request.query_params.get('report_type')

        if period_id:
            queryset = queryset.filter(period_id=period_id)
        if report_type:
            queryset = queryset.filter(report_type=report_type)

        return queryset

    def list(self, request, *args, **kwargs):
        """Lista relatórios congelados."""
        queryset = self.get_queryset()

        # Paginação
        paginator = PageNumberPagination()
        paginator.page_size = 20
        page = paginator.paginate_queryset(queryset, request)

        reports = []
        for report in page:
            reports.append({
                'id': str(report.id),
                'period': {
                    'id': report.period.id,
                    'month_name': report.period.month_name,
                    'year': report.period.year,
                },
                'report_type': report.report_type,
                'report_type_label': report.get_report_type_display(),
                'pdf_file': report.pdf_file.url if report.pdf_file else None,
                'pdf_hash': report.pdf_hash,
                'closing_balance': float(report.closing_balance),
                'total_positive': float(report.total_positive),
                'total_negative': float(report.total_negative),
                'transaction_count': report.transaction_count,
                'created_at': report.created_at.isoformat(),
                'created_by': report.created_by.get_full_name() if report.created_by else 'Sistema',
                'is_recovered': report.is_recovered,
                'replaces_report_id': str(report.replaces_report.id) if report.replaces_report else None,
            })

        return paginator.get_paginated_response(reports)

    def retrieve(self, request, *args, **kwargs):
        """Detalhes de um relatório congelado."""
        report = self.get_object()

        verification = report.verify()

        return Response({
            'id': str(report.id),
            'period': {
                'id': report.period.id,
                'month_name': report.period.month_name,
                'year': report.period.year,
                'status': report.period.status,
            },
            'report_type': report.report_type,
            'report_type_label': report.get_report_type_display(),
            'pdf_file': report.pdf_file.url if report.pdf_file else None,
            'pdf_hash': report.pdf_hash,
            'verification': verification,
            'closing_balance': float(report.closing_balance),
            'total_positive': float(report.total_positive),
            'total_negative': float(report.total_negative),
            'transaction_count': report.transaction_count,
            'created_at': report.created_at.isoformat(),
            'created_by': report.created_by.get_full_name() if report.created_by else 'Sistema',
            'is_recovered': report.is_recovered,
            'replaces_report_id': str(report.replaces_report.id) if report.replaces_report else None,
        })

    @action(detail=True, methods=['get'])
    def verify(self, request, *args, **kwargs):
        """
        Verifica integridade do PDF.

        Retorna:
        - valid: True se hash confere
        - stored_hash: Hash armazenado
        - current_hash: Hash atual do PDF
        """
        report = self.get_object()
        verification = report.verify()
        return Response(verification)

    @action(detail=True, methods=['post'])
    def recover(self, request, *args, **kwargs):
        """
        Recupera PDF original a partir do AuditLog.

        Cria um novo FrozenReport marcado como recuperado.
        """
        report = self.get_object()

        # Verificar primeiro
        verification = report.verify()
        if verification['valid']:
            return Response({
                'message': 'PDF íntegro, não é necessário recuperar.',
                'verification': verification
            }, status=400)

        # Recuperar
        try:
            recovered = report.recover_from_audit()
            return Response({
                'message': 'PDF recuperado com sucesso.',
                'recovered_id': str(recovered.id),
                'original_verification': verification
            })
        except Exception as e:
            return Response({
                'message': 'Erro ao recuperar PDF.',
                'error': str(e)
            }, status=500)


class ReceiptOCRView(APIView):
    """
    API para extrair dados de comprovantes usando OCR/LLM.

    POST /api/treasury/ocr/receipt/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Processa um comprovante e extrai os dados."""
        from treasury.services.ocr_service import ReceiptOCRService

        # Verificar se foi enviado arquivo
        if 'receipt' not in request.FILES:
            return Response(
                {'error': 'Envie o arquivo no campo "receipt".'},
                status=status.HTTP_400_BAD_REQUEST
            )

        receipt_file = request.FILES['receipt']

        # Validar tipo de arquivo
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.pdf']
        file_name = receipt_file.name.lower()
        if not any(file_name.endswith(ext) for ext in allowed_extensions):
            return Response(
                {'error': 'Tipo de arquivo não suportado. Use: JPG, PNG ou PDF.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validar tamanho (máximo 10MB)
        max_size = 10 * 1024 * 1024
        if receipt_file.size > max_size:
            return Response(
                {'error': 'Arquivo muito grande. Tamanho máximo: 10MB.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Processar OCR
            service = ReceiptOCRService()
            result = service.extract_from_receipt(receipt_file)

            # Verificar se houve erro
            if 'error' in result:
                return Response(
                    {'error': result['error']},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # Retornar dados extraídos
            return Response({
                'description': result['description'],
                'amount': result['amount'],
                'date': result['date'],
                'category_name': result['category_name'],
                'category_id': result['category_id'],
                'is_positive': result['is_positive'],
                'confidence': result['confidence'],
                'raw_data': result.get('raw_data', {}),
            })

        except Exception as e:
            return Response(
                {'error': f'Erro ao processar comprovante: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ReceiptTransactionCreateView(APIView):
    """
    API para criar transação a partir de comprovante com OCR.

    POST /api/treasury/transactions/from-receipt/
    """
    permission_classes = [IsAuthenticated, IsTreasuryUser]

    def post(self, request):
        """Cria uma transação processando o comprovante e permitindo edição."""
        from treasury.services.ocr_service import ReceiptOCRService

        # Verificar se foi enviado arquivo
        if 'receipt' not in request.FILES:
            return Response(
                {'error': 'Envie o arquivo no campo "receipt".'},
                status=status.HTTP_400_BAD_REQUEST
            )

        receipt_file = request.FILES['receipt']

        # Validar tipo de arquivo
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.pdf']
        file_name = receipt_file.name.lower()
        if not any(file_name.endswith(ext) for ext in allowed_extensions):
            return Response(
                {'error': 'Tipo de arquivo não suportado. Use: JPG, PNG ou PDF.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validar tamanho (máximo 10MB)
        max_size = 10 * 1024 * 1024
        if receipt_file.size > max_size:
            return Response(
                {'error': 'Arquivo muito grande. Tamanho máximo: 10MB.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verificar se deve criar diretamente ou apenas extrair
        create_directly = request.data.get('create', 'false') == 'true'

        try:
            # Processar OCR
            service = ReceiptOCRService()
            result = service.extract_from_receipt(receipt_file)

            # Verificar se houve erro
            if 'error' in result:
                return Response(
                    {'error': result['error']},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # Se create_directly=True, criar a transação
            if create_directly:
                # Preparar dados para criação
                transaction_data = {
                    'description': request.data.get('description', result['description']),
                    'amount': request.data.get('amount', result['amount']),
                    'is_positive': request.data.get('is_positive', result['is_positive']),
                    'date': request.data.get('date', result['date']),
                    'category_id': request.data.get('category_id', result['category_id']),
                }

                # Validar dados
                from treasury.serializers import TransactionCreateSerializer
                serializer = TransactionCreateSerializer(
                    data=transaction_data,
                    context={'request': request}
                )
                serializer.is_valid(raise_exception=True)

                # Criar transação
                transaction = serializer.save()

                # Adicionar o comprovante como acquittance_doc
                if 'acquittance_doc' in request.FILES:
                    transaction.acquittance_doc = request.FILES['acquittance_doc']
                    transaction.save()

                return Response({
                    'message': 'Transação criada com sucesso.',
                    'transaction': TransactionSerializer(transaction).data,
                }, status=status.HTTP_201_CREATED)

            else:
                # Retornar dados extraídos para preview/edição
                return Response({
                    'description': result['description'],
                    'amount': result['amount'],
                    'date': result['date'],
                    'category_name': result['category_name'],
                    'category_id': result['category_id'],
                    'is_positive': result['is_positive'],
                    'confidence': result['confidence'],
                    'preview_mode': True,
                })

        except Exception as e:
            return Response(
                {'error': f'Erro ao processar: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ReceiptMultipleOCRView(APIView):
    """
    API para extrair múltiplas transações de uma imagem (listas, envelopes, urna).

    POST /api/treasury/ocr/receipt-multiple/
    """
    permission_classes = [IsAuthenticated, IsTreasuryUser]

    def post(self, request):
        """Processa uma imagem e extrai múltiplas transações."""
        from treasury.services.ocr_service import ReceiptOCRService

        # Verificar se foi enviado arquivo
        if 'receipt' not in request.FILES:
            return Response(
                {'error': 'Envie o arquivo no campo "receipt".'},
                status=status.HTTP_400_BAD_REQUEST
            )

        receipt_file = request.FILES['receipt']

        # Validar tamanho (10MB)
        if receipt_file.size > 10 * 1024 * 1024:
            return Response(
                {'error': 'Arquivo muito grande. Tamanho máximo: 10MB.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Processar OCR múltiplo
            service = ReceiptOCRService()
            result = service.extract_multiple_from_receipt(receipt_file)

            # Verificar se houve erro
            if 'error' in result:
                return Response(
                    {'error': result['error']},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Retornar transações extraídas
            return Response({
                'transactions': result['transactions'],
                'count': len(result['transactions']),
            })

        except Exception as e:
            return Response(
                {'error': f'Erro ao processar: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BatchTransactionCreateView(APIView):
    """
    API para criar múltiplas transações em lote.

    POST /api/treasury/transactions/batch/
    Body JSON: { "transactions": [...] }
    Body FormData: receipt (arquivo), transactions (string JSON)
    """
    permission_classes = [IsAuthenticated, IsTreasuryUser]

    def post(self, request):
        """Cria múltiplas transações."""
        from treasury.serializers import TransactionCreateSerializer
        import json

        # Verificar se é FormData (com arquivo) ou JSON
        receipt_file = request.FILES.get('receipt')
        transactions_str = request.data.get('transactions')

        if transactions_str:
            # FormData: parsear string JSON
            try:
                transactions_data = json.loads(transactions_str)
            except json.JSONDecodeError:
                return Response(
                    {'error': 'Formato de transações inválido.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            # JSON normal
            transactions_data = request.data.get('transactions', [])

        if not transactions_data:
            return Response(
                {'error': 'Envie pelo menos uma transação.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Salvar comprovante uma vez (se fornecido)
        receipt_path = None
        if receipt_file:
            from django.core.files.storage import default_storage
            # Salvar e obter o caminho
            receipt_path = default_storage.save(f'treasury/receipts/batch_{receipt_file.name}', receipt_file)

        created_transactions = []
        errors = []

        for idx, tx_data in enumerate(transactions_data):
            try:
                serializer = TransactionCreateSerializer(
                    data=tx_data,
                    context={'request': request}
                )
                serializer.is_valid(raise_exception=True)
                transaction = serializer.save()

                # Usar o mesmo caminho do comprovante para todas as transações
                if receipt_path:
                    transaction.acquittance_doc.name = receipt_path
                    transaction.save(update_fields=['acquittance_doc'])

                created_transactions.append(TransactionSerializer(transaction).data)
            except Exception as e:
                errors.append({
                    'index': idx,
                    'error': str(e),
                    'data': tx_data
                })

        return Response({
            'created': created_transactions,
            'created_count': len(created_transactions),
            'errors': errors,
            'errors_count': len(errors),
        }, status=status.HTTP_201_CREATED if created_transactions else status.HTTP_400_BAD_REQUEST)


# ============================================================================
# CHART API VIEWS
# ============================================================================

class CashflowChartView(APIView):
    """
    API para dados do gráfico de fluxo de caixa mensal.

    GET /api/treasury/charts/cashflow/?start_date=&end_date=
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Retorna dados de fluxo de caixa agrupados por mês."""
        try:
            # Parse dates
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')

            if not start_date:
                # Default: start of current year
                today = timezone.now().date()
                start_date = today.replace(month=1, day=1)
            else:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()

            if not end_date:
                # Default: today
                end_date = timezone.now().date()
            else:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

            # Get transactions grouped by month
            transactions = TransactionModel.objects.filter(
                date__gte=start_date,
                date__lte=end_date,
                transaction_type='original'
            ).annotate(
                month=TruncMonth('date')
            ).values('month').annotate(
                revenues=Sum(Case(When(is_positive=True, then=F('amount')), default=Decimal('0.00'), output_field=DecimalField())),
                expenses=Sum(Case(When(is_positive=False, then=F('amount')), default=Decimal('0.00'), output_field=DecimalField()))
            ).order_by('month')

            # Build response
            months = []
            revenues = []
            expenses = []
            balance = []
            running_balance = Decimal('0.00')

            # Get initial balance from transactions before start_date
            initial_balance = TransactionModel.objects.filter(
                date__lt=start_date,
                transaction_type='original'
            ).aggregate(
                initial_revenue=Sum(Case(When(is_positive=True, then=F('amount')), default=Decimal('0.00'), output_field=DecimalField())),
                initial_expense=Sum(Case(When(is_positive=False, then=F('amount')), default=Decimal('0.00'), output_field=DecimalField()))
            )
            running_balance = (initial_balance['initial_revenue'] or Decimal('0.00')) + (initial_balance['initial_expense'] or Decimal('0.00'))

            # Build lists from transactions (only months with data)
            for tx in transactions:
                month_label = self._get_month_name(tx['month'].month, tx['month'].year)
                months.append(month_label)

                rev = float(tx['revenues'] or Decimal('0.00'))
                exp = float(tx['expenses'] or Decimal('0.00'))
                revenues.append(rev)
                expenses.append(abs(exp))  # Show as positive for display

                running_balance += Decimal(str(rev)) + Decimal(str(exp))
                balance.append(float(running_balance))

            return Response({
                'categories': months,
                'series': [
                    {'name': 'Receitas', 'data': revenues},
                    {'name': 'Despesas', 'data': expenses},
                    {'name': 'Saldo Acumulado', 'data': balance}
                ]
            })

        except ValueError as e:
            return Response({'error': f'Formato de data inválido: {e}'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _get_month_name(self, month, year):
        """Retorna o nome do mês em português."""
        months_pt = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
        return f"{months_pt[month - 1]}/{str(year)[2:]}"


class RevenuesByCategoryChartView(APIView):
    """
    API para dados do gráfico de receitas por categoria.

    GET /api/treasury/charts/revenues-by-category/?start_date=&end_date=
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Retorna receitas agrupadas por categoria."""
        try:
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')

            if not start_date:
                today = timezone.now().date()
                start_date = today.replace(month=1, day=1)
            else:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()

            if not end_date:
                end_date = timezone.now().date()
            else:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

            # Get revenues by category
            categories = TransactionModel.objects.filter(
                date__gte=start_date,
                date__lte=end_date,
                is_positive=True,
                transaction_type='original'
            ).values(
                category_name=Coalesce('category__name', Value('Sem categoria'))
            ).annotate(
                total=Sum('amount')
            ).order_by('-total')

            labels = []
            values = []

            for cat in categories:
                labels.append(cat['category_name'])
                values.append(float(cat['total']))

            return Response({
                'labels': labels,
                'values': values,
                'total': sum(values)
            })

        except ValueError as e:
            return Response({'error': f'Formato de data inválido: {e}'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ExpensesByCategoryChartView(APIView):
    """
    API para dados do gráfico de despesas por categoria.

    GET /api/treasury/charts/expenses-by-category/?start_date=&end_date=
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Retorna despesas agrupadas por categoria (valores positivos)."""
        try:
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')

            if not start_date:
                today = timezone.now().date()
                start_date = today.replace(month=1, day=1)
            else:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()

            if not end_date:
                end_date = timezone.now().date()
            else:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

            # Get expenses by category - amount is already negative for expenses, so we negate to get positive
            categories = TransactionModel.objects.filter(
                date__gte=start_date,
                date__lte=end_date,
                is_positive=False,
                transaction_type='original'
            ).values(
                category_name=Coalesce('category__name', Value('Sem categoria'))
            ).annotate(
                total=Sum('amount')
            ).order_by('total')  # Order by total (negative to positive)

            labels = []
            values = []

            for cat in categories:
                labels.append(cat['category_name'])
                # Negate to get positive value for display
                values.append(abs(float(cat['total'])))

            # Reverse so highest values are first
            labels.reverse()
            values.reverse()

            return Response({
                'labels': labels,
                'values': values,
                'total': sum(values)
            })

        except ValueError as e:
            return Response({'error': f'Formato de data inválido: {e}'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MonthlyComparisonChartView(APIView):
    """
    API para dados do gráfico comparativo mensal.

    GET /api/treasury/charts/monthly-comparison/?start_date=&end_date=
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Retorna comparativo de receitas vs despesas por mês."""
        try:
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')

            if not start_date:
                today = timezone.now().date()
                start_date = today.replace(month=1, day=1)
            else:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()

            if not end_date:
                end_date = timezone.now().date()
            else:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

            # Get transactions grouped by month
            transactions = TransactionModel.objects.filter(
                date__gte=start_date,
                date__lte=end_date,
                transaction_type='original'
            ).annotate(
                month=TruncMonth('date')
            ).values('month').annotate(
                revenues=Sum(Case(When(is_positive=True, then=F('amount')), default=Decimal('0.00'), output_field=DecimalField())),
                expenses=Sum(Case(When(is_positive=False, then=F('amount')), default=Decimal('0.00'), output_field=DecimalField()))
            ).order_by('month')

            # Build lists from transactions (only months with data)
            months = []
            revenues = []
            expenses = []
            months_pt = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']

            for tx in transactions:
                month_label = f"{months_pt[tx['month'].month - 1]}/{str(tx['month'].year)[2:]}"
                months.append(month_label)
                revenues.append(float(tx['revenues'] or Decimal('0.00')))
                expenses.append(abs(float(tx['expenses'] or Decimal('0.00'))))

            return Response({
                'categories': months,
                'series': [
                    {'name': 'Receitas', 'data': revenues},
                    {'name': 'Despesas', 'data': expenses}
                ]
            })

        except ValueError as e:
            return Response({'error': f'Formato de data inválido: {e}'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BalanceHistoryChartView(APIView):
    """
    API para dados do gráfico de histórico de saldo.

    GET /api/treasury/charts/balance-history/?start_date=&end_date=
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Retorna histórico de saldo por período."""
        try:
            # Aceita tanto start_date/end_date quanto period_start/period_end
            period_start = request.query_params.get('start_date') or request.query_params.get('period_start')
            period_end = request.query_params.get('end_date') or request.query_params.get('period_end')

            if not period_start:
                # Default: 6 months ago
                today = timezone.now().date()
                if today.month > 6:
                    period_start = today.replace(month=today.month - 6, day=1)
                else:
                    period_start = today.replace(year=today.year - 1, month=today.month - 6 + 12, day=1)
            else:
                period_start = datetime.strptime(period_start, '%Y-%m-%d').date()

            if not period_end:
                period_end = timezone.now().date()
            else:
                period_end = datetime.strptime(period_end, '%Y-%m-%d').date()

            # Ajustar data final para excluir meses parciais
            # Se a data final não for o último dia do mês, usar o último dia do mês anterior
            last_day_of_month = monthrange(period_end.year, period_end.month)[1]
            if period_end.day < last_day_of_month:
                # Usar o último dia do mês anterior
                if period_end.month == 1:
                    period_end = period_end.replace(year=period_end.year - 1, month=12, day=31)
                else:
                    period_end = period_end.replace(month=period_end.month - 1, day=monthrange(period_end.year, period_end.month - 1)[1])

            # Get periods within range
            periods = AccountingPeriod.objects.filter(
                month__gte=period_start.replace(day=1),
                month__lte=period_end.replace(day=1)
            ).order_by('month')

            labels = []
            values = []

            # Get accumulated balance from before the first period
            accumulated = Decimal('0.00')
            periods_list = list(periods)
            if periods_list:
                first_period = periods_list[0]
                # Look for previous closed periods
                prev_period = AccountingPeriod.objects.filter(
                    month__lt=first_period.month,
                    closing_balance__isnull=False
                ).order_by('-month').first()
                if prev_period and prev_period.closing_balance is not None:
                    accumulated = prev_period.closing_balance

            for period in periods_list:
                labels.append(period.month_name)
                # Use closing_balance if available, otherwise calculate current
                if period.closing_balance is not None:
                    accumulated = period.closing_balance
                    values.append(float(accumulated))
                else:
                    # For open periods, calculate balance from transactions
                    summary = period.get_transactions_summary()
                    if summary['count'] > 0:
                        accumulated += float(summary['net'])
                    else:
                        # No transactions, keep accumulated balance
                        pass
                    values.append(float(accumulated))

            return Response({
                'categories': labels,
                'values': values
            })

        except ValueError as e:
            return Response({'error': f'Formato de data inválido: {e}'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class KPICardsView(APIView):
    """
    API para dados dos cards KPI.

    GET /api/treasury/charts/kpi/?start_date=&end_date=
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Retorna dados dos KPIs para o período especificado."""
        try:
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')

            if not start_date:
                today = timezone.now().date()
                start_date = today.replace(month=1, day=1)
            else:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()

            if not end_date:
                end_date = timezone.now().date()
            else:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

            # Calculate current period stats
            transactions = TransactionModel.objects.filter(
                date__gte=start_date,
                date__lte=end_date,
                transaction_type='original'
            )

            total_revenues = transactions.filter(is_positive=True).aggregate(
                total=Sum('amount')
            )['total'] or Decimal('0.00')

            total_expenses = transactions.filter(is_positive=False).aggregate(
                total=Sum('amount')
            )['total'] or Decimal('0.00')

            current_net = total_revenues + total_expenses

            # Calculate previous period for variation
            days_diff = (end_date - start_date).days
            prev_end = start_date - timedelta(days=1)
            prev_start = prev_end - timedelta(days=days_diff)

            prev_transactions = TransactionModel.objects.filter(
                date__gte=prev_start,
                date__lte=prev_end,
                transaction_type='original'
            )

            prev_revenues = prev_transactions.filter(is_positive=True).aggregate(
                total=Sum('amount')
            )['total'] or Decimal('0.00')

            prev_expenses = prev_transactions.filter(is_positive=False).aggregate(
                total=Sum('amount')
            )['total'] or Decimal('0.00')

            prev_net = prev_revenues + prev_expenses

            # Get current balance
            service = PeriodService()
            current_balance = service.get_current_balance()

            # Calculate variation percentage
            if prev_net != 0:
                variation = ((current_net - prev_net) / abs(prev_net)) * 100
            else:
                variation = 0 if current_net == 0 else 100

            return Response({
                'total_revenues': float(total_revenues),
                'total_expenses': abs(float(total_expenses)),  # Show as positive
                'current_balance': float(current_balance),
                'current_net': float(current_net),
                'variation': round(variation, 2),
                'period': {
                    'start': start_date.strftime('%d/%m/%Y'),
                    'end': end_date.strftime('%d/%m/%Y')
                }
            })

        except ValueError as e:
            return Response({'error': f'Formato de data inválido: {e}'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AIInsightsView(APIView):
    """
    API para gerar insights financeiros usando IA com cache inteligente.

    - Desenvolvimento (DEBUG=True): Usa Ollama com ministral-3:8b
    - Produção (DEBUG=False): Usa Mistral API com mistral-small-latest
    - Cache: Insights são salvos e reutilizados se o count de transações não mudou
    - Force: Use force=true para regenerar ignorando o cache

    POST /api/treasury/charts/ai-insights/
    Body: { start_date: "2025-01-01", end_date: "2025-01-31", force: false }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Gera insights financeiros usando cache inteligente."""
        import logging
        import os
        from django.conf import settings

        logger = logging.getLogger(__name__)

        # Desenvolvimento: Ollama, Produção: Mistral API
        use_mistral_api = not getattr(settings, 'DEBUG', True)
        debug_mode = getattr(settings, 'DEBUG', True)
        api_name = "Mistral API" if use_mistral_api else "Ollama"
        logger.info(f'AI Insights request - usando {api_name} (DEBUG={debug_mode})')

        # Coletar parâmetros
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')
        force_regenerate = request.data.get('force', False)

        if not start_date or not end_date:
            logger.warning('Request sem datas start_date/end_date')
            return Response({'error': 'Datas start_date e end_date são obrigatórias'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            logger.info(f'Período solicitado: {start_date} até {end_date}, force={force_regenerate}')
        except ValueError as e:
            logger.error(f'Formato de data inválido: {e}')
            return Response({'error': 'Formato de data inválido. Use YYYY-MM-DD'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Buscar transações do período
            transactions = TransactionModel.objects.filter(
                date__gte=start_date,
                date__lte=end_date,
                transaction_type='original'
            ).order_by('-date')[:100]  # Limitar a 100 transações mais recentes

            if not transactions:
                logger.warning(f'Nenhuma transação encontrada no período {start_date} até {end_date}')
                return Response({'error': 'Nenhuma transação encontrada no período'}, status=status.HTTP_400_BAD_REQUEST)

            transactions_count = len(transactions)
            logger.info(f'Processando {transactions_count} transações')

            # Verificar cache existente
            from treasury.models import AIInsight

            existing_insight = AIInsight.objects.filter(
                start_date=start_date,
                end_date=end_date
            ).first()

            # Retornar cache se válido e não forçado
            if existing_insight and not force_regenerate:
                if existing_insight.is_still_valid(transactions_count):
                    logger.info(f'Retornando insight em cache de {existing_insight.generated_at}')
                    return Response({
                        'insights': existing_insight.content,
                        'generated_at': existing_insight.generated_at.isoformat(),
                        'cached': True,
                        'is_stale': existing_insight.is_stale
                    })
                else:
                    logger.info(f'Cache invalidado: count mudou de {existing_insight.transactions_count} para {transactions_count}')

            # Preparar resumo dos dados para a IA
            summary = self._prepare_summary_for_ai(transactions, start_date, end_date)
            logger.info(f'Summary preparado: {len(summary)} caracteres')

            # Gerar insights com Ollama (dev) ou Mistral API (prod)
            if use_mistral_api:
                insights = self._generate_insights_with_mistral(summary)
            else:
                insights = self._generate_insights_with_ollama(summary)

            logger.info(f'Insights gerados com sucesso: {len(insights)} caracteres')

            # Salvar no banco (atualiza se existe)
            model_used = os.environ.get('OLLAMA_INSIGHTS_MODEL', 'ministral-3:8b') if not use_mistral_api else getattr(settings, 'MISTRAL_MODEL', 'mistral-small-latest')

            if existing_insight:
                # Atualiza existente
                existing_insight.content = insights
                existing_insight.transactions_count = transactions_count
                existing_insight.model_used = model_used
                existing_insight.debug_mode = debug_mode
                existing_insight.save()
                logger.info(f'Insight atualizado no banco (id={existing_insight.id})')
            else:
                # Cria novo
                new_insight = AIInsight.objects.create(
                    start_date=start_date,
                    end_date=end_date,
                    content=insights,
                    transactions_count=transactions_count,
                    model_used=model_used,
                    debug_mode=debug_mode
                )
                logger.info(f'Insight salvo no banco (id={new_insight.id})')

            return Response({
                'insights': insights,
                'generated_at': timezone.now().isoformat(),
                'cached': False
            })

        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            logger.error(f'Erro ao gerar insights: {e}\n{error_trace}')
            return Response({
                'error': str(e),
                'insights': f'Erro ao gerar insights: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _generate_insights_with_ollama(self, summary: str) -> str:
        """Gera insights usando Ollama com ministral-3:8b."""
        import logging
        import os
        import requests
        from django.conf import settings

        logger = logging.getLogger(__name__)

        ollama_base_url = os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')
        ollama_model = os.environ.get('OLLAMA_INSIGHTS_MODEL', 'ministral-3:8b')

        logger.info(f'Gerando insights com Ollama: model={ollama_model}, url={ollama_base_url}')

        payload = {
            'model': ollama_model,
            'messages': [
                {
                    'role': 'system',
                    'content': 'Você é um assistente financeiro especializado em análise de dados financeiros de igrejas. '
                    'Forneça insights práticos e acionáveis em formato markdown, usando linguagem clara e objetiva. '
                    'Use emojis para tornar o texto mais visual. '
                    'Estruture sua resposta com: 📊 Visão Geral, 💡 Insights Principais, ⚠️ Pontos de Atenção, 🎯 Recomendações, 📖 Palavra de Sabedoria. '
                    'Na seção "📖 Palavra de Sabedoria", inclua 1-2 versículos bíblicos relevantes sobre fidelidade, mordomia e sabedoria financeira, '
                    'com uma breve exposição/princípio prático que se aplica à situação financeira analisada.'
                },
                {
                    'role': 'user',
                    'content': f'Analise os seguintes dados financeiros:\n\n{summary}'
                }
            ],
            'stream': False,
            'options': {
                'num_predict': 1200,
                'temperature': 0.7
            }
        }

        try:
            response = requests.post(
                f'{ollama_base_url}/api/chat',
                json=payload,
                timeout=120
            )
            logger.info(f'Ollama response status: {response.status_code}')
        except requests.exceptions.ConnectionError as e:
            error_msg = f'Ollama não está respondendo em {ollama_base_url}. Verifique se o serviço está rodando.'
            logger.error(f'ConnectionError: {error_msg} - {e}')
            raise Exception(error_msg)
        except requests.exceptions.Timeout as e:
            error_msg = f'Ollama demorou muito para responder (timeout 120s). Tente reduzir o período ou usar um modelo mais rápido.'
            logger.error(f'Timeout: {error_msg} - {e}')
            raise Exception(error_msg)
        except requests.exceptions.RequestException as e:
            error_msg = f'Erro ao comunicar com Ollama: {type(e).__name__}: {e}'
            logger.error(f'RequestException: {error_msg}')
            raise Exception(error_msg)

        if response.status_code != 200:
            error_detail = response.text[:500] if response.text else 'sem detalhes'
            error_msg = f'Ollama retornou erro {response.status_code}: {error_detail}'
            logger.error(f'Ollama HTTP error: {error_msg}')
            raise Exception(error_msg)

        try:
            result = response.json()
        except ValueError as e:
            error_msg = f'Resposta inválida do Ollama (não é JSON): {response.text[:200]}'
            logger.error(f'JSON decode error: {error_msg}')
            raise Exception(error_msg)

        insights = result.get('message', {}).get('content', '')

        if not insights:
            error_msg = f'Ollama retornou resposta vazia. Resposta completa: {result}'
            logger.error(f'Empty insights: {error_msg}')
            raise Exception('Resposta vazia da IA - tente novamente')

        logger.info(f'Insights gerados com sucesso: {len(insights)} caracteres')
        return insights

    def _generate_insights_with_mistral(self, summary: str) -> str:
        """Gera insights usando Mistral API com mistral-small-latest."""
        import logging
        from django.conf import settings

        logger = logging.getLogger(__name__)

        logger.info('Gerando insights com Mistral API')

        try:
            from mistralai import Mistral
        except ImportError:
            error_msg = 'SDK Mistral não instalado. Execute: pip install mistralai'
            logger.error(f'ImportError: {error_msg}')
            raise Exception(error_msg)

        api_key = getattr(settings, 'MISTRAL_API_KEY', None)
        if not api_key:
            error_msg = 'MISTRAL_API_KEY não configurado nas variáveis de ambiente'
            logger.error(f'Missing API key: {error_msg}')
            raise Exception(error_msg)

        model = getattr(settings, 'MISTRAL_MODEL', 'mistral-small-latest')
        logger.info(f'Usando modelo Mistral: {model}')

        try:
            client = Mistral(api_key=api_key)

            chat_response = client.chat.complete(
                model=model,
                messages=[
                    {
                        'role': 'system',
                        'content': 'Você é um assistente financeiro especializado em análise de dados financeiros de igrejas. '
                        'Forneça insights práticos e acionáveis em formato markdown, usando linguagem clara e objetiva. '
                        'Use emojis para tornar o texto mais visual. '
                        'Estruture sua resposta com: 📊 Visão Geral, 💡 Insights Principais, ⚠️ Pontos de Atenção, 🎯 Recomendações, 📖 Palavra de Sabedoria. '
                        'Na seção "📖 Palavra de Sabedoria", inclua 1-2 versículos bíblicos relevantes sobre fidelidade, mordomia e sabedoria financeira, '
                        'com uma breve exposição/princípio prático que se aplica à situação financeira analisada.'
                    },
                    {
                        'role': 'user',
                        'content': f'Analise os seguintes dados financeiros:\n\n{summary}'
                    }
                ],
                max_tokens=1200,
                temperature=0.7
            )

            insights = chat_response.choices[0].message.content

            if not insights:
                error_msg = 'Mistral retornou resposta vazia - tente novamente'
                logger.error(f'Empty response from Mistral: {error_msg}')
                raise Exception(error_msg)

            logger.info(f'Insights gerados com sucesso: {len(insights)} caracteres')
            return insights

        except Exception as e:
            if '401' in str(e) or 'authentication' in str(e).lower():
                error_msg = f'Erro de autenticação na API Mistral. Verifique MISTRAL_API_KEY: {e}'
            elif 'rate limit' in str(e).lower():
                error_msg = f'Limite de taxa da API Mistral atingido. Tente novamente em alguns minutos: {e}'
            elif 'timeout' in str(e).lower():
                error_msg = f'Timeout na API Mistral. Tente novamente: {e}'
            else:
                error_msg = f'Erro ao comunicar com Mistral API: {type(e).__name__}: {e}'
            logger.error(f'Mistral API error: {error_msg}')
            raise Exception(error_msg)

    def _prepare_summary_for_ai(self, transactions, start_date, end_date):
        """Prepara um resumo dos dados para enviar à IA."""
        from collections import defaultdict

        # Agrupar por categoria
        category_totals = defaultdict(lambda: {'revenue': Decimal('0'), 'expense': Decimal('0'), 'count': 0})

        for tx in transactions:
            cat = tx.category.name if tx.category else 'Sem Categoria'
            if tx.is_positive:
                category_totals[cat]['revenue'] += tx.amount
            else:
                category_totals[cat]['expense'] += tx.amount  # Já é negativo
            category_totals[cat]['count'] += 1

        # Calcular totais gerais
        total_revenue = sum(d['revenue'] for d in category_totals.values())
        total_expense = sum(d['expense'] for d in category_totals.values())  # Já é negativo
        net_balance = total_revenue + total_expense

        # Formatar resumo
        summary = f"""Período Analisado: {start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}

RESUMO FINANCEIRO:
• Total de Receitas: R$ {float(total_revenue):,.2f}
• Total de Despesas: R$ {abs(float(total_expense)):,.2f}
• Saldo Líquido: R$ {float(net_balance):,.2f}
• Número de Transações: {len(transactions)}

TOP RECEITAS POR CATEGORIA:
"""

        # Adicionar top categorias de receita
        revenue_by_cat = sorted(
            [(cat, float(data['revenue'])) for cat, data in category_totals.items()],
            key=lambda x: x[1],
            reverse=True
        )[:5]

        for cat, total in revenue_by_cat:
            if total > 0:
                summary += f"• {cat}: R$ {total:,.2f}\n"

        summary += "\nTOP DESPESAS POR CATEGORIA:\n"

        # Adicionar top categorias de despesa
        expense_by_cat = sorted(
            [(cat, abs(float(data['expense']))) for cat, data in category_totals.items()],
            key=lambda x: x[1],
            reverse=True
        )[:5]

        for cat, total in expense_by_cat:
            if total > 0:
                summary += f"• {cat}: R$ {total:,.2f}\n"

        summary += "\nForneça insights sobre estes dados, destacando tendências, padrões e recomendações."

        return summary
