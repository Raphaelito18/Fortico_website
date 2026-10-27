# Rapport d'audit de préparation — FORTICO

**Date :** 27 octobre 2026
**Périmètre :** audit local et préparation documentaire. Aucun déploiement, commit, push, changement DNS, migration de la base de développement ou suppression manuelle n'a été effectué.

## Validé

- **Recette visuelle existante :** rapport du 27 octobre 2026, Chrome 155 / Playwright 1.64.1, 10 routes × 4 dimensions (360×800, 390×844, 768×1024, 1440×900), 40 mesures. Le rapport conclut à zéro débordement horizontal, image cassée, erreur JS/page/console ou requête échouée ; menu mobile et formulaire contrôlés. Les détails étaient testés avec fixtures navigateur, sans créer de contenu métier dans PostgreSQL. Captures et preuve : [`rapport-recette.md`](../../qa-report/rapport-recette.md), [`résultats JSON`](../../qa-report/visual-qa-results-2026-10-27T19-03-58-483Z.json), dossier [`captures`](../../qa-report/screenshots-2026-10-27T19-03-58-483Z/).
- **PostgreSQL :** le shell Django s'est connecté réellement au moteur `postgresql`; `CONN_MAX_AGE=0`. Le `.env` local reste privé/ignoré et sélectionne PostgreSQL ; `backend/db.sqlite3` est présent mais ignoré et n'est pas le moteur actif. Aucun mot de passe ni clé n'a été affiché.
- **Tests backend après corrections :** 33 tests Django `apps.core` et `apps.content` réussis sur PostgreSQL. Le runner a utilisé sa base de test temporaire ; aucune donnée de la base de développement n'a été supprimée ni migrée par une commande d'exploitation.
- **Tests frontend :** 3 réussis. **Lint :** réussi. **Build Vite production :** réussi. Le premier build dans le bac à sable Windows a échoué avec `spawn EPERM`; la même commande `npm run build` a réussi après autorisation d'exécution hors bac à sable.
- **Contrôle `manage.py check --deploy` :** exécuté avec des valeurs HTTPS et un secret aléatoires temporaires réservés au contrôle, sur `fortico.invalid`; aucun de ces placeholders n'a été enregistré. Il reste un avertissement Django `security.W004` parce que HSTS reste à 0, choix prudent tant que le domaine et ses sous-domaines ne sont pas confirmés.
- **Secrets Git/bundle :** scan à haute confiance des fichiers suivis sans correspondance (clés privées, tokens usuels, URL PostgreSQL avec identifiants). `backend/.env` et `frontend/.env` ne sont pas suivis et sont ignorés. Le bundle ne contient ni URL d'API `localhost:8000`/`127.0.0.1:8000`, ni marqueur de clé Django. La chaîne `http://localhost` observée dans le bundle appartient au fallback interne de React Router, pas à l'API.
- **Contenus et fichiers :** les querysets publics filtrent les brouillons ; les modifications d'administration sont `IsAdminUser`; les documents privés sont servis par une vue Django qui masque les brouillons aux visiteurs, avec `no-store` et `nosniff`. Les stockages applicatifs pointent vers `private_media`, hors de `MEDIA_URL`. Les tests vérifient le téléchargement autorisé, le refus d'accès direct ancien `/media/certificates/documents/...`, la validation PDF/image et la limite de taille. Le dossier `media`/`private_media` local ne contenait aucun fichier trouvé lors de l'inventaire.
- **Formulaire de contact :** tests existants confirment l'envoi anonyme, les champs invalides (400), la limite de 5/heure (429) et l'accès admin réservé. Aucun 401 anonyme n'est signalé dans la recette finale. Un test de régression ajouté confirme que `X-Forwarded-For` fourni par un client non approuvé ne peut pas falsifier l'IP enregistrée quand `DRF_NUM_PROXIES=0`.
- **Indexation :** ajout d'un interrupteur `DJANGO_SEARCH_INDEXING_ENABLED`, désactivé par défaut : `robots.txt` indique `Disallow: /` et le sitemap répond 503 jusqu'à validation explicite du domaine et des contenus.
- **Reverse proxy :** la procédure bloque les URL directes `/media/` et `/private_media/`, et prévoit un en-tête `X-Robots-Tag: noindex, nofollow` jusqu'à l'ouverture autorisée de l'indexation.
- **Journaux/configuration :** les journaux Django vont à stdout/stderr, sans journalisation volontaire des champs du formulaire. Les erreurs et refus HTTP ont des logs applicatifs ; les API utilisent les réponses d'erreur DRF. Avec `DEBUG=False`, Django n'affiche pas ses pages de diagnostic.

## Corrections de cet audit

- Connexions PostgreSQL persistantes : le réglage codé en dur à 60 s est devenu `DB_CONN_MAX_AGE`, valeur par défaut 0, avec contrôles de valeur non négative et vérification de santé des connexions réutilisées. L'incident précédent s'explique par le serveur de développement multithreadé, les requêtes navigateur concurrentes et 60 s de connexions persistantes par thread ; aucune fermeture manuelle à chaque requête n'a été ajoutée.
- Anti-usurpation de l'IP de contact : DRF utilise maintenant `DRF_NUM_PROXIES=0` par défaut ; l'application utilise `REMOTE_ADDR` tant qu'une chaîne de proxys de confiance n'est pas explicitement définie. La configuration du proxy doit normaliser `X-Forwarded-For` avant de configurer un nombre positif.
- HSTS : durée, include-subdomains et preload sont configurables ; les valeurs par défaut n'activent ni HSTS ni preload avant le choix du domaine.
- Production fail-closed : en `DEBUG=False`, les réglages refusent les hôtes locaux/génériques, les origines CORS/CSRF HTTP ou locales, SQLite et les URLs publiques non HTTPS/non confirmées. Cookies session/CSRF et redirection HTTPS sont activés en production.
- SMTP : ajout de `EMAIL_USE_SSL` et refus de TLS + SSL activés simultanément. L'exemple d'environnement expose les paramètres attendus sans identifiants.
- OpenAPI : réponses binaires explicitement documentées pour les vues d'images et de téléchargement PDF ; les avertissements `drf_spectacular.W002` ont disparu du contrôle `--deploy`.
- SEO : indexation bloquée par défaut tant que FORTICO ne l'active pas.

## À finaliser

- Choisir le fournisseur/serveur d'hébergement et le reverse proxy, puis fournir le domaine officiel (et ses variantes), certificats, hôtes et origines CORS/CSRF exacts.
- Choisir et épingler un serveur de processus WSGI : le dépôt contient les points d'entrée WSGI/ASGI, mais aucun serveur WSGI de production n'est présent dans `backend/requirements.txt`.
- Fournir une clé Django de production différente de celle du développement et les identifiants PostgreSQL de production par un gestionnaire de secrets ; jamais dans Git ou une archive non chiffrée.
- Choisir le fournisseur SMTP et fournir host/port, utilisateur/secret selon son mode d'authentification, TLS ou SSL, expéditeur vérifié et destinataire des demandes. Aucun e-mail réel n'a été envoyé ; la livraison des notifications reste non validée.
- Choisir un cache partagé avant d'utiliser plusieurs workers/instances. Aucun `CACHES` partagé n'est configuré : le throttle DRF utilise le cache mémoire local par processus et la limite de contact peut donc être multipliée entre processus.
- Après décision de topologie, renseigner `DRF_NUM_PROXIES` et prouver que le proxy de bord remplace/chaîne correctement les en-têtes transférés. Sinon les visiteurs peuvent partager l'adresse proxy et la limite, bien que l'usurpation soit neutralisée par défaut.
- Configurer HSTS après test HTTPS et décision explicite sur les sous-domaines. Le seul avertissement `check --deploy` restant est W004 (HSTS non configuré), volontairement non supprimé.
- Renseigner `VITE_PUBLIC_SITE_URL` et `PUBLIC_SITE_URL` avec le même domaine HTTPS ; activer ensuite `DJANGO_SEARCH_INDEXING_ENABLED=True` après validation des contenus publics. Les métadonnées des pages de détail sont créées côté client React ; les robots sociaux sans exécution JavaScript peuvent ne voir que les balises générales de `index.html`.
- Valider les textes métier : le frontend affiche encore des contenus de maquette clairement identifiés comme provisoires lorsque la base ne contient pas d'expertises ou certaines informations entreprise.
- Définir RPO/RTO, fréquence, rétention, chiffrement, emplacement des sauvegardes et exécuter ultérieurement un exercice de restauration dans un environnement isolé.

## Bloqué par l'environnement ou décisions manquantes

- Aucun serveur de production, reverse proxy réel, certificat, DNS ou domaine officiel n'est disponible ; ces éléments n'ont pas été vérifiés.
- SMTP et destinataire sont absents du `.env` local ; test de livraison impossible et aucun e-mail n'a été envoyé.
- L'affichage HTTP 500 derrière la vraie infrastructure et la collecte des logs après proxy ne peuvent pas être vérifiés sans serveur. Les réponses 400/403/404 sont couvertes par les tests ; les handlers Django restent génériques et `DEBUG=False` est requis.
- Aucune restauration n'a été tentée ; seules les procédures ont été rédigées afin de ne toucher à aucune donnée.

## État Git et fichiers

À la clôture de l'audit, la branche était `main`, en avance d'un commit sur `origin/main`. L'index contenait déjà un vaste ensemble de modifications/staging et de rapports/captures QA avant cet audit ; il a été préservé. Aucun commit, push, reset ou nettoyage Git n'avait alors été fait. Les changements de l'audit étaient restés non indexés ; les trois nouveaux documents apparaissaient non suivis.

Pendant la préparation de publication qui a suivi, les trois blancs finaux signalés par `git diff --cached --check` dans des fichiers déjà indexés (`backend/apps/content/tests.py`, `backend/apps/core/utils.py`, `qa-report/rapport-recette.md`) ont été retirés. La vérification de patch est maintenant propre ; Git signale uniquement une conversion CRLF/LF potentielle sur certains fichiers texte Windows.

Fichiers modifiés pendant l'audit :

- `backend/fortico/settings.py`
- `backend/fortico/seo.py`
- `backend/apps/core/views.py`
- `backend/apps/core/test_endpoints.py`
- `backend/apps/content/views.py`
- `backend/apps/content/test_seo.py`
- `backend/.env.example`
- `frontend/.env.example`
- `docs/operations/PRODUCTION_READINESS.md` (nouveau)
- `docs/operations/BACKUP_RESTORE.md` (nouveau)
- `docs/operations/AUDIT_REPORT_2026-10-27.md` (nouveau)

Aucun fichier préexistant ni aucune capture QA n'a été supprimé.

## Décision

**Le projet n'est pas prêt à être déployé en production aujourd'hui.** Le socle applicatif passe les suites disponibles et les garde-fous ont été renforcés, mais le domaine, l'hébergement, SMTP et le cache partagé (si plusieurs workers) restent à choisir/configurer ; les sauvegardes doivent être testées isolément. Il est prêt pour une préparation de préproduction encadrée après fourniture de ces décisions, pas pour une mise en ligne immédiate.
