"""Configuration Django — API REST multi-tenant (DRF)."""
from pathlib import Path

from decouple import Csv, config
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

DEBUG = config("DEBUG", default=False, cast=bool)

SECRET_KEY = config("SECRET_KEY", default="")
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "dev-only-insecure-key-do-not-use-in-production"
    else:
        raise ImproperlyConfigured(
            "SECRET_KEY manquant : copiez .env.example vers .env (setup.sh/setup.bat le font pour vous)."
        )

ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost,127.0.0.1", cast=Csv())

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "corsheaders",
    "rest_framework",
    "core",
    "tenants",
    "accounts",
    "billing",
    "business",
    "projects",
    "timetracking",
    "notifications",
]

# API pure (jeton Bearer, aucun cookie) : pas de sessions, de CSRF ni de messages.
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": []},
    }
]

AUTH_USER_MODEL = "accounts.User"
AUTH_PASSWORD_VALIDATORS = []  # longueur minimale (8) imposée par les serializers

# --- Base de données ---------------------------------------------------------
_engine = config("DB_ENGINE", default="sqlite")
if _engine == "sqlite":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / config("DB_NAME", default="db.sqlite3"),
        }
    }
elif _engine in ("postgresql", "mysql"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql" if _engine == "postgresql" else "django.db.backends.mysql",
            "NAME": config("DB_NAME", default="saas_enterprise"),
            "USER": config("DB_USER", default=""),
            "PASSWORD": config("DB_PASSWORD", default=""),
            "HOST": config("DB_HOST", default="127.0.0.1"),
            "PORT": config("DB_PORT", default="5432" if _engine == "postgresql" else "3306"),
        }
    }
else:
    raise ImproperlyConfigured("DB_ENGINE doit valoir sqlite, postgresql ou mysql.")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Internationalisation ----------------------------------------------------
LANGUAGE_CODE = "fr"
TIME_ZONE = "UTC"  # le contrat d'API exige des datetimes ISO 8601 en UTC
USE_I18N = True
USE_TZ = True

# Les URLs de l'API n'ont pas de slash final (contrat avec le frontend).
APPEND_SLASH = False

# --- CORS / frontend ---------------------------------------------------------
FRONTEND_URL = config("FRONTEND_URL", default="http://localhost:5173")
CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS",
    default="http://localhost:5173,http://127.0.0.1:5173",
    cast=Csv(),
)

# --- Jetons d'authentification ----------------------------------------------
TOKEN_LIFETIME_DAYS = config("TOKEN_LIFETIME_DAYS", default=7, cast=int)

# --- Django REST Framework ---------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["core.authentication.BearerTokenAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser"],
    "DEFAULT_PAGINATION_CLASS": None,  # listes = tableaux JSON simples
    "DEFAULT_THROTTLE_RATES": {"public_auth": "10/min"},  # anti brute-force
    "EXCEPTION_HANDLER": "core.exceptions.api_exception_handler",
    "COERCE_DECIMAL_TO_STRING": False,  # prix, salaires... renvoyés comme nombres JSON
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
}
