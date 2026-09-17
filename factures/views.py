# factures/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django import forms as django_forms
from .models import Facture, LigneFacture, HistoriqueFacture
from .forms import FactureForm, LigneFactureForm, LigneFactureFormSet, BaseLigneFactureFormSet
from produits.models import Produit
from devis.utils import generer_numero_facture
from django.http import HttpResponse
import os
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.urls import reverse
import logging
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.db import transaction
import json
from decimal import Decimal
from users.email_service import send_transactional_email

logger = logging.getLogger(__name__)


def journaliser_facture(facture, action, ancien_statut='', acteur=None, commentaire=''):
    """Conserve la trace des transitions et opérations métier sensibles."""
    HistoriqueFacture.objects.create(
        facture=facture,
        action=action,
        ancien_statut=ancien_statut,
        nouveau_statut=facture.statut,
        acteur=acteur if getattr(acteur, 'is_authenticated', False) else None,
        commentaire=commentaire,
    )


def facture_modifiable(facture):
    return facture.statut == 'en_attente'


@login_required
def liste_factures(request):
    statut = request.GET.get('statut', '')
    recherche = request.GET.get('q', '')

    factures = Facture.objects.filter(utilisateur=request.user)

    if statut:
        factures = factures.filter(statut=statut)
    if recherche:
        factures = factures.filter(numero__icontains=recherche) | \
                   factures.filter(client__nom__icontains=recherche)

    return render(request, 'factures/liste_factures.html', {
        'factures': factures,
        'statut': statut,
        'recherche': recherche,
        'nb_total': Facture.objects.filter(utilisateur=request.user).count(),
        'nb_non_payees': Facture.objects.filter(utilisateur=request.user, statut='non_payee').count(),
        'nb_payees': Facture.objects.filter(utilisateur=request.user, statut='payee').count(),
        'nb_annulees': Facture.objects.filter(utilisateur=request.user, statut='annulee').count(),
    })


@login_required
def ajouter_facture(request):
    if request.method == 'POST':
        form = FactureForm(request.user, request.POST)
        formset = LigneFactureFormSet(request.POST, prefix='lignes', user=request.user)

        if form.is_valid() and formset.is_valid():
            facture = form.save(commit=False)
            facture.utilisateur = request.user
            facture.numero = generer_numero_facture(request.user)
            # Une facture démarre toujours en attente d'approbation.
            facture.statut = 'en_attente'
            
            # Sauvegarder la devise choisie
            devise_choisie = form.cleaned_data.get('devise')
            if devise_choisie:
                facture.devise_choisie = devise_choisie
            
            # Générer les tokens pour l'approbation
            facture.generer_tokens()
            
            # Récupérer les taxes personnalisées
            taxes_perso = request.POST.get('taxes_personnalisees', '')
            if taxes_perso:
                try:
                    taxes_data = json.loads(taxes_perso)
                    facture.taxes_personnalisees = taxes_data
                except json.JSONDecodeError:
                    facture.taxes_personnalisees = {}
            else:
                facture.taxes_personnalisees = {}
            
            # Désactiver l'ancien système si des taxes personnalisées existent
            if facture.taxes_personnalisees and (facture.taxes_personnalisees.get('ids') or facture.taxes_personnalisees.get('personnalisees')):
                facture.taux_taxe = 0
                facture.type_taxe = ''
            else:
                facture.taux_taxe = form.cleaned_data.get('taux_taxe', 0)
                facture.type_taxe = form.cleaned_data.get('type_taxe', 'TVA')
            
            facture.save()
            journaliser_facture(facture, 'creation', acteur=request.user)
            
            # Sauvegarder les taxes sélectionnées (ManyToMany)
            if form.cleaned_data.get('taxes'):
                facture.taxes.set(form.cleaned_data['taxes'])

            # Sauvegarder les lignes
            lignes_sauvegardees = 0
            for ligne_form in formset:
                if ligne_form.cleaned_data and not ligne_form.cleaned_data.get('DELETE'):
                    ligne = ligne_form.save(commit=False)
                    ligne.facture = facture
                    ligne.save()
                    lignes_sauvegardees += 1

            if lignes_sauvegardees == 0:
                facture.delete()
                messages.error(request, '❌ Veuillez ajouter au moins un produit ou service.')
                return render_creation_facture(request, form, formset)

            messages.success(request, f'✅ Facture {facture.numero} créée !')
            
            return redirect('gestion_liens_facture', pk=facture.pk)
        else:
            messages.error(request, '❌ Veuillez corriger les erreurs.')
            print(f"❌ ERREURS FORM: {form.errors}")
            print(f"❌ ERREURS FORMSET: {formset.errors}")
    else:
        form = FactureForm(request.user)
        formset = LigneFactureFormSet(prefix='lignes', user=request.user)

    return render_creation_facture(request, form, formset)


def render_creation_facture(request, form, formset):
    """Helper pour le rendu de la création"""
    produits = Produit.objects.filter(
        user=request.user, actif=True
    ).select_related('pays').order_by('nom')

    return render(request, 'factures/form_facture.html', {
        'form': form,
        'formset': formset,
        'produits': produits,
        'lignes_existantes': [],
        'titre': 'Créer une facture',
        'bouton': 'Créer la facture'
    })


@login_required
def gestion_liens_facture(request, pk):
    """Page pour gérer les liens d'approbation et client"""
    facture = get_object_or_404(Facture, pk=pk, utilisateur=request.user)
    
    base_url = request.build_absolute_uri('/')[:-1]
    lien_approbation = f"{base_url}{reverse('visualiser_facture_approbation', args=[facture.token_approbation])}"
    lien_client = f"{base_url}{reverse('visualiser_facture_client', args=[facture.token_client])}"
    
    return render(request, 'factures/gestion_liens.html', {
        'facture': facture,
        'lien_approbation': lien_approbation,
        'lien_client': lien_client,
    })


@transaction.atomic
def visualiser_facture_approbation(request, token):
    """Page publique pour que le supérieur approuve la facture"""
    facture = get_object_or_404(Facture.objects.select_for_update(), token_approbation=token)
    
    if facture.statut != 'en_attente':
        return render(request, 'factures/public/approbation.html', {
            'facture': facture,
            'deja_traite': True,
            'message_warning': 'Cette facture a déjà été approuvée.'
        })
    
    if request.method == 'POST':
        action = request.POST.get('action')
        commentaire = request.POST.get('commentaire', '')
        
        if action == 'approuver':
            facture.approuver(request.user, commentaire)
            
            try:
                send_transactional_email(subject=f'Facture {facture.numero} approuvée', recipient=facture.utilisateur.email,
                                         text_body=f'Votre facture {facture.numero} a été approuvée.\n\nCommentaire : {commentaire}')
            except Exception:
                logger.exception("Notification d'approbation de la facture %s non envoyée", facture.numero)
            
            return render(request, 'factures/public/approbation.html', {
                'facture': facture,
                'action_effectuee': 'approuver',
                'message_success': f'✅ Facture {facture.numero} approuvée avec succès !',
                'commentaire': commentaire
            })
            
        elif action == 'rejeter':
            facture.rejeter(request.user, commentaire)
            
            try:
                send_transactional_email(subject=f'Facture {facture.numero} rejetée', recipient=facture.utilisateur.email,
                                         text_body=f'Votre facture {facture.numero} a été rejetée.\n\nMotif : {commentaire}')
            except Exception:
                logger.exception("Notification de rejet de la facture %s non envoyée", facture.numero)
            
            return render(request, 'factures/public/approbation.html', {
                'facture': facture,
                'action_effectuee': 'rejeter',
                'message_success': f'❌ Facture {facture.numero} rejetée.',
                'commentaire': commentaire
            })
    
    return render(request, 'factures/public/approbation.html', {
        'facture': facture,
        'deja_traite': False
    })


@transaction.atomic
def visualiser_facture_client(request, token):
    """Page publique pour que le client accepte la facture"""
    facture = get_object_or_404(Facture.objects.select_for_update(), token_client=token)
    
    if facture.statut != 'approuvee':
        return render(request, 'factures/public/client.html', {
            'facture': facture,
            'message_warning': 'Cette facture n\'a pas encore été approuvée en interne.',
            'en_attente': True
        })
    
    if facture.accepte_par_client is not None:
        return render(request, 'factures/public/client.html', {
            'facture': facture,
            'deja_repondu': True,
            'message_warning': 'Vous avez déjà répondu à cette facture.'
        })
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'accepter':
            facture.accepter_par_client(commentaire='Acceptation via lien client')
            
            try:
                send_transactional_email(subject=f'Facture {facture.numero} acceptée', recipient=facture.utilisateur.email,
                                         text_body=f'Le client {facture.client.nom} a accepté la facture {facture.numero}.')
            except Exception:
                logger.exception("Notification d'acceptation de la facture %s non envoyée", facture.numero)
            
            return render(request, 'factures/public/client.html', {
                'facture': facture,
                'action_effectuee': 'accepter',
                'message_success': f'✅ Merci ! Votre acceptation a été enregistrée.'
            })
            
        elif action == 'refuser':
            facture.refuser_par_client(commentaire='Refus via lien client')
            
            try:
                send_transactional_email(subject=f'Facture {facture.numero} refusée', recipient=facture.utilisateur.email,
                                         text_body=f'Le client {facture.client.nom} a refusé la facture {facture.numero}.')
            except Exception:
                logger.exception("Notification de refus de la facture %s non envoyée", facture.numero)
            
            return render(request, 'factures/public/client.html', {
                'facture': facture,
                'action_effectuee': 'refuser',
                'message_success': f'ℹ️ Nous avons bien enregistré votre refus.'
            })
    
    return render(request, 'factures/public/client.html', {
        'facture': facture,
    })


@login_required
def detail_facture(request, pk):
    facture = get_object_or_404(
        Facture.objects.select_related('client__pays_obj'),
        pk=pk, 
        utilisateur=request.user
    )
    lignes = facture.lignes.all()

    return render(request, 'factures/detail_facture.html', {
        'facture': facture,
        'lignes': lignes,
    })


@login_required
@transaction.atomic
def modifier_facture(request, pk):
    facture = get_object_or_404(
        Facture.objects.select_related('client__pays_obj'),
        pk=pk, 
        utilisateur=request.user
    )

    if not facture_modifiable(facture):
        messages.error(request, '❌ Seule une facture en attente peut être modifiée.')
        return redirect('detail_facture', pk=pk)

    if request.method == 'POST':
        form = FactureForm(request.user, request.POST, instance=facture)
        formset = LigneFactureFormSet(request.POST, prefix='lignes', user=request.user)

        if form.is_valid() and formset.is_valid():
            facture = form.save(commit=False)
            
            # Récupérer les taxes personnalisées
            taxes_perso = request.POST.get('taxes_personnalisees', '')
            if taxes_perso:
                try:
                    taxes_data = json.loads(taxes_perso)
                    facture.taxes_personnalisees = taxes_data
                except json.JSONDecodeError:
                    facture.taxes_personnalisees = {}
            else:
                facture.taxes_personnalisees = {}
            
            # Désactiver l'ancien système si des taxes personnalisées existent
            if facture.taxes_personnalisees and (facture.taxes_personnalisees.get('ids') or facture.taxes_personnalisees.get('personnalisees')):
                facture.taux_taxe = 0
                facture.type_taxe = ''
            else:
                facture.taux_taxe = form.cleaned_data.get('taux_taxe', 0)
                facture.type_taxe = form.cleaned_data.get('type_taxe', 'TVA')
            
            facture.save()
            
            # Sauvegarder les taxes ManyToMany
            if form.cleaned_data.get('taxes'):
                facture.taxes.set(form.cleaned_data['taxes'])
            else:
                facture.taxes.clear()
            
            facture.lignes.all().delete()

            lignes_sauvegardees = 0
            for ligne_form in formset:
                if ligne_form.cleaned_data and not ligne_form.cleaned_data.get('DELETE'):
                    ligne = ligne_form.save(commit=False)
                    ligne.facture = facture
                    ligne.save()
                    lignes_sauvegardees += 1

            if lignes_sauvegardees == 0:
                messages.error(request, '❌ Veuillez ajouter au moins un produit ou service.')
                return render_modification_facture(request, facture, form, formset)

            journaliser_facture(
                facture,
                'modification',
                acteur=request.user,
                commentaire='Facture modifiée avant approbation',
            )
            messages.success(request, f'✏️ Facture {facture.numero} modifiée !')
            return redirect('detail_facture', pk=facture.pk)
        else:
            messages.error(request, '❌ Veuillez corriger les erreurs.')
            print(f"❌ ERREURS FORM: {form.errors}")
            print(f"❌ ERREURS FORMSET: {formset.errors}")
        
        lignes_existantes = []
    else:
        form = FactureForm(request.user, instance=facture)
        formset = LigneFactureFormSet(prefix='lignes', user=request.user)
        lignes_existantes = list(facture.lignes.all())

    return render_modification_facture(request, facture, form, formset, lignes_existantes)


def render_modification_facture(request, facture, form, formset, lignes_existantes=None):
    if lignes_existantes is None:
        lignes_existantes = []
    
    produits = Produit.objects.filter(
        user=request.user, actif=True
    ).select_related('pays').order_by('nom')

    return render(request, 'factures/form_facture.html', {
        'form': form,
        'formset': formset,
        'produits': produits,
        'lignes_existantes': lignes_existantes,
        'titre': f'Modifier - {facture.numero}',
        'bouton': 'Enregistrer',
        'facture': facture
    })


@login_required
def supprimer_facture(request, pk):
    facture = get_object_or_404(Facture, pk=pk, utilisateur=request.user)

    if not facture_modifiable(facture):
        messages.error(request, '❌ Seule une facture en attente peut être supprimée. Annulez-la pour conserver la traçabilité.')
        return redirect('detail_facture', pk=pk)

    if request.method == 'POST':
        numero = facture.numero
        facture.delete()
        messages.success(request, f'🗑️ Facture {numero} supprimée.')
        return redirect('liste_factures')

    return render(request, 'factures/confirmer_suppression.html', {'facture': facture})


@login_required
def changer_statut_facture(request, pk):
    facture = get_object_or_404(Facture, pk=pk, utilisateur=request.user)

    if request.method == 'POST':
        nouveau_statut = request.POST.get('statut')
        try:
            if nouveau_statut == 'payee':
                facture.marquer_payee(request.user)
            elif nouveau_statut == 'annulee':
                facture.annuler(request.user)
            else:
                raise ValidationError('Transition inconnue.')
        except ValidationError:
            messages.error(request, '❌ Cette transition de statut n’est pas autorisée.')
            return redirect('detail_facture', pk=pk)
        if nouveau_statut in {'payee', 'annulee'}:
            messages.success(request, f'Statut mis à jour : {facture.get_statut_display()}')

    return redirect('detail_facture', pk=pk)


@login_required
def telecharger_pdf_facture(request, pk):
    facture = get_object_or_404(
        Facture.objects.select_related('client__pays_obj'),
        pk=pk, 
        utilisateur=request.user
    )
    from .pdf import generer_pdf_facture

    buffer = generer_pdf_facture(facture)

    nom_fichier = f"facture_{facture.numero}.pdf"
    chemin_relatif = f"factures/pdf/{nom_fichier}"
    chemin_complet = os.path.join(settings.MEDIA_ROOT, chemin_relatif)

    os.makedirs(os.path.dirname(chemin_complet), exist_ok=True)

    with open(chemin_complet, 'wb') as f:
        f.write(buffer.getvalue())

    facture.fichier_pdf = chemin_relatif
    facture.save()

    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{nom_fichier}"'
    return response


# ============================================================
# ENVOI DE FACTURE PAR EMAIL (AVEC CONFIGURATION BASE DE DONNÉES)
# ============================================================

@login_required
def envoyer_facture_email(request, pk):
    """Envoie la facture par email avec choix du destinataire"""
    facture = get_object_or_404(Facture, pk=pk, utilisateur=request.user)
    
    # Récupérer l'option choisie par l'utilisateur
    option_destinataire = request.POST.get('option_destinataire')
    
    # Déterminer l'adresse email du destinataire
    if option_destinataire == 'client':
        email_destinataire = facture.client.email
        if not email_destinataire:
            messages.error(request, f"Le client {facture.client.nom} n'a pas d'adresse email enregistrée.")
            return redirect('liste_factures')
    else:
        email_destinataire = request.POST.get('email_autre')
        if not email_destinataire:
            messages.error(request, "Veuillez saisir une adresse email.")
            return redirect('liste_factures')
    
    # Vérifier que le PDF existe, sinon le générer
    if not facture.fichier_pdf or not os.path.exists(facture.fichier_pdf.path):
        from .pdf import generer_pdf_facture
        buffer = generer_pdf_facture(facture)
        nom_fichier = f"facture_{facture.numero}.pdf"
        chemin_relatif = f"factures/pdf/{nom_fichier}"
        chemin_complet = os.path.join(settings.MEDIA_ROOT, chemin_relatif)
        os.makedirs(os.path.dirname(chemin_complet), exist_ok=True)
        with open(chemin_complet, 'wb') as f:
            f.write(buffer.getvalue())
        facture.fichier_pdf = chemin_relatif
        facture.save()
    
    # Déterminer la devise
    devise = facture.get_devise()
    
    # URLs complètes
    base_url = request.build_absolute_uri('/')[:-1]
    lien_facture = f"{base_url}{reverse('detail_facture', args=[facture.pk])}"
    lien_pdf = f"{base_url}{reverse('pdf_facture', args=[facture.pk])}"
    
    # Contexte pour le template email
    context = {
        'facture': facture,
        'client': facture.client,
        'total_ht': facture.calculer_total_ht(),
        'total_ttc': facture.calculer_total_ttc(),
        'tva': facture.calculer_tva(),
        'devise': devise,
        'date_echeance': facture.date_echeance,
        'lien_facture': lien_facture,
        'lien_pdf': lien_pdf,
        'utilisateur': request.user,
        'taxes_details': facture.get_taxes_details(),
    }
    
    # Rendre le template HTML
    html_message = render_to_string('factures/emails/facture_email.html', context)
    plain_message = strip_tags(html_message)
    
    sujet = f"Facture {facture.numero} - {facture.client.nom}"
    with open(facture.fichier_pdf.path, 'rb') as pdf_file:
        pdf_content = pdf_file.read()
    
    try:
        send_transactional_email(
            subject=sujet, recipient=email_destinataire, text_body=plain_message,
            html_body=html_message, type_email='factures', reply_to=request.user.email,
            attachments=[(f"facture_{facture.numero}.pdf", pdf_content, 'application/pdf')],
        )
        facture.date_envoi_email = timezone.now()
        facture.save(update_fields=['date_envoi_email'])
        journaliser_facture(facture, 'envoi_email', acteur=request.user,
                            commentaire=f'Email envoyé à {email_destinataire}')
        messages.success(request, f"Facture {facture.numero} envoyée par email à {email_destinataire}")
    except Exception:
        logger.exception("Envoi de la facture %s vers %s impossible", facture.numero, email_destinataire)
        messages.error(request, "L'e-mail n'a pas pu être envoyé. Vérifiez la configuration SMTP ou réessayez plus tard.")
    
    return redirect('liste_factures')
