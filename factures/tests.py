from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from clients.models import Client
from .forms import FactureForm
from .models import Facture, HistoriqueFacture


class FactureWorkflowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('proprietaire', 'owner@example.com', 'MotDePasseFort123!')
        self.client_obj = Client.objects.create(utilisateur=self.user, nom='Client test')

    def test_formulaire_ne_permet_pas_de_choisir_le_statut(self):
        self.assertNotIn('statut', FactureForm(self.user).fields)

    def test_transition_directe_vers_payee_est_refusee(self):
        facture = Facture.objects.create(
            utilisateur=self.user, client=self.client_obj, numero='FAC-TEST-0001',
            date_echeance=timezone.now().date() + timedelta(days=30), statut='en_attente',
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('changer_statut_facture', args=[facture.pk]), {'statut': 'payee'}, follow=True
        )
        self.assertEqual(response.status_code, 200)
        facture.refresh_from_db()
        self.assertEqual(facture.statut, 'en_attente')

    def test_modification_d_une_facture_est_journalisee(self):
        facture = Facture.objects.create(
            utilisateur=self.user, client=self.client_obj, numero='FAC-TEST-0003',
            date_echeance=timezone.now().date() + timedelta(days=30),
        )
        self.client.force_login(self.user)

        response = self.client.post(reverse('modifier_facture', args=[facture.pk]), {
            'client': self.client_obj.pk,
            'date_echeance': (timezone.now().date() + timedelta(days=45)).isoformat(),
            'notes': 'Version modifiée',
            'pays': '', 'type_taxe': '', 'taux_taxe': '', 'devise': 'FCFA',
            'lignes-TOTAL_FORMS': '1', 'lignes-INITIAL_FORMS': '0',
            'lignes-MIN_NUM_FORMS': '0', 'lignes-MAX_NUM_FORMS': '1000',
            'lignes-0-description': 'Service modifié',
            'lignes-0-quantite': '1', 'lignes-0-prix_unitaire': '1000',
        })

        self.assertEqual(response.status_code, 302)
        self.assertTrue(HistoriqueFacture.objects.filter(
            facture=facture, action='modification'
        ).exists())

    def test_transitions_facture_et_historique(self):
        facture = Facture.objects.create(
            utilisateur=self.user, client=self.client_obj, numero='FAC-TEST-0002',
            date_echeance=timezone.now().date() + timedelta(days=30),
        )
        facture.approuver(self.user, 'Validation interne')
        facture.accepter_par_client(commentaire='Accord client')
        facture.marquer_payee(self.user, 'Règlement reçu')
        facture.refresh_from_db()
        self.assertEqual(facture.statut, 'payee')
        self.assertEqual(HistoriqueFacture.objects.filter(facture=facture).count(), 3)
