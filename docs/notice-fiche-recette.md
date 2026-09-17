# Fiche de recette Bwana Facturation

## Objet

Cette fiche permet à chaque collègue d'exécuter les 7 cas de test fonctionnels et de consigner le résultat obtenu.

## Colonnes à remplir

- **Résultat obtenu** : décrire brièvement ce qui s'est réellement passé.
- **Statut (OK/NOK)** : mettre `OK` si le résultat correspond entièrement au résultat attendu, sinon `NOK`.
- **Testeur** : nom ou initiales de la personne qui exécute le test.
- **Date** : date d'exécution.
- **Commentaires / anomalie** : message d'erreur, capture d'écran, numéro du document ou précision utile.

## Import dans Excel

1. Ouvrir Excel.
2. Aller dans **Données > À partir d'un fichier texte/CSV**.
3. Sélectionner `fiche-recette-bwana-facturation.csv`.
4. Choisir l'encodage UTF-8 et le séparateur `point-virgule`.
5. Enregistrer le fichier au format `.xlsx` et le partager avec l'équipe.

## Import dans Google Sheets

1. Ouvrir une feuille Google Sheets.
2. Choisir **Fichier > Importer > Importer**.
3. Sélectionner le fichier CSV.
4. Choisir **Séparateur personnalisé** puis saisir `;`.
5. Partager la feuille avec les collègues et leur donner le droit de modifier.

## Règle de décision

Un cas est `OK` uniquement si toutes les conditions du résultat attendu sont respectées. Sinon, mettre `NOK` et décrire l'anomalie. Ne jamais inscrire de mot de passe ou de secret SMTP dans la feuille.

## Périmètre

Cette fiche couvre les fonctions modifiées dans le rapport et les workflows devis/factures. Les feuilles de paie ne font pas partie du périmètre fonctionnel de cette application de facturation et doivent être suivies dans un document RH séparé.
