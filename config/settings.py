# config/settings.py - CLEAN MULTILANG VERSION

"""
Django settings for config project.
"""

from pathlib import Path
import os
from dotenv import load_dotenv
from django.utils.translation import gettext_lazy as _

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Application definition
INSTALLED_APPS = [
    'modeltranslation',

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third party apps
    'corsheaders',
    'phonenumber_field',

    # Local apps
    'apps.core',
    'apps.users',
    'apps.products',
    'apps.categories',
    'apps.brands',
    'apps.orders',
    'apps.reviews',
    'apps.telegram_auth',
    'apps.cart',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',  # ← i18n uchun
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.template.context_processors.i18n',  # ← i18n uchun
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.core.context_processors.site_settings',
                'apps.core.context_processors.header_data',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DATABASE_NAME'),
        'USER': os.getenv('DATABASE_USER'),
        'PASSWORD': os.getenv('DATABASE_PASSWORD'),
        'HOST': os.getenv('DATABASE_HOST'),
        'PORT': os.getenv('DATABASE_PORT'),
    }
}

# Password validation
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

# ========================================
# INTERNATIONALIZATION SETTINGS
# ========================================
LANGUAGE_CODE = 'uz'  # Default
TIME_ZONE = 'Asia/Tashkent'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Languages
LANGUAGES = [
    ('uz', _('O\'zbekcha')),
    ('ru', _('Русский')),
    ('en', _('English')),
]

# Locale files
LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

# ========================================
# MODELTRANSLATION SETTINGS (DB content uchun)
# ========================================
MODELTRANSLATION_LANGUAGES = ('uz', 'ru', 'en')
MODELTRANSLATION_DEFAULT_LANGUAGE = 'uz'
MODELTRANSLATION_FALLBACK_LANGUAGES = ('uz', 'ru', 'en')

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Custom user model
AUTH_USER_MODEL = 'users.User'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS settings
CORS_ALLOWED_ORIGINS = [
    "https://avto.asliddin.me",
    "https://www.avto.asliddin.me",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

# CSRF trusted origins
CSRF_TRUSTED_ORIGINS = [
    "https://avto.asliddin.me",
    "https://www.avto.asliddin.me",
]

# Session settings
SESSION_COOKIE_AGE = 86400  # 1 kun
SESSION_SAVE_EVERY_REQUEST = True

# Phone number field settings
PHONENUMBER_DEFAULT_REGION = 'UZ'
PHONENUMBER_DEFAULT_FORMAT = 'NATIONAL'

# Telegram Bot Settings
BOT_TOKEN = os.getenv('BOT_TOKEN')
BOT_USERNAME = os.getenv('BOT_USERNAME', 'avtokontinent_auth_bot')

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'apps.telegram_auth': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Telegram auth settings
TEMP_CODE_EXPIRY_MINUTES = 1  # 5 xonali kod 1 daqiqa
USER_CODE_EXPIRY_MINUTES = 5  # 4 xonali kod 5 daqiqa

# Login/Logout URLs
LOGIN_URL = '/auth/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_URL = '/users/logout/'
LOGOUT_REDIRECT_URL = '/'

LOGIN_REQUIRED_REDIRECT_URL = '/auth/login/'
