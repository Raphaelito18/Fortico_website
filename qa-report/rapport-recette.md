# Rapport de recette visuelle et interactive — FORTICO

**Date :** 27 octobre 2026

**Résultat :** recette navigateur exécutée sur Chrome ; aucune correction backend nécessaire.

## Environnement

- Chrome 155.0.8059.85 piloté par Playwright 1.64.1, ajouté aux dépendances de développement avec mise à jour du lockfile.
- Frontend servi sur `http://127.0.0.1:5173/` par l’instance Vite déjà présente.
- Django testé sur `http://127.0.0.1:8000/`, connecté à PostgreSQL 18.1 (`fortico_db`). Le serveur de recette a été configuré avec `CONN_MAX_AGE=0` pour ne pas accumuler des connexions PostgreSQL pendant les navigations.
- SMTP et destinataire de notification non configurés.

## Routes et affichage

Les dix routes ci-dessous ont été ouvertes aux quatre dimensions demandées, soit 40 mesures Playwright : accueil, expertises, réalisations, détail de réalisation, à propos, certificats, actualités, détail d’article, contact et 404.

Les routes de détail sans slug publié affichent normalement la page 404. Les parcours de détail et les liens de cartes ont également été testés avec des réponses factices limitées à Playwright ; aucune donnée métier n’a été ajoutée à PostgreSQL.

- Dimensions vérifiées : 360 × 800, 390 × 844, 768 × 1024 et 1440 × 900 px.
- Débordement horizontal : aucun sur les 40 mesures.
- Images : aucune image cassée ; logo et illustration de l’accueil chargés.
- Menu mobile : ouverture, navigation et fermeture vérifiées à 360, 390 et 768 px.
- Cartes : navigation vers les détails de réalisation et d’article vérifiée avec les fixtures navigateur.
- Pied de page : visible sur toutes les pages ; le défaut d’espace blanc après le pied de page sur les pages courtes a été corrigé.

## Formulaire de contact

- Une soumission anonyme a envoyé `POST /api/v1/contact/` sans en-tête d’autorisation et reçu **201**. Le message de succès est apparu, le formulaire a été réinitialisé et le bouton est redevenu actif.
- Les contrôles HTML bloquent les champs requis vides et l’adresse invalide. Une soumission invalide transmise au serveur a reçu **400** avec les erreurs de validation ; aucun enregistrement invalide n’a été créé.
- Une réponse **429** a été simulée dans le navigateur pour vérifier l’état de l’interface sans consommer la limite réelle. Le message de limitation s’affiche et le bouton redevient actif.
- Une panne API **503** simulée affiche l’état d’indisponibilité du contenu.
- Le 401 antérieur n’a pas été reproduit ; aucun en-tête d’autorisation n’était présent lors de la soumission valide.
- La demande valide de QA a été identifiée avec son marqueur unique, puis supprimée. Aucune ligne marquée `QA-BROWSER-` ne subsiste. Aucun e-mail réel n’a été envoyé ; la livraison SMTP reste à valider après configuration.

## Console et réseau

- Erreurs JavaScript, erreurs de page et avertissements console : **0**.
- Requêtes réseau réellement échouées : **0**. Des requêtes annulées (`ERR_ABORTED`) correspondent au nettoyage normal des appels React lors du démontage des pages.
- Les réponses 404 des slugs de détail inexistants, 400 du formulaire invalide, 503 et 429 simulés sont attendues.
- Le navigateur demandait `/favicon.ico` et recevait 404. L’icône existante du logo a été déclarée dans `index.html` ; le 404 a disparu lors de la passe finale.

## Corrections apportées

- Ajout de `flex: 1` à `#main-content` pour que le pied de page reste au bas de la fenêtre sur les pages courtes.
- Déclaration du logo existant comme favicon pour supprimer la requête 404.
- Ajout de Playwright aux dépendances de développement afin de conserver le script de recette réexécutable.

## Tests de régression

- Django sur PostgreSQL : **31 tests réussis**.
- Frontend : **3 tests réussis**.
- Lint : réussi.
- Build de production : réussi. L’exécution dans le bac à sable échouait avec `spawn EPERM` ; le build a été relancé hors bac à sable et a réussi.

Le test Django émet un avertissement non bloquant indiquant que `backend/staticfiles/` n’existe pas. Aucun test n’échoue.

## Captures et résultats détaillés

Toutes les captures de la passe finale sont dans [`screenshots-2026-10-27T19-03-58-483Z`](screenshots-2026-10-27T19-03-58-483Z/). Les captures des pages d’accueil et Contact couvrent les quatre dimensions ; les autres routes sont capturées à 1440 × 900. Les deux captures de détails sont explicitement des fixtures navigateur.

- [Accueil — 360 × 800](screenshots-2026-10-27T19-03-58-483Z/home-360x800.png)
- [Accueil — 390 × 844](screenshots-2026-10-27T19-03-58-483Z/home-390x844.png)
- [Accueil — 768 × 1024](screenshots-2026-10-27T19-03-58-483Z/home-768x1024.png)
- [Accueil — 1440 × 900](screenshots-2026-10-27T19-03-58-483Z/home-1440x900.png)
- [Contact — 360 × 800](screenshots-2026-10-27T19-03-58-483Z/contact-360x800.png)
- [Contact — 390 × 844](screenshots-2026-10-27T19-03-58-483Z/contact-390x844.png)
- [Contact — 768 × 1024](screenshots-2026-10-27T19-03-58-483Z/contact-768x1024.png)
- [Contact — 1440 × 900](screenshots-2026-10-27T19-03-58-483Z/contact-1440x900.png)
- [Expertises — 1440 × 900](screenshots-2026-10-27T19-03-58-483Z/expertises-1440x900.png)
- [Réalisations — 1440 × 900](screenshots-2026-10-27T19-03-58-483Z/realisations-1440x900.png)
- [Détail réalisation, fixture navigateur](screenshots-2026-10-27T19-03-58-483Z/detail-realisation-browser-fixture-1440x900.png)
- [À propos — 1440 × 900](screenshots-2026-10-27T19-03-58-483Z/entreprise-1440x900.png)
- [Certificats — 1440 × 900](screenshots-2026-10-27T19-03-58-483Z/certificats-1440x900.png)
- [Actualités — 1440 × 900](screenshots-2026-10-27T19-03-58-483Z/actualites-1440x900.png)
- [Détail article, fixture navigateur](screenshots-2026-10-27T19-03-58-483Z/detail-article-browser-fixture-1440x900.png)
- [Page 404 — 1440 × 900](screenshots-2026-10-27T19-03-58-483Z/404-1440x900.png)

Le [résultat Playwright détaillé (JSON)](visual-qa-results-2026-10-27T19-03-58-483Z.json) et le [script réexécutable](fortico-visual-qa.mjs) sont joints au rapport.
