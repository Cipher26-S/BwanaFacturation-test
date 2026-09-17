from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [('devis', '0005_devis_expire_historique')]

    operations = [
        migrations.AlterModelOptions(
            name='historiquedevis',
            options={
                'ordering': ['-cree_le'],
                'verbose_name': 'Historique de devis',
                'verbose_name_plural': 'Historiques de devis',
            },
        ),
    ]
