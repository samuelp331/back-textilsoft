import os
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-secret-key-change-me")
DEBUG = os.getenv("DJANGO_DEBUG", "True").lower() == "true"
ALLOWED_HOSTS = [host.strip() for host in os.getenv("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")]


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework.authtoken",
    "accounts",
    "profiles",
    "inventory",
    "suppliers",
    "reports",
    "alerts",
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    "config.cors.SimpleCORSMiddleware",
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = "config.wsgi.application"


# Database

DATABASES = {
    "default": dj_database_url.config(
        default=os.getenv("DATABASE_URL"),
        conn_max_age=600,
    )
}

# Supabase: en el panel → Project Settings → Database, copia la URI (PostgreSQL).
# - Conexión directa o Session pooler (puerto 5432): suele bastar DB_CONN_MAX_AGE=600.
# - Transaction pooler / PgBouncer (puerto 6543): pon DB_TRANSACTION_POOLER=True y,
#   si ves errores de cursor o conexiones, DB_CONN_MAX_AGE=0.
# DATABASE_URL = os.getenv("DATABASE_URL", "").strip().strip('"').strip("'")
# USE_SQLITE = os.getenv("USE_SQLITE", "True").lower() == "true"
# DB_CONN_MAX_AGE = int(os.getenv("DB_CONN_MAX_AGE", "600"))
# DB_SSL_REQUIRE = os.getenv("DB_SSL_REQUIRE", "True").lower() == "true"
# DB_TRANSACTION_POOLER = os.getenv("DB_TRANSACTION_POOLER", "False").lower() == "true"

# if DATABASE_URL:
#     DATABASES = {
#         "default": dj_database_url.parse(
#             DATABASE_URL,
#             conn_max_age=DB_CONN_MAX_AGE,
#             ssl_require=DB_SSL_REQUIRE,
#         )
#     }
#     if DB_TRANSACTION_POOLER:
#         DATABASES["default"]["DISABLE_SERVER_SIDE_CURSORS"] = True
# elif USE_SQLITE:
#     DATABASES = {
#         "default": {
#             "ENGINE": "django.db.backends.sqlite3",
#             "NAME": BASE_DIR / "db.sqlite3",
#         }
#     }
# else:
#     DATABASES = {
#         "default": {
#             "ENGINE": os.getenv("DB_ENGINE", "django.db.backends.postgresql"),
#             "NAME": os.getenv("DB_NAME", "postgres"),
#             "USER": os.getenv("DB_USER", "postgres"),
#             "PASSWORD": os.getenv("DB_PASSWORD", ""),
#             "HOST": os.getenv("DB_HOST", "localhost"),
#             "PORT": os.getenv("DB_PORT", "5432"),
#         }
#     }


# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = "es-co"

TIME_ZONE = "America/Bogota"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "accounts.Usuario"

# El registro público (POST /api/register) está deshabilitado en la vista; altas vía /api/admin/usuarios/.
# Si en el futuro se reactiva el endpoint, estos son los roles permitidos en RegisterSerializer (separados por comas).
REGISTRATION_ASSIGNABLE_ROLES = tuple(
    x.strip()
    for x in os.getenv(
        "REGISTRATION_ASSIGNABLE_ROLES",
        "operario,bodeguero,supervisor,administrador",
    ).split(",")
    if x.strip()
)

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
}

# Correo y recuperación de contraseña (ver variables en .env)
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "TextilSoft <noreply@localhost>")
EMAIL_BACKEND = os.getenv(
    "EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend",
)
EMAIL_HOST = os.getenv("EMAIL_HOST") or ""
if EMAIL_HOST.strip():
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True").lower() == "true"
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER") or ""
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD") or ""
# Base del front donde abre index.html con ?page=resetPassword...
PASSWORD_RESET_FRONTEND_URL = os.getenv(
    "PASSWORD_RESET_FRONTEND_URL",
    "http://127.0.0.1:5173",
).strip().rstrip("/")

