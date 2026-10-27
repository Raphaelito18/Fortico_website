# Préparation à la mise en production — FORTICO

État au 27 octobre 2026. Ce document prépare un futur déploiement ; aucun serveur, DNS ou environnement public n'a été modifié pendant l'audit. L'hébergeur et le domaine restent à choisir/confirmer par FORTICO.

## Décision actuelle

La recette locale précédente et les tests fournissent une bonne base, mais le site n'est pas prêt à être publié immédiatement : il manque le domaine officiel, les paramètres de SMTP, un serveur cible et une décision d'exploitation/backup. Ne pas indexer avant validation du contenu public et de `PUBLIC_SITE_URL`.

## Architecture constatée

- API Django/DRF sous `/api/v1/`, administration sous `/admin/`, schéma sous `/api/schema/` et documentation sous `/api/docs/`.
- Frontend React/Vite construit dans `frontend/dist/` ; l'API est appelée sur `/api` par défaut.
- PostgreSQL sélectionné explicitement avec `DB_ENGINE=postgresql`.
- WhiteNoise sert les fichiers collectés dans `backend/staticfiles/`.
- Les images de contenu et documents de certificats utilisent `PrivateMediaStorage` dans `backend/private_media/` et sont servis par des vues Django qui contrôlent la publication. Aucun alias web vers ce répertoire ne doit exister.

## Variables à fournir via un gestionnaire de secrets/configuration

Ne pas copier les valeurs locales de `backend/.env` vers la production. Fournir une clé Django générée uniquement pour l'environnement de production, des identifiants PostgreSQL propres à cet environnement, et les valeurs approuvées ci-dessous.

Backend :

- `DJANGO_DEBUG=False`
- `DJANGO_SECRET_KEY` : secret aléatoire, privé, indépendant du développement.
- `DJANGO_ALLOWED_HOSTS` : noms d'hôte exacts, sans schéma ni chemin.
- `DJANGO_CORS_ALLOWED_ORIGINS` : origines HTTPS exactes du navigateur si le frontend est séparé ; laisser vide pour une architecture strictement same-origin.
- `DJANGO_CSRF_TRUSTED_ORIGINS` : origines HTTPS exactes si des requêtes CSRF viennent d'une origine distincte. Same-origin peut rester vide.
- `DJANGO_SECURE_SSL_REDIRECT=True` derrière un proxy configuré pour transmettre `X-Forwarded-Proto: https` après avoir écrasé la valeur client.
- `DB_ENGINE=postgresql`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`.
- `DB_CONN_MAX_AGE=0` initialement. Toute valeur positive doit être dimensionnée avec le nombre maximal de workers/threads par processus et la limite PostgreSQL. Pour le modèle Django à connexions persistantes, une borne haute approximative est `instances × workers × threads` ; réserver également des connexions à l'administration, migrations et supervision. Ne pas confondre cette option avec un pool externe.
- `DRF_NUM_PROXIES=0` tant que la topologie n'est pas établie. Si un proxy/CDN est introduit, configurer le nombre exact de proxys de confiance uniquement après s'être assuré que le proxy de bord remplace ou complète correctement `X-Forwarded-For`. Avec 0, la limite et l'adresse enregistrée utilisent `REMOTE_ADDR` (souvent l'adresse du proxy, donc les visiteurs peuvent partager une limite).
- `DJANGO_LOG_LEVEL=INFO` (journaux vers stdout/stderr ; collecte et rétention à définir).
- `DJANGO_SECURE_HSTS_SECONDS=0` au démarrage. Après confirmation que tous les sous-domaines concernés sont accessibles en HTTPS, augmenter progressivement ; n'activer include-subdomains/preload qu'après validation explicite.
- SMTP : `DJANGO_EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, un seul de `EMAIL_USE_TLS` / `EMAIL_USE_SSL`, `DEFAULT_FROM_EMAIL` et `CONTACT_NOTIFICATION_EMAIL`.
- `FRONTEND_URL` et `PUBLIC_SITE_URL` avec le domaine officiel confirmé.
- `DJANGO_SEARCH_INDEXING_ENABLED=False` au départ. Après validation du domaine officiel et des contenus publiés, passer à `True` pour permettre l'exploration ; `robots.txt` est une consigne publique, pas un contrôle d'accès.

Frontend :

- `VITE_API_BASE_URL=/api` si le proxy et le frontend partagent l'origine. Si l'API est séparée, utiliser l'URL HTTPS validée, terminée par `/api`.
- `VITE_PUBLIC_SITE_URL` : origine officielle sans chemin ; nécessaire aux canoniques/Open Graph des pages de détail.
- Aucune variable `VITE_*` ne doit contenir de secret : les valeurs sont compilées dans le JavaScript public.

Les fichiers `.env` locaux sont ignorés par Git. Garder cette propriété et ne pas déposer de secrets dans des archives non chiffrées.

Avec `DJANGO_DEBUG=False`, les réglages refusent maintenant le démarrage si les hôtes/origines de production ne sont pas explicites, si PostgreSQL n'est pas choisi, ou si `PUBLIC_SITE_URL`/`FRONTEND_URL` n'utilisent pas une origine HTTPS confirmée. Ces garde-fous empêchent d'exploiter silencieusement les valeurs locales d'exemple.

## Ordre de mise en service (à exécuter plus tard, après choix de l'hébergeur)

1. Provisionner un serveur pris en charge et un PostgreSQL isolé pour la production ; restreindre le réseau et créer un rôle applicatif au moindre privilège. Ne pas réutiliser la base de développement.
2. Installer les versions Python/Node compatibles avec `backend/requirements.txt` et le lockfile frontend (`npm ci`), sans mise à jour générale des dépendances. Le dépôt fournit WSGI/ASGI Django mais aucun serveur de processus WSGI de production n'est actuellement épinglé : choisir et verrouiller le serveur WSGI/process manager après décision de plateforme ; ne jamais utiliser `runserver` en production.
3. Injecter les secrets et variables de configuration par le gestionnaire de secrets de l'hébergeur. Vérifier `DJANGO_DEBUG=False`, les hôtes, origines et moteur PostgreSQL avant démarrage.
4. Construire le frontend reproductiblement (`npm ci`, `npm run build`) avec l'URL API et le domaine public confirmés. Vérifier le bundle : aucune clé/valeur secrète.
5. Construire l'environnement Python, puis exécuter `python manage.py check --deploy`. Résoudre les avertissements de déploiement applicables ; tester la configuration HTTPS derrière un proxy dans un environnement de préproduction.
6. Prendre une sauvegarde PostgreSQL et des deux espaces de fichiers avant migration. Examiner les migrations (`showmigrations`, SQL si nécessaire) et leur compatibilité/temps d'arrêt ; appliquer `migrate` uniquement au serveur de production après approbation de changement. Aucune migration n'a été lancée par le présent audit.
7. Exécuter `collectstatic --noinput`. Servir `backend/staticfiles/` via WhiteNoise ou le serveur web selon une stratégie unique. Publier le contenu compilé `frontend/dist/` par le serveur web.
8. Stocker `backend/media/` et `backend/private_media/` sur volumes persistants séparés du code. Ne jamais configurer de `root`/`alias` web sur `private_media`. N'exposer que les routes de téléchargement contrôlées par Django pour les contenus privés. Protéger aussi les anciens chemins publics de certificats (`/media/certificates/documents/`) par une réponse 404/deny.
9. Configurer le reverse proxy : TLS moderne, renouvellement des certificats, HTTP redirigé vers HTTPS, limite de taille des corps cohérente avec la validation Django (5 Mo par fichier), timeouts mesurés, transmission de `Host` et `X-Forwarded-Proto` fiable. Exemple de logique, à adapter à l'hébergeur : `location /private_media/ { deny all; }`; interdire également `/media/certificates/documents/`; ne jamais aliaser ces chemins vers des fichiers. Le proxy remplace les en-têtes `X-Forwarded-*` reçus du client.
10. Configurer SMTP avec les paramètres transmis par FORTICO et le fournisseur choisi. Démarrer avec envoi de notification désactivé tant que destinataire et expéditeur ne sont pas validés. Valider en préproduction avec un destinataire autorisé seulement ; aucun email réel n'a été envoyé durant l'audit.
11. Installer une sauvegarde planifiée et une alerte d'échec. Définir fréquence, rétention, chiffrement, lieu séparé, RPO/RTO et responsables avec FORTICO ; réaliser un exercice de restauration isolé.
12. Avant ouverture : confirmer domaine/DNS/certificat, hôtes et origines, accès admin, contenus publiés, contact et notification, erreurs 400/403/404/500 sans tracebacks publics, redirections, sitemap/canoniques/robots et sauvegarde récente. N'ouvrir l'indexation qu'après vérification de la production publique et du domaine.

## Reverse proxy et erreurs

Django est configuré pour rediriger vers HTTPS en production, utiliser des cookies secure et croire `X-Forwarded-Proto` ; le proxy doit écraser cet en-tête et n'être qu'une source de confiance. À défaut, boucle de redirections possible. `DEBUG=False` garantit que les réponses d'erreur Django n'incluent pas les pages de debug ; la configuration actuelle n'ajoute pas de vues personnalisées `handler400/403/404/500`. Vérifier les codes et les pages/API génériques après installation. Ne journaliser ni mot de passe, ni clé, ni contenu complet des formulaires.

Règles à transposer au serveur choisi (exemple Nginx, chemins et upstream à adapter) :

```nginx
location ^~ /private_media/ { return 404; }
location ^~ /media/ { return 404; }
add_header X-Robots-Tag "noindex, nofollow" always;

location /api/ {
    client_max_body_size 6m;
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
}
location /admin/ { proxy_pass http://127.0.0.1:8000; }
location /api-auth/ { proxy_pass http://127.0.0.1:8000; }
location = /robots.txt { proxy_pass http://127.0.0.1:8000; }
location = /sitemap.xml { proxy_pass http://127.0.0.1:8000; }
location / {
    root /srv/fortico/current/frontend/dist;
    try_files $uri $uri/ /index.html;
}
```

Ne pas ajouter d'alias public pour `/private_media/` ni `/media/` : aucun modèle actuel ne dépend d'une URL média directe, et les anciennes URLs publiques de certificats doivent rester fermées. Les documents et images doivent continuer de passer par les vues Django avec contrôle de publication et d'accès. Les images publiées sont elles aussi servies via l'API dans le code actuel.

Tant que l'indexation est désactivée, le reverse proxy doit également renvoyer `X-Robots-Tag: noindex, nofollow` sur les réponses du frontend. Retirer cet en-tête uniquement lors de l'ouverture explicite de l'indexation et après approbation du domaine/contenu.

La limitation DRF utilise le cache Django par défaut. Aucun cache partagé n'est configuré dans le dépôt ; le cache mémoire local est propre à chaque processus. Avant un déploiement à plusieurs workers/instances, fournir un cache partagé et le configurer pour que les 5 envois/heure soient réellement agrégés. Sans cela, la limite peut être multipliée par le nombre de processus.

## Domaine, robots et indexation

`DJANGO_SEARCH_INDEXING_ENABLED` désactivé renvoie `Disallow: /` dans `robots.txt` et un sitemap 503, y compris si une URL est présente. `PUBLIC_SITE_URL` pilote le sitemap une fois l'indexation activée ; sans origine reconnue, le sitemap répond 503. `VITE_PUBLIC_SITE_URL` pilote les URLs canoniques et `og:url` des pages de détail. Une valeur vide retire les canoniques. Le domaine doit être choisi une seule fois et reporté dans les deux configurations, `FRONTEND_URL`, les hôtes/CORS/CSRF et le reverse proxy. Le sitemap actuel inclut ses routes publiques prédéfinies et les détails publiés d'articles/projets ; il n'ajoute pas encore les expertises/certificats dynamiques.

## Contrôles de retour arrière

Avant toute mise en service, capturer la révision du code, les versions de dépendances, les migrations avant/après et les sauvegardes. En cas d'incident, arrêter le trafic/maintenance, remettre le frontend précédent et le code précédent si compatibles, puis restaurer la base uniquement vers une base de restauration isolée ou via une procédure de reprise approuvée. Ne jamais appliquer une restauration destructive à la base active sans décision et plan formels. Les migrations destructives nécessitent une stratégie dédiée de retour en avant.

## Informations que FORTICO doit fournir

- Domaine officiel et variantes (www/non-www), gestionnaire DNS et titulaire.
- Fournisseur d'hébergement et architecture cible, région et responsable opérationnel.
- Paramètres PostgreSQL de production, capacité et limite de connexions.
- Fournisseur SMTP, host/port, mode TLS/SSL, expéditeur validé, destinataire métier.
- Coordonnées publiques (téléphone/adresse) et contenu final à publier.
- Politique de sauvegarde : RPO/RTO, rétention, chiffrement, emplacement et personnes habilitées.
- Politique d'indexation, sous-domaines à inclure en HSTS et contacts de supervision.
