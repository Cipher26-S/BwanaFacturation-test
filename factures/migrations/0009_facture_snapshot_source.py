from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('factures', '0008_historiquefacture'),
    ]

    operations = [
        migrations.AddField(
            model_name='facture',
            name='snapshot_source',
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
