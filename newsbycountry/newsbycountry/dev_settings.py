from pathlib import Path
import os
from celery.schedules import crontab, schedule

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-w=lmfw+4$5f=o5xfbckk#ap4gmov1btpu-3u00dx6db(^s(olf'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["10.0.0.14", "localhost"]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'rest_framework',
    'django_minio_backend',
    'django_celery_beat',
    'django_celery_results',

    'apps.people',
    'apps.foreign_policy',
    'apps.geography',
    'apps.references'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'newsbycountry.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, "templates")],
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

WSGI_APPLICATION = 'newsbycountry.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get("POSTGRES_DB"),
        'USER': os.environ.get("POSTGRES_USER"),
        'PASSWORD': os.environ.get("POSTGRES_PASSWORD"),
        'HOST': 'dev-psql',
        'PORT': 5432
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

# STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

MEDIA_URL = '/media/'
MINIO_MEDIA_FILES_BUCKET = "test-django"

# MINIO Storage configuration:
MINIO_CONSISTENCY_CHECK_ON_START = True
DEFAULT_FILE_STORAGE = 'django_minio_backend.models.MinioBackend'

STATICFILES_STORAGE = 'django_minio_backend.models.MinioBackendStatic'

MINIO_ACCESS_KEY = os.environ.get("MINIO_ACCESS_KEY_ID")
MINIO_SECRET_KEY = os.environ.get("MINIO_SECRET_ACCESS_KEY")
MINIO_ENDPOINT = "dev-minio-service:9000"
MINIO_USE_HTTPS = False
MINIO_EXTERNAL_ENDPOINT = "localhost:9000"
MINIO_EXTERNAL_ENDPOINT_USE_HTTPS = False

MINIO_PUBLIC_BUCKETS = [
    'test-django',
]
#MINIO_STATIC_FILES_BUCKET = 'test-django'
MINIO_MEDIA_FILES_BUCKET = 'test-django'

STATIC_URL = "/static/"
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static")
]

# Celery Config:
CELERY_BROKER_URL= os.environ.get("CELERY_BROKER")
CELERY_RESULT_BACKEND = 'django-db'
CELERY_CACHE_BACKEND = 'django-cache'

CELERY_BEAT_SCHEDULE = {
    "ingest_foreign_policy_rss_feed": {
        "task": "apps.foreign_policy.models.load_foreign_policy_rss_feed",
        "schedule": crontab(hour=8, minute=0)
    }
}