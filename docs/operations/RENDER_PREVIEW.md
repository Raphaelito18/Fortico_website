# Préparation du backend Django sur Render — prévisualisation

État au 27 octobre 2026. Ce document prépare un service de prévisualisation seulement. Aucun service, base distante, variable Render, déploiement ou migration distante n'a été créé ou exécuté. Le dernier commit Git publié reste `ac0d479`; les adaptations décrites ici sont locales jusqu'à leur revue et publication dans le cadre de la mission en cours.

## Architecture et fichiers du dépôt

- Créer plus tard un service Render **Web Service** Python depuis `Raphaelito18/Fortico_website`, branche `main`, avec `backend` comme **Root Directory**. Les commandes de build et de démarrage sont relatives à ce dossier.
- Le frontend Vite reste sur son service Render existant. Les appels sont construits dans `frontend/src/App.jsx` à partir de `VITE_API_BASE_URL`; la valeur `/api` par défaut vise la même origine. Avec des services séparés, il faudra la remplacer par l'URL HTTPS réelle du backend suivie de `/api` et reconstruire le frontend.
- Le WSGI Django existant est `fortico.wsgi:application`.
- `backend/requirements/production.txt` inclut les exigences runtime et Gunicorn. `requirements.txt` inclut déjà Django, psycopg binaire et WhiteNoise : aucune nouvelle dépendance n'est requise.
- WhiteNoise et `CompressedManifestStaticFilesStorage` sont déjà configurés. Le build doit installer les dépendances et lancer `collectstatic`.
- `backend/.python-version` épingle la version Python locale vérifiée, `3.14.2`.
- Il n'y a volontairement pas de `render.yaml` dans cette préparation : la configuration manuelle du tableau de bord évite qu'une application Blueprint crée automatiquement une base ou un service avant vérification du forfait et des coûts. Les valeurs de secrets et domaines restent à saisir dans le tableau de bord après attribution des vraies URL.

## Commandes du service Render

Réglages du futur Web Service (Root Directory = `backend`) :

**Build Command**

```sh
pip install -r requirements/production.txt && python manage.py collectstatic --no-input
```

**Start Command**

```sh
gunicorn fortico.wsgi:application --bind 0.0.0.0:$PORT
```

Ne pas ajouter `python manage.py migrate` à la commande de build ou de démarrage. `collectstatic` rassemble les fichiers statiques et WhiteNoise les sert ; cela ne nécessite pas de persistance pour les médias téléversés.

## Base PostgreSQL distante

Le réglage Django accepte maintenant `DATABASE_URL` avec les schémas `postgres://` et `postgresql://`. Il décode les identifiants URL-encodés, conserve les options de requête PostgreSQL (par exemple `sslmode=require`) et conserve `DB_CONN_MAX_AGE=0` par défaut. Une URL mal formée ou incomplète provoque une erreur de configuration sans imprimer ses identifiants.

Si `DATABASE_URL` est renseignée, elle est prioritaire sur les variables `DB_*`; `DB_ENGINE=sqlite` en même temps est refusé. Si l'URL n'est pas renseignée, la configuration locale `DB_ENGINE`/`DB_NAME`/`DB_USER`/`DB_PASSWORD`/`DB_HOST`/`DB_PORT` continue de fonctionner comme avant. En production, les garde-fous Django refusent toujours SQLite et les réglages PostgreSQL incomplets.

Render Dashboard (plus tard) : créer une base PostgreSQL distincte de la base locale et de toute future base de production. Choisir le plan gratuit seulement après confirmation qu'il n'entraîne aucun frais, et placer le service web dans la même région. Copier l'**Internal Database URL** de cette base uniquement dans la variable secrète `DATABASE_URL` du Web Service. Ne jamais publier l'URL ou la déposer dans Git.

### Migration contrôlée

Les migrations ne sont pas exécutées automatiquement. Render ne propose la **Pre-Deploy Command** que sur ses services web payants ; le plan gratuit n'a pas non plus de Shell/SSH de service. Pour rester sans dépense :

1. Créer et identifier la base de prévisualisation; vérifier son nom, son hôte et sa région dans le tableau de bord Render.
2. Copier son **External Database URL** dans un environnement local privé temporaire, jamais dans le chat ni dans une commande enregistrée. Fournir aussi localement les mêmes réglages `DJANGO_DEBUG=False`, `DJANGO_SECRET_KEY`, hôtes et origines HTTPS nécessaires aux contrôles Django. `DATABASE_URL` doit remplacer les éventuels `DB_*` locaux.
3. Avant de migrer, confirmer depuis Django que la connexion active aboutit à la base et à l'utilisateur Preview attendus. Comparer le résultat `current_database()` / `current_user` avec les métadonnées Render, et ne jamais afficher l'URL complète ou son mot de passe :

   ```powershell
   python manage.py shell -c "from django.db import connection; c=connection.cursor(); c.execute('select current_database(), current_user, inet_server_addr(), inet_server_port()'); print(c.fetchone())"
   ```

4. Seulement après cette vérification, appliquer une fois `python manage.py migrate` depuis `backend`. Ne lancer aucune migration si l'identité de la base ne correspond pas à la base Preview.
5. Si la connexion extérieure est indisponible, arrêter et faire examiner les options par le responsable Render; ne pas exposer la base locale ni migrer vers une cible non identifiée.

Cette procédure n'a pas été exécutée : aucune base distante n'existe à ce stade.

## Variables Render à configurer

Récupérer les URL Render réellement attribuées au frontend et au backend. Ne pas utiliser le domaine officiel tant qu'il n'est pas confirmé.

| Variable | Valeur à fournir dans le futur service backend |
|---|---|
| `DJANGO_DEBUG` | `False` |
| `DJANGO_SECRET_KEY` | Secret aléatoire généré pour cet environnement dans le tableau de bord Render; différent du secret local |
| `DJANGO_ALLOWED_HOSTS` | Hôte exact du backend, extrait de son URL Render, sans `https://` ni chemin |
| `DJANGO_CORS_ALLOWED_ORIGINS` | Origine exacte HTTPS du frontend Render, sans chemin |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Même origine HTTPS du frontend Render |
| `FRONTEND_URL` | URL HTTPS complète du frontend Render |
| `PUBLIC_SITE_URL` | Origine HTTPS du frontend de prévisualisation; ce n'est pas le domaine officiel |
| `DATABASE_URL` | Internal Database URL de la base de prévisualisation Render, stockée comme secret |
| `DB_CONN_MAX_AGE` | `0` |
| `DJANGO_SEARCH_INDEXING_ENABLED` | `False` |
| `DJANGO_SECURE_SSL_REDIRECT` | `True` (Render termine HTTPS et transmet le protocole proxy) |
| `DJANGO_SECURE_HSTS_SECONDS` | `0` jusqu'à validation ultérieure du domaine et des sous-domaines |
| `DJANGO_EMAIL_BACKEND` | Laisser le backend console par défaut; SMTP n'est pas configuré |

Ne pas renseigner `PUBLIC_SITE_URL` ni `FRONTEND_URL` avec un domaine inventé. Les URL temporaires réelles Render servent à la prévisualisation uniquement. Ne pas configurer `EMAIL_HOST_PASSWORD` ou aucun identifiant dans un fichier versionné.

Dans les réglages Environment du service frontend Render, définir :

```text
VITE_API_BASE_URL=https://<URL-REELLE-DU-BACKEND-RENDER>/api
```

`VITE_API_BASE_URL` est intégrée au bundle public; cette valeur contient uniquement l'URL de l'API, jamais un secret. Après toute modification, reconstruire le site statique. Laisser `VITE_PUBLIC_SITE_URL` vide tant que FORTICO n'a pas confirmé le domaine officiel, ou n'utiliser l'URL de prévisualisation que si l'on veut explicitement des canoniques temporaires.

## Parcours de création ultérieur

1. Avant d'ajouter une ressource, vérifier le forfait Render, le moyen de paiement enregistré et les limites de dépenses du workspace. Ne sélectionner que `Free`, ne pas faire d'upgrade, et arrêter si la configuration peut entraîner des frais non autorisés.
2. Créer une base PostgreSQL Preview gratuite distincte, dans une région choisie pour le service backend, et lire ses limites avant création. Relever `DATABASE_URL` dans Render sans la copier dans Git ou le chat.
3. Créer le Web Service Python depuis le dépôt, branche `main`, Root Directory `backend`, commandes ci-dessus, plan `Free`. Avant de lancer le build, fournir la clé, l'URL DB et les origines exactes. `DJANGO_ALLOWED_HOSTS` doit contenir l'hôte correspondant au nom de service choisi; si Render attribue un hôte différent de celui prévu, corriger la valeur et redéployer. Si les origines ne peuvent pas être déterminées avant le premier build, un échec de configuration est préférable à un démarrage avec `DEBUG=True`.
4. Relever l'URL HTTPS réellement attribuée au backend; l'ajouter à `DJANGO_ALLOWED_HOSTS` (hostname seulement).
5. Relever l'URL HTTPS du frontend Render existant; l'ajouter à CORS, CSRF, `FRONTEND_URL` et `PUBLIC_SITE_URL` du backend.
6. Renseigner `VITE_API_BASE_URL` sur le service frontend avec l'URL backend réelle, reconstruire le frontend puis contrôler navigateur, API, soumission de contact et logs.

## Limites importantes du plan gratuit

- Un Web Service gratuit s'endort après 15 minutes sans requête; le premier appel peut prendre environ une minute à le réveiller.
- Le système de fichiers du Web Service est éphémère; les fichiers téléversés disparaissent au redémarrage/redéploiement. Aucun stockage de médias persistant n'est préparé. Ne pas téléverser de documents métier ou privés pendant cette prévisualisation.
- PostgreSQL Free est limité à 1 Go, une seule base Free active par workspace, et expire après 30 jours; après la période de grâce, Render supprime ses données. Il n'inclut pas de sauvegardes gérées. Exporter les données nécessaires avant expiration, ou accepter explicitement que les données de démo/contact Preview soient jetables.
- Free n'offre ni Shell/SSH, ni jobs ponctuels, ni commande Pre-Deploy. Les migrations contrôlées doivent donc venir d'une machine d'exploitation vers l'URL externe de cette base, après contrôle de cible.
- Render peut facturer le dépassement de bande passante sortante ou de minutes de pipeline si un moyen de paiement est associé. Avant création, vérifier les limites de dépense; sans moyen de paiement, Render indique que les services/builds concernés sont suspendus plutôt que facturés. Surveiller les usages inclus.
- Les services gratuits ne conviennent pas à la production et ne garantissent ni disponibilité, ni conservation durable. La limite DRF repose sur le cache mémoire local; le quota peut être réinitialisé au redémarrage.
- Le service gratuit ne peut pas envoyer de courrier sortant sur les ports SMTP habituels 25, 465 ou 587. Le formulaire pourra enregistrer une demande si la base et les migrations sont opérationnelles, mais aucune notification email réelle ne doit être promise.

## État actuel

La configuration est prête à être publiée après revue. Aucune ressource Render n'a été créée; leur création fera l'objet d'une opération ultérieure distincte. Aucun test n'a été fait contre PostgreSQL distant, aucune migration distante n'a été exécutée, et aucune URL Render backend n'est encore disponible.
