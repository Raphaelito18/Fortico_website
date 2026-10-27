# FORTICO Madagascar

Site vitrine construit avec React, Vite, Django REST Framework et SQLite en développement. PostgreSQL est pris en charge pour les environnements de production. Les textes et coordonnées non fournis par FORTICO restent volontairement signalés comme à compléter.

## Prérequis

- Python 3.12 ou supérieur et `pip`.
- Node.js 20.19 ou supérieur et npm.
- PostgreSQL uniquement si vous choisissez de ne pas utiliser SQLite.

## Démarrer en local

### Backend Django

Dans PowerShell, depuis le dossier du projet :

```powershell
cd backend
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Le backend et l’administration sont disponibles à `http://127.0.0.1:8000/` et `http://127.0.0.1:8000/admin/`. L’API est sous `/api/v1/` et sa documentation sous `/api/docs/`. Le fichier `.env` contient les paramètres locaux et ne doit pas être ajouté à Git. Sans paramètres `DB_NAME` et `DB_PASSWORD`, le backend choisit `backend/db.sqlite3`.

### Frontend React

Dans un second terminal, depuis le dossier du projet :

```powershell
cd frontend
npm ci
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
npm run dev
```

Le site est disponible à `http://localhost:5173/`. Vite transmet `/api` et `/media` au backend local `http://127.0.0.1:8000`. Si Django tourne ailleurs, indiquez son adresse dans `VITE_DEV_API_TARGET` dans `frontend/.env`.

## Administration et contenu

Après avoir créé un compte administrateur avec `python manage.py createsuperuser`, connectez-vous à `/admin/`. Le compte Django administrateur peut gérer la fiche entreprise, les expertises, les réalisations, les certificats, les actualités, les images et les messages reçus. Les contenus publiés sont consultables publiquement ; les modifications via l’API nécessitent un utilisateur autorisé. Les brouillons restent visibles uniquement pour les administrateurs connectés.

Endpoints publics principaux :

- `GET /api/v1/company/`
- `GET /api/v1/expertises/`
- `GET /api/v1/projects/`
- `GET /api/v1/certificates/`
- `GET /api/v1/articles/`
- `POST /api/v1/contact/`

Les demandes de contact sont limitées à cinq par heure et par adresse IP. Elles sont consultables dans l’administration Django. Pour recevoir les notifications par e-mail, configurez les paramètres SMTP et `CONTACT_NOTIFICATION_EMAIL` dans `backend/.env`.

## Vérifications

```powershell
cd backend
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
cd ..\frontend
npm run lint
npm run build
```

## Base de données et sauvegardes

En développement avec SQLite, arrêtez le serveur et copiez `backend/db.sqlite3` dans un emplacement de sauvegarde protégé. Sauvegardez également `backend/media/`, qui contient les images et documents téléversés. Ne placez ni la base ni les secrets dans Git.

En production PostgreSQL, configurez `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST` et `DB_PORT` dans l’environnement. Sauvegardez les données avec `pg_dump` selon la politique de l’hébergeur et sauvegardez séparément le stockage des médias. Testez régulièrement la restauration. Appliquez les migrations avec `python manage.py migrate` lors du déploiement.

## Préparation au déploiement

Configurez `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=False`, `DJANGO_ALLOWED_HOSTS`, les origines CORS, PostgreSQL, HTTPS et le serveur SMTP. Définissez `VITE_API_BASE_URL` dans `frontend/.env` pour l’URL de l’API publique, puis générez le site avec `npm run build`. Servez `frontend/dist/` avec l’hébergement choisi et configurez les chemins de médias. Les variables `VITE_*` sont publiques : n’y stockez aucun secret.

Les informations officielles, le logo et les photos de FORTICO doivent être ajoutés par une personne habilitée dans l’administration avant la mise en ligne publique.
