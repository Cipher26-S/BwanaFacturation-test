from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from clients.models import Client
from .forms import DevisForm
from .models import Devis, HistoriqueDevis


class DevisWorkflowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('proprietaire', 'owner@example.com', 'MotDePasseFort123!')
        self.client_obj = Client.objects.create(utilisateur=self.user, nom='Client test')

    def test_formulaire_ne_permet_pas_de_choisir_le_statut(self):
        self.assertNotIn('statut', DevisForm(user=self.user).fields)

    def test_devis_accepte_ne_peut_pas_etre_modifie_ni_supprime(self):
        devis = Devis.objects.create(
            utilisateur=self.user, client=self.client_obj, numero='DEV-TEST-0001',
            date_validite=timezone.now().date() + timedelta(days=30), statut='accepte',
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse('modifier_devis', args=[devis.pk]), follow=True)
        self.assertEqual(response.status_code, 200)
        response = self.client.post(reverse('supprimer_devis', args=[devis.pk]), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Devis.objects.filter(pk=devis.pk).exists())

    def test_modification_d_un_devis_est_journalisee(self):
        devis = Devis.objects.create(
            utilisateur=self.user, client=self.client_obj, numero='DEV-TEST-0003',
            date_validite=timezone.now().date() + timedelta(days=30),
        )
        self.client.force_login(self.user)

        response = self.client.post(reverse('modifier_devis', args=[devis.pk]), {
            'client': self.client_obj.pk,
            'date_validite': (timezone.now().date() + timedelta(days=45)).isoformat(),
            'notes': 'Version modifiée',
            'pays': '', 'type_taxe': '', 'taux_taxe': '', 'devise': 'FCFA',
            'lignes-TOTAL_FORMS': '1', 'lignes-INITIAL_FORMS': '0',
            'lignes-MIN_NUM_FORMS': '0', 'lignes-MAX_NUM_FORMS': '1000',
            'lignes-0-description': 'Service modifié',
            'lignes-0-quantite': '1', 'lignes-0-prix_unitaire': '1000',
        })

        self.assertEqual(response.status_code, 302)
        self.assertTrue(HistoriqueDevis.objects.filter(
            devis=devis, action='modification'
        ).exists())

    def test_transitions_devis_et_historique(self):
        devis = Devis.objects.create(
            utilisateur=self.user, client=self.client_obj, numero='DEV-TEST-0002',
            date_validite=timezone.now().date() + timedelta(days=30),
        )
        devis.approuver(self.user, 'Bon pour validation')
        devis.accepter_par_client(commentaire='Accord client')
        devis.refresh_from_db()
        self.assertEqual(devis.statut, 'accepte')
        self.assertEqual(HistoriqueDevis.objects.filter(devis=devis).count(), 2)
