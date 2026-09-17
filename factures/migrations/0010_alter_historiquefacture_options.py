from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [('factures', '0009_facture_snapshot_source')]

    operations = [
        migrations.AlterModelOptions(
            name='historiquefacture',
            options={
                'ordering': ['-cree_le'],
                'verbose_name': 'Historique de facture',
                'verbose_name_plural': 'Historiques de factures',
            },
        ),
    ]
