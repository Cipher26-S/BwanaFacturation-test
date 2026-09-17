from unittest.mock import Mock, patch

from django.contrib.auth.models import User
from django.core import mail
from django.core.mail import get_connection
from django.test import TestCase
from django.urls import reverse

from .email_service import send_transactional_email


class InscriptionEmailTests(TestCase):
    @patch('users.views.send_transactional_email', side_effect=OSError('SMTP indisponible'))
    def test_echec_email_ne_active_jamais_le_compte(self, _send_email):
        response = self.client.post(reverse('inscription'), {
            'first_name': 'Awa', 'last_name': 'Traore', 'email': 'awa@example.com',
            'password1': 'MotDePasseFort123!', 'password2': 'MotDePasseFort123!',
            'terms': 'on',
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.get(email='awa@example.com').is_active)


class TransactionalEmailTests(TestCase):
    def test_envoie_html_reply_to_et_piece_jointe(self):
        send_transactional_email(
            subject='Facture de test',
            recipient='client@example.com',
            text_body='Message texte',
            html_body='<p>Message HTML</p>',
            reply_to='commercial@example.com',
            attachments=[('facture.pdf', b'%PDF-test', 'application/pdf')],
        )

        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.to, ['client@example.com'])
        self.assertEqual(message.reply_to, ['commercial@example.com'])
        self.assertEqual(message.attachments[0], ('facture.pdf', b'%PDF-test', 'application/pdf'))
        self.assertEqual(message.alternatives[0][0], '<p>Message HTML</p>')

    def test_utilise_la_configuration_email_fournie(self):
        connection = get_connection('django.core.mail.backends.locmem.EmailBackend')
        email_config = Mock()
        email_config.get_connection.return_value = connection
        email_config.from_email = 'smtp@example.com'

        send_transactional_email(
            subject='Test SMTP',
            recipient='client@example.com',
            text_body='Message',
            email_config=email_config,
        )

        email_config.get_connection.assert_called_once_with()
        self.assertEqual(mail.outbox[0].from_email, 'smtp@example.com')
