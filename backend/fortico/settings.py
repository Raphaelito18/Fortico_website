"""
Réglages Django du projet FORTICO Madagascar.

Toute la configuration sensible est lue dans les variables d'environnement
(fichier « backend/.env »), afin qu'aucun secret ne soit stocké dans Git.

Deux bases de données sont supportées automatiquement :
  - PostgreSQL (production, et développement si les variables DB_* sont
    renseignées) ;
  - SQLite (repli pour le développement local, sans configuration).
"""

import os
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import load_dotenv

# --------------------------------------------------------------------------
# Chemins
# --------------------------------------------------------------------------
# BASE_DIR = dossier « backend » (contient manage.py)
BASE_DIR = Path(__file__).resolve().parent.parent

# Charge le fichier .env s'il existe (les variables déjà présentes dans
# l'environnement du système ont la priorité).
load_dotenv(BASE_DIR / '.env')


# --------------------------------------------------------------------------
# Helpers de lecture des variables d'environnement
# --------------------------------------------------------------------------
def env_str(name: str, default: str = '') -> str:
    """Retourne une variable d'environnement sous forme de texte."""
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip()


def env_bool(name: str, default: bool = False) -> bool:
    """Retourne une variable d'environnement sous forme de booléen."""
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {'1', 'true', 'yes', 'on', 'oui'}


def env_list(name: str, default: str = '') -> list[str]:
    """Retourne une variable d'environnement sous forme de liste separated by commas."""
    value = os.environ.get(name, default)
    return [item.strip() for item in value.split(',') if item.strip()]


def env_int(name: str, default: int) -> int:
    """Retourne une variable d'environnement sous forme d'entier."""
    value = os.environ.get(name)
    if value is None or not value.strip():
        return default
    try:
        return int(value)
    except ValueError:
        return default


# --------------------------------------------------------------------------
# Sécurité
# --------------------------------------------------------------------------
SECRET_KEY = env_str('DJANGO_SECRET_KEY', 'django-insecure-change-me-in-production')

DEBUG = env_bool('DJANGO_DEBUG', True)

ALLOWED_HOSTS = env_list('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1')
PUBLIC_SITE_URL = env_str('PUBLIC_SITE_URL').rstrip('/')
SEARCH_INDEXING_ENABLED = env_bool('DJANGO_SEARCH_INDEXING_ENABLED', False)

# En production, on refuse d'héberger le site si la clé secrète n'a pas été
# modifiée : cela évite une mise en production avec la clé de démonstration.
if not DEBUG and SECRET_KEY.startswith('django-insecure-'):
    raise RuntimeError(
        "DJANGO_SECRET_KEY doit être défini dans le fichier .env avant la mise "
        "en production (voir .env.example)."
    )


# --------------------------------------------------------------------------
# Applications
# --------------------------------------------------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Applications du projet
    'apps.core',
    'apps.content',
    # Librairies tierces
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'drf_spectacular',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # WhiteNoise sert les fichiers statiques (CSS/JS) sans dépendance à un
    # serveur de fichiers statiques supplémentaire.
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'fortico.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'fortico.wsgi.application'
ASGI_APPLICATION = 'fortico.asgi.application'


# --------------------------------------------------------------------------
# Base de données
# --------------------------------------------------------------------------
DB_NAME = env_str('DB_NAME')
DB_USER = env_str('DB_USER')
DB_PASSWORD = env_str('DB_PASSWORD')
DB_HOST = env_str('DB_HOST', 'localhost')
DB_PORT = env_str('DB_PORT', '5432')
DB_CONN_MAX_AGE = env_int('DB_CONN_MAX_AGE', 0)
if DB_CONN_MAX_AGE < 0:
    raise RuntimeError('DB_CONN_MAX_AGE doit \u00eatre un entier sup\u00e9rieur ou \u00e9gal \u00e0 z\u00e9ro.')

DB_ENGINE = env_str('DB_ENGINE').lower()
if not DB_ENGINE:
    # CompatibilitÃ© avec la configuration historique : DB_* remplis implique PostgreSQL.
    DB_ENGINE = 'postgresql' if any((DB_NAME, DB_USER, DB_PASSWORD)) else 'sqlite'

if DB_ENGINE in {'postgres', 'postgresql'}:
    missing_db_values = [
        name for name, value in (
            ('DB_NAME', DB_NAME),
            ('DB_USER', DB_USER),
            ('DB_PASSWORD', DB_PASSWORD),
        ) if not value
    ]
    if missing_db_values:
        raise RuntimeError(
            'Configuration PostgreSQL incomplÃ¨te : renseignez '
            + ', '.join(missing_db_values)
            + ' dans backend/.env.'
        )
    # PostgreSQL (production, ou développement configuré).
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': DB_NAME,
            'USER': DB_USER,
            'PASSWORD': DB_PASSWORD,
            'HOST': DB_HOST,
            'PORT': DB_PORT,
            # Le serveur de d\u00e9veloppement peut cr\u00e9er plusieurs connexions
            # persistantes par thread. Garder 0 par d\u00e9faut \u00e9vite de saturer
            # PostgreSQL ; un pool born\u00e9 peut \u00eatre activ\u00e9 explicitement
            # selon le nombre de workers et la limite de connexions du serveur.
            'CONN_MAX_AGE': DB_CONN_MAX_AGE,
            'CONN_HEALTH_CHECKS': True,
        }
    }
elif DB_ENGINE == 'sqlite':
    # Repli SQLite : pratique pour démarrer sans installer PostgreSQL.
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    raise RuntimeError('DB_ENGINE doit valoir "postgresql" ou "sqlite".')


# --------------------------------------------------------------------------
# Authentification
# --------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Durée de vie d'un jeton d'API (TokenAuthentication) en minutes.
TOKEN_LIFETIME_MINUTES = env_int('API_TOKEN_LIFETIME', 480)


# --------------------------------------------------------------------------
# Internationalisation
# --------------------------------------------------------------------------
LANGUAGE_CODE = 'fr-fr'

TIME_ZONE = 'Indian/Antananarivo'  # Madagascar (UTC+3)

USE_I18N = True

USE_TZ = True

LANGUAGES = [
    ('fr', 'Français'),
    ('en', 'English'),
]


# --------------------------------------------------------------------------
# Fichiers statiques et fichiers envoyés par les utilisateurs
# --------------------------------------------------------------------------
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = []

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
# Les certificats peuvent contenir des informations non publiées. Ce dossier
# ne doit pas être exposé par un serveur de fichiers statiques.
PRIVATE_MEDIA_ROOT = BASE_DIR / 'private_media'

STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

# Taille maximale d'un fichier envoyé (5 Mo) et formats autorisés.
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
MAX_UPLOAD_SIZE_MB = 5


# --------------------------------------------------------------------------
# Django REST Framework
# --------------------------------------------------------------------------
DRF_NUM_PROXIES = env_int('DRF_NUM_PROXIES', 0)
if DRF_NUM_PROXIES < 0:
    raise RuntimeError('DRF_NUM_PROXIES doit \u00eatre un entier sup\u00e9rieur ou \u00e9gal \u00e0 z\u00e9ro.')

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 12,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    # Ne faire confiance à X-Forwarded-For qu'après avoir configuré le
    # nombre de proxys de confiance qui nettoient/complètent cet en-tête.
    'NUM_PROXIES': DRF_NUM_PROXIES,
    # Limitation du nombre de requêtes : protège l'API des abus.
    'DEFAULT_THROTTLE_RATES': {
        'anon': '60/hour',
        'user': '600/hour',
        'contact': '5/hour',
    },
    'DATETIME_FORMAT': '%d/%m/%Y à %H:%M',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'API FORTICO Madagascar',
    'DESCRIPTION': (
        "API REST du site professionnel FORTICO Madagascar. "
        "Expose les contenus publics (entreprise, expertises, réalisations, "
        "certificats, actualités) et la réception des demandes de contact."
    ),
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
}


# --------------------------------------------------------------------------
# CORS — accès à l'API depuis le frontend React
# --------------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = env_list(
    'DJANGO_CORS_ALLOWED_ORIGINS',
    'http://localhost:5173,http://127.0.0.1:5173',
)
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = env_list(
    'DJANGO_CSRF_TRUSTED_ORIGINS',
    ','.join(CORS_ALLOWED_ORIGINS),
)


# --------------------------------------------------------------------------
# Sessions et cookies
# --------------------------------------------------------------------------
SESSION_COOKIE_AGE = env_int('SESSION_COOKIE_AGE', 60 * 60 * 24 * 14)
SESSION_COOKIE_SECURE = env_bool('SESSION_COOKIE_SECURE', False)
CSRF_COOKIE_SECURE = env_bool('CSRF_COOKIE_SECURE', False)
X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'same-origin'

# OPTIONS pour une page d'administration Django (connexion).
LOGIN_URL = '/admin/login/'
LOGIN_REDIRECT_URL = '/admin/'
LOGOUT_REDIRECT_URL = '/'


# --------------------------------------------------------------------------
# Sécurité en production (HTTPS)
# --------------------------------------------------------------------------
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = env_bool('DJANGO_SECURE_SSL_REDIRECT', True)
    # HSTS est activ\u00e9 apr\u00e8s validation du domaine et de tous ses
    # sous-domaines. Ne pas pr\u00e9charger un domaine avant accord explicite.
    SECURE_HSTS_SECONDS = env_int('DJANGO_SECURE_HSTS_SECONDS', 0)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool(
        'DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS', False,
    )
    SECURE_HSTS_PRELOAD = env_bool('DJANGO_SECURE_HSTS_PRELOAD', False)
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


# --------------------------------------------------------------------------
# Envoi d'e-mails (formulaire de contact)
# --------------------------------------------------------------------------
# En développement, les e-mails sont écrits dans la console du serveur.
# En production, renseignez un vrai serveur SMTP dans le .env.
EMAIL_BACKEND = env_str(
    'DJANGO_EMAIL_BACKEND',
    'django.core.mail.backends.console.EmailBackend',
)
EMAIL_HOST = env_str('EMAIL_HOST', '')
EMAIL_PORT = env_int('EMAIL_PORT', 587)
EMAIL_HOST_USER = env_str('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = env_str('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = env_bool('EMAIL_USE_TLS', True)
EMAIL_USE_SSL = env_bool('EMAIL_USE_SSL', False)
if EMAIL_USE_TLS and EMAIL_USE_SSL:
    raise RuntimeError('EMAIL_USE_TLS et EMAIL_USE_SSL ne peuvent pas \u00eatre activ\u00e9s ensemble.')
DEFAULT_FROM_EMAIL = env_str('DEFAULT_FROM_EMAIL', 'no-reply@fortico.local')

# Adresse de l'expéditeur des notifications « nouveau message de contact ».
CONTACT_NOTIFICATION_EMAIL = env_str('CONTACT_NOTIFICATION_EMAIL', '')
# URL publique du frontend (utilisée dans les liens des e-mails).
FRONTEND_URL = env_str('FRONTEND_URL', 'http://localhost:5173')


# --------------------------------------------------------------------------
# Divers
# --------------------------------------------------------------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Nombre de messages affichés par page dans l'administration Django.
ADMIN_PAGINATE_BY = 25

# Identifiant du site (utilisé par l'admin et les cookies).
SITE_ID = 1


# --------------------------------------------------------------------------
# Garde-fous de production et journalisation
# --------------------------------------------------------------------------
def is_confirmed_https_origin(value: str) -> bool:
    parsed = urlsplit(value)
    return (
        parsed.scheme == 'https'
        and bool(parsed.netloc)
        and parsed.path in {'', '/'}
        and not parsed.query
        and not parsed.fragment
        and not parsed.username
        and not parsed.password
        and parsed.hostname not in {'localhost', '127.0.0.1', '::1'}
    )


if not DEBUG:
    if not ALLOWED_HOSTS or any(host in {'localhost', '127.0.0.1', '*'} for host in ALLOWED_HOSTS):
        raise RuntimeError('DJANGO_ALLOWED_HOSTS doit contenir uniquement les h\u00f4tes confirm\u00e9s en production.')
    if DATABASES['default']['ENGINE'] != 'django.db.backends.postgresql':
        raise RuntimeError('La production FORTICO doit utiliser PostgreSQL (DB_ENGINE=postgresql).')
    if any(not is_confirmed_https_origin(origin) for origin in CORS_ALLOWED_ORIGINS):
        raise RuntimeError('Les origines CORS de production doivent \u00eatre des origines HTTPS confirm\u00e9es.')
    if any(not is_confirmed_https_origin(origin) for origin in CSRF_TRUSTED_ORIGINS):
        raise RuntimeError('Les origines CSRF de production doivent \u00eatre des origines HTTPS confirm\u00e9es.')
    public_site = urlsplit(PUBLIC_SITE_URL)
    if (
        public_site.scheme != 'https' or not public_site.netloc
        or public_site.path not in {'', '/'} or public_site.query or public_site.fragment
        or public_site.username or public_site.password
        or public_site.hostname in {'localhost', '127.0.0.1', '::1'}
    ):
        raise RuntimeError('PUBLIC_SITE_URL doit être l’origine HTTPS confirmée du site public.')
    frontend_site = urlsplit(FRONTEND_URL)
    if (
        frontend_site.scheme != 'https' or not frontend_site.netloc
        or frontend_site.path not in {'', '/'} or frontend_site.query or frontend_site.fragment
        or frontend_site.username or frontend_site.password
        or frontend_site.hostname in {'localhost', '127.0.0.1', '::1'}
    ):
        raise RuntimeError('FRONTEND_URL doit être une URL HTTPS confirmée en production.')

LOG_LEVEL = env_str('DJANGO_LOG_LEVEL', 'INFO').upper()
if LOG_LEVEL not in {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}:
    LOG_LEVEL = 'INFO'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '{asctime} {levelname} {name}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
        },
    },
    'root': {'handlers': ['console'], 'level': LOG_LEVEL},
    'loggers': {
        'django.request': {'handlers': ['console'], 'level': 'WARNING', 'propagate': False},
    },
}
