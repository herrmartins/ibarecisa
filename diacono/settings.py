import os
from pathlib import Path
from decouple import config
import mimetypes
import sys
import sentry_sdk

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


SECRET_KEY = config("SECRET_KEY")

DEBUG = config("DEBUG", cast=bool)

if not DEBUG:
    ALLOWED_HOSTS = ["ibarecisa.org.br", "diacono.ibarecisa.org.br",
                     "104.251.208.79", "104.237.2.251", "https://104.237.2.251",
                     'mail.ibarecisa.org.br']
else:
    ALLOWED_HOSTS = ["*"]


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "phonenumber_field",
    "ckeditor",
    "rest_framework",
    "xhtml2pdf",
    "weasyprint",
    "captcha",
    "corsheaders",
    "reversion",
    "reversion_compare",
    "storages",
    "blog.apps.BlogConfig",
    "events.apps.EventsConfig",
    "core.apps.CoreConfig",
    "users.apps.UsersConfig",
    "secretarial.apps.SecretarialConfig",
    "treasury.apps.TreasuryConfig",
    "worship.apps.WorshipConfig",
    "api2",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "reversion.middleware.RevisionMiddleware",
    "core.middleware.ApprovalMiddleware",
    "treasury.middleware.AccountingPeriodMiddleware",
]

ROOT_URLCONF = "diacono.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.core_context_processor.context_user_data",
                "django.contrib.auth.context_processors.auth",
            ],
        },
    },
]

WSGI_APPLICATION = "diacono.wsgi.application"

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    },
    "audit": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "audit.sqlite3",
    }
}

# Router para direcionar models de auditoria para banco separado
DATABASE_ROUTERS = [
    "treasury.routers.AuditRouter",
]


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = "pt-br"

TIME_ZONE = "America/Sao_Paulo"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/


if not DEBUG:
    STATIC_ROOT = BASE_DIR / "staticfiles"
    STATICFILES_DIRS = [
        BASE_DIR / "static",
        BASE_DIR / "blog" / "static",
    ]
else:
    STATICFILES_DIRS = [
        BASE_DIR / "static",
        BASE_DIR / "blog" / "static",
    ]

STATIC_URL = "/static/"

MEDIA_ROOT = BASE_DIR / "media"
MEDIA_URL = "/media/"

# Storage Configuration
# Desenvolvimento: armazenamento local
# Produção: S3 compatível (Cloudflare R2, Backblaze B2, etc.)
if not DEBUG:
    # Configurações S3
    AWS_ACCESS_KEY_ID = config("AWS_ACCESS_KEY_ID", default="")
    AWS_SECRET_ACCESS_KEY = config("AWS_SECRET_ACCESS_KEY", default="")
    AWS_STORAGE_BUCKET_NAME = config("AWS_STORAGE_BUCKET_NAME", default="")
    AWS_S3_ENDPOINT_URL = config("AWS_S3_ENDPOINT_URL", default="")
    AWS_S3_REGION_NAME = config("AWS_S3_REGION_NAME", default="auto")
    AWS_QUERYSTRING_AUTH = False
    AWS_DEFAULT_ACL = None
    AWS_S3_FILE_OVERWRITE = False
    # URL customizada para arquivos (útil para domínio customizado no R2)
    AWS_S3_CUSTOM_DOMAIN = config("AWS_S3_CUSTOM_DOMAIN", default="")

    # STORAGES (Django 4.2+)
    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }
else:
    # Desenvolvimento: armazenamento local
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "users.CustomUser"
LOGOUT_REDIRECT_URL = "core:home"
LOGIN_REDIRECT_URL = "core:home"

CKEDITOR_CONFIGS = {
    "default": {
        "skin": "moono",
        "toolbar": "basic",
        "height": "full",
        "width": "full",
        "removePlugins": "exportpdf",
        "toolbarCanCollapse": "true",
    },
}

# TinyMCE Configuration
TINYMCE_JS_URL = 'https://cdn.tiny.cloud/1/no-api-key/tinymce/8/tinymce.min.js'
TINYMCE_COMPRESSOR = False
TINYMCE_API_KEY = config('TINYMCE_API_KEY', default='')


mimetypes.add_type("image/jpeg", ".jpg", strict=True)
mimetypes.add_type("image/jpeg", ".jpeg", strict=True)
mimetypes.init()


LANGUAGE_CODE = "pt-br"
USE_I18N = True
USE_L10N = True

EMAIL_BACKEND = config("EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = config("EMAIL_HOST")
EMAIL_HOST_USER = config("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD")
EMAIL_PORT = config("EMAIL_PORT")
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="Rafael Martins <naoresponda@ibarecisa.org.br>")


handler404 = "core.views.custom_404"
handler403 = "core.views.custom_403"


if not DEBUG:
    # HTTPS Settings
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True

    # HSTS Settings
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_PRELOAD = True
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True

if DEBUG:
    CORS_ALLOWED_ORIGINS = [
        "http://127.0.0.1:8000",
    ]
else:
    CORS_ALLOWED_ORIGINS = [
        "https://ibarecisa.org.br",
        "https://diacono.ibarecisa.org.br",
        "https://104.237.2.251",
    ]
customColorPalette = [
    {
        'color': 'hsl(4, 90%, 58%)',
        'label': 'Red'
    },
    {
        'color': 'hsl(340, 82%, 52%)',
        'label': 'Pink'
    },
    {
        'color': 'hsl(291, 64%, 42%)',
        'label': 'Purple'
    },
    {
        'color': 'hsl(262, 52%, 47%)',
        'label': 'Deep Purple'
    },
    {
        'color': 'hsl(231, 48%, 48%)',
        'label': 'Indigo'
    },
    {
        'color': 'hsl(207, 90%, 54%)',
        'label': 'Blue'
    },
]

CAPTCHA_IMAGE_SIZE = (250, 100)
CAPTCHA_FONT_SIZE = 40
CAPTCHA_TEST_MODE = True

MISTRAL_API_KEY = config("MISTRAL_API_KEY", default="")
USE_MISTRAL_OCR = config("USE_MISTRAL_OCR", default=False)  # False=Ollama em dev, True=Mistral sempre
MISTRAL_MODEL = config("MISTRAL_MODEL", default="mistral-small-latest")

# Ollama Configuration (desenvolvimento)
OLLAMA_HOST = config("OLLAMA_HOST", default="http://localhost:11434")
OLLAMA_OCR_MODEL = config("OLLAMA_OCR_MODEL", default="qwen3-vl:4b")
OLLAMA_TEXT_MODEL = config("OLLAMA_TEXT_MODEL", default="gemma3n:e4b")

if not DEBUG:
    sentry_sdk.init(
        dsn="https://56e7c96aedf9c170eeb59c9b515f6ef4@o4509815595597824.ingest.us.sentry.io/4509815598678016",
        # Add data like request headers and IP for users,
        # see https://docs.sentry.io/platforms/python/data-management/data-collected/ for more info
        send_default_pii=True,
    )


# Django REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
}
