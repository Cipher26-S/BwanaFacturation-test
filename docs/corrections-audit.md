# Corrections de l'audit Bwana Facturation

## Changements livrés

- L'échec SMTP ne valide plus jamais un compte : le compte reste inactif et un lien peut être renvoyé.
- Les e-mails d'activation, de réinitialisation, de devis et de factures passent par un service commun qui journalise les erreurs sans exposer les détails SMTP aux utilisateurs.
- Les statuts ne font plus partie des formulaires de devis et de factures : ils sont imposés par le workflow.
- Les devis et factures ne sont modifiables/supprimables qu'à l'état `en_attente`.
- Les transitions de facture sont limitées à `en_attente → approuvee/rejetee`, `approuvee → non_payee/rejetee` et `non_payee → payee/annulee`.
- Les validations publiques et la conversion devis-vers-facture utilisent un verrou de base de données pour empêcher le double traitement.
- Les événements métier sont conservés dans `HistoriqueDevis` et `HistoriqueFacture`.
- La facture issue d'un devis conserve un instantané du document source (lignes, client, devise, taxes et notes) pour l'audit.

## Déploiement

1. Sauvegarder la base PostgreSQL.
2. Installer les dépendances : `pip install -r requirements.txt`.
3. Appliquer les migrations : `python manage.py migrate`.
4. Lancer les tests sans dépendre de PostgreSQL local : `python manage.py test users devis factures --settings=config.test_settings`.
5. Dans l'administration, envoyer un e-mail de test pour les configurations `principal` et `factures`.

## Recette fonctionnelle

1. Créer un compte, vérifier qu'il reste inactif sans clic sur le lien, puis utiliser « Renvoyer l'email d'activation ».
2. Tester « Mot de passe oublié », un lien invalide et un lien expiré.
3. Créer un devis : il doit être `en_attente`; le formulaire ne doit pas permettre de choisir un autre état.
4. Approuver le devis par le lien interne puis l'accepter par le lien client; seule cette séquence permet la conversion en facture.
5. Vérifier qu'un devis accepté est impossible à modifier ou supprimer.
6. Créer une facture, l'approuver, la faire accepter par le client, puis la marquer payée.
7. Vérifier les entrées d'historique et le blocage de toute modification après traitement.
