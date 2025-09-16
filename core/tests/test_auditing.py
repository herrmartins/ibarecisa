from django.test import TestCase
from django.contrib.auth import get_user_model
from reversion.models import Revision, Version
from secretarial.models import MeetingMinuteModel, MinuteProjectModel
from treasury.models import TransactionModel, MonthlyBalance
from events.models import Event, Venue, EventCategory
from worship.models import Song, SongFile, Composer, Hymnal, SongTheme
import reversion
import datetime
from decimal import Decimal

User = get_user_model()


class AuditingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='test_auditor',
            email='auditor@test.com',
            password='testpass123'
        )
        # Criar MonthlyBalance necessário para transações
        self.monthly_balance = MonthlyBalance.objects.create(
            month=datetime.date(2024, 1, 1),
            is_first_month=True
        )

    def test_meeting_minute_auditing_on_create(self):
        """Testa se uma revisão é criada quando uma ata é criada"""
        with reversion.create_revision():
            reversion.set_user(self.user)
            minute = MeetingMinuteModel.objects.create(
                president=self.user,
                secretary=self.user,
                meeting_date=datetime.date(2024, 1, 1),
                body="Conteúdo da reunião de teste"
            )

        # Verifica se uma revisão foi criada
        revisions = Revision.objects.filter(user=self.user)
        self.assertEqual(revisions.count(), 1)

        revision = revisions.first()
        versions = Version.objects.filter(revision=revision)
        self.assertEqual(versions.count(), 1)

        version = versions.first()
        self.assertIsNotNone(version)
        self.assertEqual(str(version.object_id), str(minute.pk))

    def test_transaction_auditing_on_create(self):
        """Testa se uma revisão é criada quando uma transação é criada"""
        with reversion.create_revision():
            reversion.set_user(self.user)
            transaction = TransactionModel.objects.create(
                user=self.user,
                description="Transação de teste",
                amount=Decimal('100.00'),
                date=datetime.date(2024, 1, 1)
            )

        # Verifica se uma revisão foi criada
        revisions = Revision.objects.filter(user=self.user)
        self.assertTrue(revisions.exists())

        revision = revisions.last()  # Pega a última revisão
        versions = Version.objects.filter(revision=revision)
        self.assertTrue(versions.exists())

        version = versions.first()
        self.assertIsNotNone(version)
        # Verificar se o objeto existe e tem o ID correto
        self.assertEqual(str(version.object_id), str(transaction.pk))

    def test_transaction_auditing_on_update(self):
        """Testa se uma nova revisão é criada quando uma transação é atualizada"""
        # Criar transação inicial
        with reversion.create_revision():
            reversion.set_user(self.user)
            transaction = TransactionModel.objects.create(
                user=self.user,
                description="Transação original",
                amount=Decimal('100.00'),
                date=datetime.date(2024, 1, 1)
            )

        initial_revisions = Revision.objects.filter(user=self.user).count()

        # Atualizar transação
        with reversion.create_revision():
            reversion.set_user(self.user)
            transaction.description = "Transação atualizada"
            transaction.save()

        # Verifica se uma nova revisão foi criada
        final_revisions = Revision.objects.filter(user=self.user).count()
        self.assertEqual(final_revisions, initial_revisions + 1)

    def test_compare_version_admin_functionality(self):
        """Testa se o CompareVersionAdmin permite comparação de versões"""
        from secretarial.admin import MeetingMinuteAdmin
        from treasury.admin import TransactionAdmin
        from reversion_compare.admin import CompareVersionAdmin

        # Verifica se as classes admin herdam de CompareVersionAdmin
        self.assertTrue(issubclass(MeetingMinuteAdmin, CompareVersionAdmin))
        self.assertTrue(issubclass(TransactionAdmin, CompareVersionAdmin))

    def test_version_diff_generation(self):
        """Testa se diffs são gerados corretamente entre versões"""
        # Criar uma transação inicial
        with reversion.create_revision():
            reversion.set_user(self.user)
            transaction = TransactionModel.objects.create(
                user=self.user,
                description="Descrição original",
                amount=Decimal('100.00'),
                date=datetime.date(2024, 1, 1)
            )

        # Criar uma segunda versão com mudanças
        with reversion.create_revision():
            reversion.set_user(self.user)
            transaction.description = "Descrição modificada"
            transaction.amount = Decimal('150.00')
            transaction.save()

        # Verificar se temos duas versões
        versions = Version.objects.filter(object_id=str(transaction.pk)).order_by('revision__date_created')
        self.assertEqual(versions.count(), 2)

        # Verificar se os dados das versões são diferentes
        version1 = versions[0]
        version2 = versions[1]

        data1 = version1.field_dict
        data2 = version2.field_dict

        # Verificar que os campos mudaram
        self.assertNotEqual(data1['description'], data2['description'])
        self.assertNotEqual(data1['amount'], data2['amount'])

        # Verificar valores específicos
        self.assertEqual(data1['description'], "Descrição original")
        self.assertEqual(data2['description'], "Descrição modificada")
        self.assertEqual(data1['amount'], Decimal('100.00'))
        self.assertEqual(data2['amount'], Decimal('150.00'))

    def test_event_auditing_on_create(self):
        """Testa se uma revisão é criada quando um evento é criado"""
        # Criar venue necessário
        venue = Venue.objects.create(
            name="Local de teste",
            address="Endereço do local",
            capacity=100
        )

        with reversion.create_revision():
            reversion.set_user(self.user)
            event = Event.objects.create(
                user=self.user,
                title="Evento de teste",
                description="Descrição do evento",
                start_date=datetime.datetime(2024, 6, 1, 10, 0),
                location=venue
            )

        revisions = Revision.objects.filter(user=self.user)
        self.assertTrue(revisions.exists())

        revision = revisions.last()
        versions = Version.objects.filter(revision=revision)
        self.assertTrue(versions.exists())

        version = versions.first()
        self.assertIsNotNone(version)
        self.assertEqual(str(version.object_id), str(event.pk))

    def test_venue_auditing_on_create(self):
        """Testa se uma revisão é criada quando um local é criado"""
        with reversion.create_revision():
            reversion.set_user(self.user)
            venue = Venue.objects.create(
                name="Local de teste",
                address="Endereço do local",
                capacity=100
            )

        revisions = Revision.objects.filter(user=self.user)
        self.assertTrue(revisions.exists())

        revision = revisions.last()
        versions = Version.objects.filter(revision=revision)
        self.assertTrue(versions.exists())

        version = versions.first()
        self.assertIsNotNone(version)
        self.assertEqual(str(version.object_id), str(venue.pk))

    def test_event_category_auditing_on_create(self):
        """Testa se uma revisão é criada quando uma categoria de evento é criada"""
        with reversion.create_revision():
            reversion.set_user(self.user)
            category = EventCategory.objects.create(
                name="Categoria de teste",
                description="Descrição da categoria"
            )

        revisions = Revision.objects.filter(user=self.user)
        self.assertTrue(revisions.exists())

        revision = revisions.last()
        versions = Version.objects.filter(revision=revision)
        self.assertTrue(versions.exists())

        version = versions.first()
        self.assertIsNotNone(version)
        self.assertEqual(str(version.object_id), str(category.pk))

    def test_song_auditing_on_create(self):
        """Testa se uma revisão é criada quando uma música é criada"""
        composer = Composer.objects.create(name="Compositor de teste")

        with reversion.create_revision():
            reversion.set_user(self.user)
            song = Song.objects.create(
                title="Música de teste",
                artist=composer,
                lyrics="Letra da música"
            )

        revisions = Revision.objects.filter(user=self.user)
        self.assertTrue(revisions.exists())

        revision = revisions.last()
        versions = Version.objects.filter(revision=revision)
        self.assertTrue(versions.exists())

        version = versions.first()
        self.assertIsNotNone(version)
        self.assertEqual(str(version.object_id), str(song.pk))

    def test_minute_project_auditing_on_create(self):
        """Testa se uma revisão é criada quando um projeto de ata é criado"""
        with reversion.create_revision():
            reversion.set_user(self.user)
            project = MinuteProjectModel.objects.create(
                president=self.user,
                secretary=self.user,
                meeting_date=datetime.date(2024, 1, 1),
                number_of_attendees="10",
                body="Corpo do projeto"
            )

        revisions = Revision.objects.filter(user=self.user)
        self.assertTrue(revisions.exists())

        revision = revisions.last()
        versions = Version.objects.filter(revision=revision)
        self.assertTrue(versions.exists())

        version = versions.first()
        self.assertIsNotNone(version)
        self.assertEqual(str(version.object_id), str(project.pk))

    def test_new_models_compare_version_admin_functionality(self):
        """Testa se os novos modelos usam CompareVersionAdmin"""
        from events.admin import EventAdmin, VenueAdmin, EventCategoryAdmin
        from worship.admin import SongAdmin, SongFileAdmin, ComposerAdmin, HymnalAdmin
        from secretarial.admin import MinuteProjectAdmin
        from reversion_compare.admin import CompareVersionAdmin

        # Verifica se as classes admin herdam de CompareVersionAdmin
        self.assertTrue(issubclass(EventAdmin, CompareVersionAdmin))
        self.assertTrue(issubclass(VenueAdmin, CompareVersionAdmin))
        self.assertTrue(issubclass(EventCategoryAdmin, CompareVersionAdmin))
        self.assertTrue(issubclass(SongAdmin, CompareVersionAdmin))
        self.assertTrue(issubclass(SongFileAdmin, CompareVersionAdmin))
        self.assertTrue(issubclass(ComposerAdmin, CompareVersionAdmin))
        self.assertTrue(issubclass(HymnalAdmin, CompareVersionAdmin))
        self.assertTrue(issubclass(MinuteProjectAdmin, CompareVersionAdmin))