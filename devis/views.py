# devis/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Devis, LigneDevis, HistoriqueDevis
from .forms import DevisForm, LigneDevisForm, LigneDevisFormSet
from .utils import generer_numero_devis
from django.http import HttpResponse
import os
import json
from django.conf import settings
from produits.models import Produit
from django.db.models import Q
from django.db import transaction
from django.urls import reverse
from django.utils import timezone
import logging
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from taxes.models import Taxe
from users.email_service import send_transactional_email

logger = logging.getLogger(__name__)


def journaliser_devis(devis, action, ancien_statut='', acteur=None, commentaire=''):
    """Conserve la trace des transitions et opérations métier sensibles."""
    HistoriqueDevis.objects.create(
        devis=devis,
        action=action,
        ancien_statut=ancien_statut,
        nouveau_statut=devis.statut,
        acteur=acteur if getattr(acteur, 'is_authenticated', False) else None,
        commentaire=commentaire,
    )


def devis_modifiable(devis):
    return devis.statut == 'en_attente' and not devis.transforme_en_facture


@login_required
def liste_devis(request):
    statut = request.GET.get('statut', '')
    recherche = request.GET.get('q', '')

    devis = Devis.objects.filter(utilisateur=request.user)

    if statut:
        devis = devis.filter(statut=statut)
    if recherche:
        devis = devis.filter(
            Q(numero__icontains=recherche) |
            Q(client__nom__icontains=recherche) |
            Q(client__entreprise__icontains=recherche)
        )

    nb_total = Devis.objects.filter(utilisateur=request.user).count()
    nb_attente = Devis.objects.filter(utilisateur=request.user, statut='en_attente').count()
    nb_acceptes = Devis.objects.filter(utilisateur=request.user, statut='accepte').count()
    nb_refuses = Devis.objects.filter(utilisateur=request.user, statut='refuse').count()

    return render(request, 'devis/liste_devis.html', {
        'devis': devis.select_related('client').order_by('-date_creation'),
        'statut': statut,
        'recherche': recherche,
        'nb_total': nb_total,
        'nb_attente': nb_attente,
        'nb_acceptes': nb_acceptes,
        'nb_refuses': nb_refuses,
    })


@login_required
def ajouter_devis(request):
    if request.method == 'POST':
        form = DevisForm(request.POST, user=request.user)
        formset = LigneDevisFormSet(request.POST, prefix='lignes', user=request.user)

        if form.is_valid() and formset.is_valid():
            # Validation de la date
            date_validite = form.cleaned_data.get('date_validite')
            if date_validite <= timezone.now().date():
                messages.error(request, '❌ La date de validité doit être postérieure à aujourd\'hui.')
                return render_creation_devis(request, form, formset)

            devis = form.save(commit=False)
            devis.utilisateur = request.user
            devis.numero = generer_numero_devis(request.user)
            # Le statut initial n'est jamais choisi depuis un formulaire utilisateur.
            devis.statut = 'en_attente'
            
            # Générer les tokens pour l'approbation
            devis.generer_tokens()
            
            # ✅ RÉCUPÉRER LES TAXES PERSONNALISÉES (champ caché)
            taxes_perso = request.POST.get('taxes_personnalisees', '')
            if taxes_perso:
                try:
                    taxes_data = json.loads(taxes_perso)
                    devis.taxes_personnalisees = taxes_data
                except json.JSONDecodeError:
                    devis.taxes_personnalisees = {}
            else:
                devis.taxes_personnalisees = {}
            
            # ✅ IMPORTANT : Désactiver l'ancien système si des taxes personnalisées existent
            if devis.taxes_personnalisees and (devis.taxes_personnalisees.get('ids') or devis.taxes_personnalisees.get('personnalisees')):
                devis.taux_taxe = 0
                devis.type_taxe = ''
            else:
                devis.taux_taxe = form.cleaned_data.get('taux_taxe', 0)
                devis.type_taxe = form.cleaned_data.get('type_taxe', 'TVA')
            
            devis.save()
            journaliser_devis(devis, 'creation', acteur=request.user)
            
            # Sauvegarder les taxes sélectionnées (ManyToMany)
            if form.cleaned_data.get('taxes'):
                devis.taxes.set(form.cleaned_data['taxes'])

            # Sauvegarder les lignes
            lignes_sauvegardees = 0
            for ligne_form in formset:
                if ligne_form.cleaned_data and not ligne_form.cleaned_data.get('DELETE'):
                    ligne = ligne_form.save(commit=False)
                    ligne.devis = devis
                    ligne.save()
                    lignes_sauvegardees += 1

            if lignes_sauvegardees == 0:
                devis.delete()
                messages.error(request, '❌ Veuillez ajouter au moins un produit ou service.')
                return render_creation_devis(request, form, formset)

            messages.success(request, f'✅ Devis {devis.numero} créé avec succès !')
            
            # Rediriger vers la page de gestion des liens
            return redirect('gestion_liens_devis', pk=devis.pk)
        else:
            messages.error(request, '❌ Veuillez corriger les erreurs dans le formulaire.')
            print(f"❌ ERREURS FORM: {form.errors}")
            print(f"❌ ERREURS FORMSET: {formset.errors}")
    else:
        form = DevisForm(user=request.user)
        formset = LigneDevisFormSet(prefix='lignes', user=request.user)

    return render_creation_devis(request, form, formset)


def render_creation_devis(request, form, formset):
    """Helper pour le rendu de la création"""
    produits = Produit.objects.filter(
        user=request.user, actif=True
    ).select_related('pays').order_by('nom')

    return render(request, 'devis/form_devis.html', {
        'form': form,
        'formset': formset,
        'produits': produits,
        'lignes_existantes': [],
        'titre': 'Créer un devis',
        'bouton': 'Créer le devis',
    })


@login_required
def gestion_liens_devis(request, pk):
    """Page pour gérer les liens d'approbation et client"""
    devis = get_object_or_404(Devis, pk=pk, utilisateur=request.user)
    
    base_url = request.build_absolute_uri('/')[:-1]
    lien_approbation = f"{base_url}{reverse('visualiser_devis_approbation', args=[devis.token_approbation])}"
    lien_client = f"{base_url}{reverse('visualiser_devis_client', args=[devis.token_client])}"
    
    return render(request, 'devis/gestion_liens.html', {
        'devis': devis,
        'lien_approbation': lien_approbation,
        'lien_client': lien_client,
    })


@transaction.atomic
def visualiser_devis_approbation(request, token):
    """Page publique pour que le supérieur approuve le devis"""
    devis = get_object_or_404(Devis.objects.select_for_update(), token_approbation=token)
    
    if devis.statut != 'en_attente':
        return render(request, 'devis/public/approbation.html', {
            'devis': devis,
            'deja_traite': True,
            'message_warning': 'Ce devis a déjà été approuvé.'
        })
    
    if request.method == 'POST':
        action = request.POST.get('action')
        commentaire = request.POST.get('commentaire', '')
        
        if action == 'approuver':
            devis.approuver(request.user, commentaire)
            
            try:
                send_transactional_email(subject=f'Devis {devis.numero} approuvé', recipient=devis.utilisateur.email,
                                         text_body=f'Votre devis {devis.numero} a été approuvé.\n\nCommentaire : {commentaire}')
            except Exception:
                logger.exception("Notification d'approbation du devis %s non envoyée", devis.numero)
            
            return render(request, 'devis/public/approbation.html', {
                'devis': devis,
                'action_effectuee': 'approuver',
                'message_success': f'✅ Devis {devis.numero} approuvé avec succès !',
                'commentaire': commentaire
            })
            
        elif action == 'rejeter':
            devis.rejeter(request.user, commentaire)
            
            try:
                send_transactional_email(subject=f'Devis {devis.numero} rejeté', recipient=devis.utilisateur.email,
                                         text_body=f'Votre devis {devis.numero} a été rejeté.\n\nMotif : {commentaire}')
            except Exception:
                logger.exception("Notification de rejet du devis %s non envoyée", devis.numero)
            
            return render(request, 'devis/public/approbation.html', {
                'devis': devis,
                'action_effectuee': 'rejeter',
                'message_success': f'❌ Devis {devis.numero} rejeté.',
                'commentaire': commentaire
            })
    
    return render(request, 'devis/public/approbation.html', {
        'devis': devis,
        'deja_traite': False
    })


@transaction.atomic
def visualiser_devis_client(request, token):
    """Page publique pour que le client accepte/refuse le devis"""
    devis = get_object_or_404(Devis.objects.select_for_update(), token_client=token)
    
    if devis.statut != 'approuve_superieur':
        return render(request, 'devis/public/client.html', {
            'devis': devis,
            'message_warning': 'Ce devis n\'a pas encore été approuvé en interne.',
            'en_attente': True
        })
    
    if devis.accepte_par_client is not None:
        return render(request, 'devis/public/client.html', {
            'devis': devis,
            'deja_repondu': True,
            'message_warning': 'Vous avez déjà répondu à ce devis.'
        })
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'accepter':
            devis.accepter_par_client(commentaire='Acceptation via lien client')
            
            try:
                send_transactional_email(subject=f'Devis {devis.numero} accepté', recipient=devis.utilisateur.email,
                                         text_body=f'Le client {devis.client.nom} a accepté le devis {devis.numero}.')
            except Exception:
                logger.exception("Notification d'acceptation du devis %s non envoyée", devis.numero)
            
            return render(request, 'devis/public/client.html', {
                'devis': devis,
                'action_effectuee': 'accepter',
                'message_success': f'✅ Merci ! Votre acceptation a été enregistrée.'
            })
            
        elif action == 'refuser':
            devis.refuser_par_client(commentaire='Refus via lien client')
            
            try:
                send_transactional_email(subject=f'Devis {devis.numero} refusé', recipient=devis.utilisateur.email,
                                         text_body=f'Le client {devis.client.nom} a refusé le devis {devis.numero}.')
            except Exception:
                logger.exception("Notification de refus du devis %s non envoyée", devis.numero)
            
            return render(request, 'devis/public/client.html', {
                'devis': devis,
                'action_effectuee': 'refuser',
                'message_success': f'ℹ️ Nous avons bien enregistré votre refus.'
            })
    
    return render(request, 'devis/public/client.html', {
        'devis': devis,
    })


@login_required
def detail_devis(request, pk):
    devis = get_object_or_404(Devis, pk=pk, utilisateur=request.user)
    lignes = devis.lignes.all().select_related('produit')
    
    if devis.date_validite < timezone.now().date() and devis.statut == 'en_attente':
        devis.expirer()

    return render(request, 'devis/detail_devis.html', {
        'devis': devis,
        'lignes': lignes,
    })


@login_required
@transaction.atomic
def modifier_devis(request, pk):
    devis = get_object_or_404(Devis, pk=pk, utilisateur=request.user)

    if not devis_modifiable(devis):
        messages.error(request, '❌ Seul un devis en attente peut être modifié.')
        return redirect('detail_devis', pk=pk)

    if request.method == 'POST':
        form = DevisForm(request.POST, user=request.user, instance=devis)
        formset = LigneDevisFormSet(request.POST, prefix='lignes', user=request.user)

        if form.is_valid() and formset.is_valid():
            date_validite = form.cleaned_data.get('date_validite')
            if date_validite <= timezone.now().date():
                messages.error(request, '❌ La date de validité doit être postérieure à aujourd\'hui.')
                return render_modification_devis(request, devis, form, formset)

            devis = form.save(commit=False)
            
            # ✅ RÉCUPÉRER LES TAXES PERSONNALISÉES
            taxes_perso = request.POST.get('taxes_personnalisees', '')
            if taxes_perso:
                try:
                    taxes_data = json.loads(taxes_perso)
                    devis.taxes_personnalisees = taxes_data
                except json.JSONDecodeError:
                    devis.taxes_personnalisees = {}
            else:
                devis.taxes_personnalisees = {}
            
            # ✅ Désactiver l'ancien système si des taxes personnalisées existent
            if devis.taxes_personnalisees and (devis.taxes_personnalisees.get('ids') or devis.taxes_personnalisees.get('personnalisees')):
                devis.taux_taxe = 0
                devis.type_taxe = ''
            else:
                devis.taux_taxe = form.cleaned_data.get('taux_taxe', 0)
                devis.type_taxe = form.cleaned_data.get('type_taxe', 'TVA')
            
            devis.save()
            
            if form.cleaned_data.get('taxes'):
                devis.taxes.set(form.cleaned_data['taxes'])
            else:
                devis.taxes.clear()
            
            devis.lignes.all().delete()

            lignes_sauvegardees = 0
            for ligne_form in formset:
                if ligne_form.cleaned_data and not ligne_form.cleaned_data.get('DELETE'):
                    ligne = ligne_form.save(commit=False)
                    ligne.devis = devis
                    ligne.save()
                    lignes_sauvegardees += 1

            if lignes_sauvegardees == 0:
                messages.error(request, '❌ Veuillez ajouter au moins un produit ou service.')
                return render_modification_devis(request, devis, form, formset)

            journaliser_devis(
                devis,
                'modification',
                acteur=request.user,
                commentaire='Devis modifié avant approbation',
            )
            messages.success(request, f'✏️ Devis {devis.numero} modifié avec succès !')
            return redirect('detail_devis', pk=devis.pk)
        else:
            messages.error(request, '❌ Veuillez corriger les erreurs.')
    else:
        form = DevisForm(user=request.user, instance=devis)
        formset = LigneDevisFormSet(prefix='lignes', user=request.user)
        lignes_existantes = list(devis.lignes.all().select_related('produit'))

    return render_modification_devis(request, devis, form, formset, lignes_existantes)


def render_modification_devis(request, devis, form, formset, lignes_existantes=None):
    if lignes_existantes is None:
        lignes_existantes = []
    
    produits = Produit.objects.filter(
        user=request.user, actif=True
    ).select_related('pays').order_by('nom')

    return render(request, 'devis/form_devis.html', {
        'form': form,
        'formset': formset,
        'produits': produits,
        'lignes_existantes': lignes_existantes,
        'titre': f'Modifier - {devis.numero}',
        'bouton': 'Enregistrer',
        'devis': devis,
    })


@login_required
def supprimer_devis(request, pk):
    devis = get_object_or_404(Devis, pk=pk, utilisateur=request.user)

    if not devis_modifiable(devis):
        messages.error(request, '❌ Seul un devis en attente peut être supprimé.')
        return redirect('detail_devis', pk=pk)

    if request.method == 'POST':
        numero = devis.numero
        devis.delete()
        messages.success(request, f'🗑️ Devis {numero} supprimé.')
        return redirect('liste_devis')

    return render(request, 'devis/confirmer_suppression.html', {'devis': devis})


@login_required
@transaction.atomic
def transformer_en_facture(request, pk):
    devis = get_object_or_404(Devis.objects.select_for_update(), pk=pk, utilisateur=request.user)

    if devis.statut != 'accepte':
        messages.error(request, '❌ Seul un devis accepté peut être transformé en facture.')
        return redirect('detail_devis', pk=pk)

    if devis.transforme_en_facture:
        messages.error(request, '❌ Ce devis a déjà été transformé en facture.')
        return redirect('detail_devis', pk=pk)

    if request.method == 'POST':
        from factures.models import Facture, LigneFacture
        from devis.utils import generer_numero_facture
        import datetime

        client = devis.client
        pays_facture = devis.pays or getattr(client, 'pays_nom', '')
        type_taxe_facture = devis.type_taxe or getattr(client, 'type_taxe_nom', 'TVA')
        taux_taxe_facture = devis.taux_taxe or getattr(client, 'taux_tva', 0)

        facture = Facture.objects.create(
            utilisateur=request.user,
            client=client,
            devis=devis,
            numero=generer_numero_facture(request.user),
            date_echeance=timezone.now().date() + datetime.timedelta(days=30),
            notes=devis.notes,
            statut='en_attente',
            pays=pays_facture,
            type_taxe=type_taxe_facture,
            taux_taxe=taux_taxe_facture,
            devise_choisie=devis.devise_choisie,
            snapshot_source={
                'devis_numero': devis.numero,
                'client': {'nom': client.nom, 'email': client.email},
                'notes': devis.notes,
                'devise': devis.devise_choisie,
                'taxes_personnalisees': devis.taxes_personnalisees or {},
                'lignes': [
                    {
                        'description': ligne.description,
                        'quantite': str(ligne.quantite),
                        'prix_unitaire': str(ligne.prix_unitaire),
                    }
                    for ligne in devis.lignes.all()
                ],
            },
        )
        
        if devis.taxes.exists():
            facture.taxes.set(devis.taxes.all())
        
        # ✅ Copier les taxes personnalisées
        if hasattr(devis, 'taxes_personnalisees') and devis.taxes_personnalisees:
            facture.taxes_personnalisees = devis.taxes_personnalisees
            facture.save(update_fields=['taxes_personnalisees'])

        for ligne in devis.lignes.all().select_related('produit'):
            LigneFacture.objects.create(
                facture=facture,
                description=ligne.description,
                quantite=ligne.quantite,
                prix_unitaire=ligne.prix_unitaire,
            )

        devis.transforme_en_facture = True
        devis.save(update_fields=['transforme_en_facture'])
        journaliser_devis(devis, 'transformation_en_facture', devis.statut, request.user,
                          f'Facture {facture.numero} créée depuis ce devis')

        messages.success(request, f'✅ Facture {facture.numero} créée avec succès !')
        return redirect('detail_facture', pk=facture.pk)

    return render(request, 'devis/confirmer_transformation.html', {'devis': devis})


@login_required
def telecharger_pdf_devis(request, pk):
    devis = get_object_or_404(Devis, pk=pk, utilisateur=request.user)
    from .pdf import generer_pdf_devis

    buffer = generer_pdf_devis(devis)

    nom_fichier = f"devis_{devis.numero}.pdf"
    chemin_relatif = f"devis/pdf/{nom_fichier}"
    chemin_complet = os.path.join(settings.MEDIA_ROOT, chemin_relatif)

    os.makedirs(os.path.dirname(chemin_complet), exist_ok=True)

    with open(chemin_complet, 'wb') as f:
        f.write(buffer.getvalue())

    devis.fichier_pdf = chemin_relatif
    devis.save()

    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{nom_fichier}"'
    return response


@login_required
def envoyer_devis_email(request, pk):
    """Envoie le devis par email au client ou à une autre personne"""
    devis = get_object_or_404(Devis, pk=pk, utilisateur=request.user)
    
    # Récupérer l'option choisie par l'utilisateur
    option_destinataire = request.POST.get('option_destinataire')
    
    # Déterminer l'adresse email du destinataire
    if option_destinataire == 'client':
        email_destinataire = devis.client.email
        if not email_destinataire:
            messages.error(request, f"Le client {devis.client.nom} n'a pas d'adresse email enregistrée.")
            return redirect('liste_devis')
    else:
        email_destinataire = request.POST.get('email_autre')
        if not email_destinataire:
            messages.error(request, "Veuillez saisir une adresse email.")
            return redirect('liste_devis')
    
    # Vérifier que le PDF existe, sinon le générer
    from .pdf import generer_pdf_devis
    buffer = generer_pdf_devis(devis)
    
    # Base URL pour les liens absolus
    base_url = request.build_absolute_uri('/')[:-1]
    
    # Contexte pour le template email
    context = {
        'devis': devis,
        'client': devis.client,
        'total_ht': devis.calculer_total_ht(),
        'total_ttc': devis.calculer_total_ttc(),
        'tva': devis.calculer_tva(),
        'devise': devis.get_devise(),
        'date_validite': devis.date_validite,
        'lien_devis': f"{base_url}{reverse('detail_devis', args=[devis.pk])}",
        'lien_pdf': f"{base_url}{reverse('pdf_devis', args=[devis.pk])}",
        'utilisateur': request.user,
        'taxes_details': devis.get_taxes_details(),
    }
    
    # Rendre le template HTML
    html_message = render_to_string('devis/emails/devis_email.html', context)
    plain_message = strip_tags(html_message)
    
    sujet = f"Devis {devis.numero} - {devis.client.nom}"
    try:
        send_transactional_email(
            subject=sujet, recipient=email_destinataire, text_body=plain_message,
            html_body=html_message, type_email='factures', reply_to=request.user.email,
            attachments=[(f"devis_{devis.numero}.pdf", buffer.getvalue(), 'application/pdf')],
        )
        journaliser_devis(devis, 'envoi_email', acteur=request.user,
                          commentaire=f'Email envoyé à {email_destinataire}')
        messages.success(request, f"Devis {devis.numero} envoyé par email à {email_destinataire}")
    except Exception:
        logger.exception("Envoi du devis %s vers %s impossible", devis.numero, email_destinataire)
        messages.error(request, "L'e-mail n'a pas pu être envoyé. Vérifiez la configuration SMTP ou réessayez plus tard.")
    
    return redirect('liste_devis')


@login_required
def tableau_de_bord(request):
    from factures.models import Facture
    from clients.models import Client
    import json
    from datetime import date
    from dateutil.relativedelta import relativedelta

    nb_clients = Client.objects.filter(utilisateur=request.user).count()
    nb_devis = Devis.objects.filter(utilisateur=request.user).count()
    nb_devis_en_attente = Devis.objects.filter(utilisateur=request.user, statut='en_attente').count()
    nb_factures = Facture.objects.filter(utilisateur=request.user).count()
    nb_factures_payees = Facture.objects.filter(utilisateur=request.user, statut='payee').count()

    factures_payees = Facture.objects.filter(utilisateur=request.user, statut='payee')
    ca_total = sum(f.calculer_total_ttc() for f in factures_payees)
    factures_attente = Facture.objects.filter(utilisateur=request.user, statut='non_payee')
    montant_attente = sum(f.calculer_total_ttc() for f in factures_attente)

    derniers_devis = Devis.objects.filter(utilisateur=request.user).order_by('-date_creation')[:5]
    dernieres_factures = Facture.objects.filter(utilisateur=request.user).order_by('-date_creation')[:5]

    aujourd_hui = date.today()
    mois_labels, devis_par_mois, factures_par_mois = [], [], []
    for i in range(11, -1, -1):
        mois = aujourd_hui - relativedelta(months=i)
        mois_labels.append(mois.strftime('%b %Y'))
        devis_par_mois.append(
            Devis.objects.filter(
                utilisateur=request.user,
                date_creation__year=mois.year,
                date_creation__month=mois.month
            ).count()
        )
        factures_par_mois.append(
            Facture.objects.filter(
                utilisateur=request.user,
                date_creation__year=mois.year,
                date_creation__month=mois.month
            ).count()
        )

    ca_labels, ca_par_mois = [], []
    for i in range(5, -1, -1):
        mois = aujourd_hui - relativedelta(months=i)
        ca_labels.append(mois.strftime('%b %Y'))
        fs = Facture.objects.filter(
            utilisateur=request.user,
            statut='payee',
            date_creation__year=mois.year,
            date_creation__month=mois.month
        )
        ca_par_mois.append(float(sum(f.calculer_total_ttc() for f in fs)))

    devis_statuts_labels = ['En attente', 'Acceptés', 'Refusés']
    devis_statuts_data = [
        Devis.objects.filter(utilisateur=request.user, statut='en_attente').count(),
        Devis.objects.filter(utilisateur=request.user, statut='accepte').count(),
        Devis.objects.filter(utilisateur=request.user, statut='refuse').count(),
    ]
    factures_statuts_labels = ['Non payées', 'Payées', 'Annulées']
    factures_statuts_data = [
        Facture.objects.filter(utilisateur=request.user, statut='non_payee').count(),
        Facture.objects.filter(utilisateur=request.user, statut='payee').count(),
        Facture.objects.filter(utilisateur=request.user, statut='annulee').count(),
    ]

    return render(request, 'tableau_de_bord.html', {
        'nb_clients': nb_clients,
        'nb_devis': nb_devis,
        'nb_devis_en_attente': nb_devis_en_attente,
        'nb_factures': nb_factures,
        'nb_factures_payees': nb_factures_payees,
        'ca_total': ca_total,
        'montant_attente': montant_attente,
        'derniers_devis': derniers_devis,
        'dernieres_factures': dernieres_factures,
        'mois_labels': json.dumps(mois_labels),
        'devis_par_mois': json.dumps(devis_par_mois),
        'factures_par_mois': json.dumps(factures_par_mois),
        'ca_labels': json.dumps(ca_labels),
        'ca_par_mois': json.dumps(ca_par_mois),
        'devis_statuts_labels': json.dumps(devis_statuts_labels),
        'devis_statuts_data': json.dumps(devis_statuts_data),
        'factures_statuts_labels': json.dumps(factures_statuts_labels),
        'factures_statuts_data': json.dumps(factures_statuts_data),
    })
