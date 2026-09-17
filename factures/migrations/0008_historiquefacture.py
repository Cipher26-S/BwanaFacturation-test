from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('factures', '0007_facture_date_envoi_email'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='HistoriqueFacture',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(max_length=80)),
                ('ancien_statut', models.CharField(blank=True, max_length=20)),
                ('nouveau_statut', models.CharField(blank=True, max_length=20)),
                ('commentaire', models.TextField(blank=True)),
                ('cree_le', models.DateTimeField(auto_now_add=True)),
                ('acteur', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('facture', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='historique', to='factures.facture')),
            ],
            options={'ordering': ['-cree_le']},
        ),
    ]
