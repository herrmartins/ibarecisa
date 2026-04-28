from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('treasury', '0020_balance_adjustment_reason'),
    ]

    operations = [
        migrations.RunSQL(
            sql="UPDATE treasury_transactionmodel SET amount = ABS(amount) WHERE is_positive = 0 AND amount < 0",
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
