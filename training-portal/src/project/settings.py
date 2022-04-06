import os

from django.core.management.utils import get_random_secret_key

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = os.path.normpath(os.path.join(BASE_DIR, "../data"))

secret_key_file = os.path.join(DATA_DIR, "secret-key.txt")

if os.path.exists(secret_key_file):
    with open(secret_key_file) as fp:
        SECRET_KEY = fp.read().strip()
else:
    SECRET_KEY = get_random_secret_key()
    with open(secret_key_file, "w") as fp:
        fp.write(SECRET_KEY)

DEBUG = os.environ.get("DJANGO_DEBUG", "false").lower() == "true"

ALLOWED_HOSTS = ["*"]


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "crispy_forms",
    "oauth2_provider",
    "corsheaders",
    "mod_wsgi.server",
    "project.apps.workshops",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "oauth2_provider.middleware.OAuth2TokenMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "csp.middleware.CSPMiddleware",
]

ROOT_URLCONF = "project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "project", "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "project.apps.workshops.contexts.portal",
            ],
        },
    },
]

WSGI_APPLICATION = "project.wsgi.application"


# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(DATA_DIR, "db.sqlite3"),
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "static")

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "project", "static"),
]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {"format": "%(levelname)s:%(name)s - %(message)s"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "simple"},
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
        },
    },
}


# User login page.

LOGIN_URL = "login"
LOGOUT_URL = "logout"

LOGIN_REDIRECT_URL = "index"
LOGOUT_REDIRECT_URL = "index"

# Crisp form rendering.

CRISPY_TEMPLATE_PACK = "bootstrap4"

# Assorted configuration for CORS, CSP, OAuth etc.

CORS_ORIGIN_ALLOW_ALL = True

CSP_DEFAULT_SRC = ("'none'",)
CSP_STYLE_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'",)
CSP_IMG_SRC = (
    "'self'",
    "data:",
    "www.google-analytics.com",
    "www.googletagmanager.com",
)
CSP_FONT_SRC = ("'self'",)
CSP_FRAME_SRC = ("'self'",)
CSP_INCLUDE_NONCE_IN = ("script-src",)
CSP_FRAME_ANCESTORS = ("'self'",)

FRAME_ANCESTORS = os.environ.get("FRAME_ANCESTORS", "")

if FRAME_ANCESTORS:
    CSP_FRAME_ANCESTORS = FRAME_ANCESTORS.split(",")
    SESSION_COOKIE_SAMESITE = "None"
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SAMESITE = "None"
    CSRF_COOKIE_SECURE = True

OAUTH2_PROVIDER_APPLICATION_MODEL = "oauth2_provider.Application"

OAUTH2_PROVIDER = {
    "SCOPES": {
        "user:info": "User information",
    },
}

AUTHENTICATION_BACKENDS = [
    "oauth2_provider.backends.OAuth2Backend",
    "django.contrib.auth.backends.ModelBackend",
]

# Settings specific to the training portal.

CONFIG_DIR = os.path.normpath(os.path.join(BASE_DIR, "../config"))

TRAINING_PORTAL = os.environ.get("TRAINING_PORTAL", "")

PORTAL_TITLE = os.environ.get("PORTAL_TITLE") or "Workshops"

PORTAL_LOGO = None

portal_log_path = os.path.join(CONFIG_DIR, "logo")

if os.path.exists(portal_log_path):
    with open(portal_log_path) as fp:
        PORTAL_LOGO = fp.read()

GOOGLE_TRACKING_ID = os.environ.get("GOOGLE_TRACKING_ID")

OPERATOR_API_GROUP = os.environ.get("OPERATOR_API_GROUP", "eduk8s.io")

RESOURCE_STATUS_KEY = os.environ.get("RESOURCE_STATUS_KEY", "eduk8s")
RESOURCE_NAME_PREFIX = os.environ.get("RESOURCE_NAME_PREFIX", "eduk8s")

INGRESS_DOMAIN = os.environ.get("INGRESS_DOMAIN", f"training.{OPERATOR_API_GROUP}")
INGRESS_CLASS = os.environ.get("INGRESS_CLASS", "")
INGRESS_PROTOCOL = os.environ.get("INGRESS_PROTOCOL", "http")
INGRESS_SECRET = os.environ.get("INGRESS_SECRET", "")

PORTAL_NAME = os.environ.get("TRAINING_PORTAL", "")
PORTAL_UID = os.environ.get("PORTAL_UID", "")

PORTAL_HOSTNAME = os.environ.get(
    "PORTAL_HOSTNAME", f"{TRAINING_PORTAL}-ui.{INGRESS_DOMAIN}"
)

PORTAL_PASSWORD = os.environ.get("PORTAL_PASSWORD")
PORTAL_INDEX = os.environ.get("PORTAL_INDEX")

ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "eduk8s")

REGISTRATION_TYPE = os.environ.get("REGISTRATION_TYPE", "one-step")
ENABLE_REGISTRATION = os.environ.get("ENABLE_REGISTRATION", "true")
CATALOG_VISIBILITY = os.environ.get("CATALOG_VISIBILITY", "private")

if REGISTRATION_TYPE == "one-step" and ENABLE_REGISTRATION == "true":
    REGISTRATION_OPEN = True
else:
    REGISTRATION_OPEN = False

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"
