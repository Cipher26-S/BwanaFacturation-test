from django.urls import path
from . import views_admin

urlpatterns = [
    # Dashboard
    path('',                              views_admin.admin_dashboard,           name='admin_dashboard'),

    # Utilisateurs
    path('users/',                        views_admin.admin_liste_users,         name='admin_liste_users'),
    path('users/<int:pk>/',               views_admin.admin_detail_user,         name='admin_detail_user'),
    path('users/<int:pk>/toggle/',        views_admin.admin_toggle_user,         name='admin_toggle_user'),
    path('users/<int:pk>/superuser/',     views_admin.admin_toggle_superuser,    name='admin_toggle_superuser'),
    path('users/<int:pk>/supprimer/',     views_admin.admin_supprimer_user,      name='admin_supprimer_user'),
    path('users/<int:pk>/reset-pwd/',     views_admin.admin_reset_password,      name='admin_reset_password'),
    path('users/<int:pk>/impersonate/',   views_admin.admin_impersonate,         name='admin_impersonate'),
    path('stop-impersonate/',             views_admin.admin_stop_impersonate,    name='admin_stop_impersonate'),

    # Historique connexions
    path('connexions/',                   views_admin.admin_historique_connexions, name='admin_historique_connexions'),

    # Maintenance
    path('maintenance/',                  views_admin.admin_maintenance,         name='admin_maintenance'),

    # Annonces
    path('annonces/',                     views_admin.admin_annonces,            name='admin_annonces'),
    path('annonces/ajouter/',             views_admin.admin_ajouter_annonce,     name='admin_ajouter_annonce'),
    path('annonces/<int:pk>/toggle/',     views_admin.admin_toggle_annonce,      name='admin_toggle_annonce'),
    path('annonces/<int:pk>/supprimer/',  views_admin.admin_supprimer_annonce,   name='admin_supprimer_annonce'),

    # ══════════════════════════════════════════
    # PAYS & TAXES — clients / devis / factures
    # ══════════════════════════════════════════
    path('pays-taxes/',                          views_admin.admin_taxes_pays_liste,    name='admin_taxes_pays_liste'),
    path('pays-taxes/ajouter/',                  views_admin.admin_taxes_pays_ajouter,  name='admin_taxes_pays_ajouter'),
    path('pays-taxes/<int:pk>/',                 views_admin.admin_taxes_pays_detail,   name='admin_taxes_pays_detail'),
    path('pays-taxes/<int:pk>/modifier/',        views_admin.admin_taxes_pays_modifier, name='admin_taxes_pays_modifier'),
    path('pays-taxes/<int:pk>/toggle/',          views_admin.admin_taxes_pays_toggle,   name='admin_taxes_pays_toggle'),
    path('pays-taxes/<int:pays_pk>/taxe/ajouter/', views_admin.admin_taxe_ajouter,      name='admin_taxe_ajouter'),
    path('taxe/<int:pk>/toggle/',                views_admin.admin_taxe_toggle,         name='admin_taxe_toggle'),
    path('taxe/<int:pk>/supprimer/',             views_admin.admin_taxe_supprimer,      name='admin_taxe_supprimer'),

    # ══════════════════════════════════════════
    # PAYS & TAXES — catalogue produits
    # ══════════════════════════════════════════
    path('produits-pays/',                          views_admin.admin_produits_pays_liste,    name='admin_produits_pays_liste'),
    path('produits-pays/ajouter/',                  views_admin.admin_produits_pays_ajouter,  name='admin_produits_pays_ajouter'),
    path('produits-pays/<int:pk>/',                 views_admin.admin_produits_pays_detail,   name='admin_produits_pays_detail'),
    path('produits-pays/<int:pk>/modifier/',        views_admin.admin_produits_pays_modifier, name='admin_produits_pays_modifier'),
    path('produits-pays/<int:pays_pk>/typetaxe/ajouter/', views_admin.admin_typetaxe_ajouter, name='admin_typetaxe_ajouter'),
    path('typetaxe/<int:pk>/supprimer/',            views_admin.admin_typetaxe_supprimer,     name='admin_typetaxe_supprimer'),
    path('produits-pays/<int:pays_pk>/province/ajouter/', views_admin.admin_province_ajouter, name='admin_province_ajouter'),
    path('province/<int:pk>/supprimer/',            views_admin.admin_province_supprimer,     name='admin_province_supprimer'),

    # ══════════════════════════════════════════
    # CONFIGURATION EMAIL (NOUVEAU)
    # ══════════════════════════════════════════
    path('email/config/',                 views_admin.admin_config_email,            name='admin_config_email'),
    path('email/config/<int:pk>/modifier/', views_admin.admin_config_email_modifier, name='admin_config_email_modifier'),
    path('email/config/<int:pk>/tester/',   views_admin.admin_config_email_tester,   name='admin_config_email_tester'),
    path('email/config/<int:pk>/activer/',  views_admin.admin_config_email_activer,  name='admin_config_email_activer'),
]