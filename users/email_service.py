"""Service unique pour les emails transactionnels de l'application."""
import logging
from email.utils import formataddr, parseaddr

from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection

logger = logging.getLogger(__name__)

DISPLAY_NAMES = {
    'principal': 'Bwana Facturation',
    'factures': 'Bwana Facturation - Factures',
}


def _with_display_name(from_email, type_email):
    """Ajoute un nom d'expéditeur lisible (ex: "Bwana Facturation <adresse>")
    si l'adresse n'en a pas déjà un — aide à la fois la lisibilité pour le
    destinataire et la classification anti-spam des boîtes de réception."""
    name, addr = parseaddr(from_email)
    if name:
        return from_email
    return formataddr((DISPLAY_NAMES.get(type_email, 'Bwana Facturation'), addr or from_email))


def get_email_connection(type_email='principal', email_config=None):
    """Retourne la configuration active en base, ou celle des settings."""
    if email_config is not None:
        return email_config.get_connection(), email_config.from_email

    try:
        from .admin_models import ConfigurationEmail
        config = ConfigurationEmail.objects.filter(type_email=type_email, actif=True).first()
        if config:
            return config.get_connection(), config.from_email
    except Exception:
        logger.exception("Impossible de charger la configuration email '%s'", type_email)

    if type_email == 'factures':
        return (
            get_connection(
                host=settings.FACTURE_EMAIL_HOST,
                port=settings.FACTURE_EMAIL_PORT,
                username=settings.FACTURE_EMAIL_HOST_USER,
                password=settings.FACTURE_EMAIL_HOST_PASSWORD,
                use_tls=settings.FACTURE_EMAIL_USE_TLS,
            ),
            settings.FACTURE_DEFAULT_FROM_EMAIL,
        )
    return get_connection(), settings.DEFAULT_FROM_EMAIL


def send_transactional_email(
    *, subject, recipient, text_body, html_body=None, type_email='principal',
    reply_to=None, attachments=None, email_config=None,
):
    """Envoie un email et remonte l'erreur au code appelant, sans l'ignorer."""
    connection, from_email = get_email_connection(type_email, email_config=email_config)
    from_email = _with_display_name(from_email, type_email)
    message = EmailMultiAlternatives(subject, text_body, from_email, [recipient], connection=connection)
    if html_body:
        message.attach_alternative(html_body, 'text/html')
    if reply_to:
        message.reply_to = [reply_to]
    for filename, content, mimetype in attachments or []:
        message.attach(filename, content, mimetype)
    try:
        message.send(fail_silently=False)
    except Exception:
        logger.exception("Echec d'envoi de l'email transactionnel à %s", recipient)
        raise
