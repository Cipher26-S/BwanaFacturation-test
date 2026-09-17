from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('devis', '0004_devis_taxes_personnalisees_alter_lignedevis_tva'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='devis', name='statut',
            field=models.CharField(choices=[('en_attente', 'En attente'), ('approuve_superieur', 'Approuvé par supérieur'), ('rejete_superieur', 'Rejeté par supérieur'), ('accepte', 'Accepté'), ('refuse', 'Refusé'), ('expire', 'Expiré')], default='en_attente', max_length=20),
        ),
        migrations.CreateModel(
            name='HistoriqueDevis',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(max_length=80)),
                ('ancien_statut', models.CharField(blank=True, max_length=20)),
                ('nouveau_statut', models.CharField(blank=True, max_length=20)),
                ('commentaire', models.TextField(blank=True)),
                ('cree_le', models.DateTimeField(auto_now_add=True)),
                ('acteur', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('devis', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='historique', to='devis.devis')),
            ],
            options={'ordering': ['-cree_le']},
        ),
    ]
