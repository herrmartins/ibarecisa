from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.db.models import Q, Sum, F, DecimalField
from django.db.models.functions import Coalesce
from django.db import transaction
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
