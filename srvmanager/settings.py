import os
import ldap
from django_auth_ldap.config import LDAPSearch, GroupOfNamesType
from datetime import timedelta
from pathlib import Path


def get_bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in ['true', '1']


def get_list_env(name: str, default: list) -> list:
    value = os.getenv(name)
    if value is None:
        return default
    return [item.strip() for item in value.split(',')]


def get_int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or not value.isdigit():
        return default
    return int(value)


BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET')

DEBUG = get_bool_env('DEBUG', False)

ALLOWED_HOSTS = get_list_env('ALLOWED_HOSTS', ['*'])
CORS_ALLOW_ALL_ORIGINS = get_bool_env('CORS_ALLOW_ALL_ORIGINS', False)

AUTHENTICATION_BACKENDS = [
    'django_auth_ldap.backend.LDAPBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# LDAP SETTING
AUTH_LDAP_SERVER_URI = os.getenv('AUTH_LDAP_SERVER_URI')
AUTH_LDAP_BIND_DN = os.getenv('AUTH_LDAP_BIND_DN')
AUTH_LDAP_BIND_PASSWORD = os.getenv('AUTH_LDAP_BIND_PASSWORD')
AUTH_LDAP_USER_SEARCH = LDAPSearch(
    os.getenv('AUTH_LDAP_USER_SEARCH'),
    ldap.SCOPE_SUBTREE,
    '(sAMAccountName=%(user)s)',
)
AUTH_LDAP_GROUP_SEARCH = LDAPSearch(
    os.getenv('AUTH_LDAP_GROUP_SEARCH'),
    ldap.SCOPE_SUBTREE,
    '(objectClass=groupOfNames)',
)
AUTH_LDAP_GROUP_TYPE = GroupOfNamesType()
AUTH_LDAP_USER_ATTR_MAP = {
    'first_name': 'givenName',
    'last_name': 'sn',
    'email': 'mail',
}
AUTH_LDAP_USER_FLAGS_BY_GROUP = {
    "is_active": os.getenv('AUTH_LDAP_USER_IS_ACTIVE'),
    "is_staff": os.getenv('AUTH_LDAP_USER_IS_STAFF'),
    "is_superuser": os.getenv('AUTH_LDAP_USER_IS_SUPERUSER'),
}

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'core',
    'ops',
    'etaupdater',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    )
}

# Simple JWT
ACCESS_TOKEN_LIFETIME = timedelta(
    minutes=get_int_env('ACCESS_TOKEN_LIFETIME', 5))
REFRESH_TOKEN_LIFETIME = timedelta(
    minutes=get_int_env('REFRESH_TOKEN_LIFETIME', 60*24*3))

UPDATE_LAST_LOGIN = True

ROOT_URLCONF = 'srvmanager.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'srvmanager.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'USER': os.getenv('POSTGRES_USER'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD'),
        'HOST': os.getenv('POSTGRES_HOST'),
        'PORT': os.getenv('POSTGRES_PORT', 5432),
        'NAME': os.getenv('POSTGRES_DB'),
    }
}

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

LANGUAGE_CODE = 'ru'

TIME_ZONE = 'Asia/Krasnoyarsk'

USE_I18N = True

USE_TZ = True

STATIC_URL = 'static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CELERY
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL')
CELERY_RESULT_BACKEND = os.getenv('CELERY_BROKER_URL')
CELERY_TIMEZONE = 'Asia/Krasnoyarsk'
CELERY_TASK_ALWAYS_EAGER = get_bool_env('DEBUG', False)
CELERY_TASK_EAGER_PROPAGATES = get_bool_env('DEBUG', False)

# ETAUPDATER
ETALON_DOCKER_IMAGES_COUNT = get_int_env('ETALON_DOCKER_IMAGES_COUNT', 7)
