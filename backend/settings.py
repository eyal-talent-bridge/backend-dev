"""
Django settings for backend project.

Generated by 'django-admin startproject' using Django 4.2.7.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

from pathlib import Path
from datetime import timedelta
import os,logging
from dotenv import load_dotenv
load_dotenv()
# Build pathps inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))



# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'fallback_default_secret')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = ['users.up.railway.app', '127.0.0.1', 'localhost']

users_logger = logging.getLogger('users')

# Application definition

INSTALLED_APPS = [
    'admin_interface',
    'colorfield',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'users',
    'rest_framework_simplejwt',
    # 'rest_framework_simplejwt.token_blacklist',
    'drf_yasg',
    'channels',
    'corsheaders',
    
]

X_FRAME_OPTIONS = "SAMEORIGIN"
SILENCED_SYSTEM_CHECKS = ["security.W019"]



MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'corsheaders.middleware.CorsMiddleware',

]


ROOT_URLCONF = 'backend.urls'

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

WSGI_APPLICATION = 'backend.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    # 'default': {
    #     'ENGINE': 'django.db.backends.sqlite3',
    #     'NAME': BASE_DIR / 'db.sqlite3',
    # }

    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Jerusalem'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')


# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'



REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}



SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    # 'BLACKLIST_AFTER_ROTATION': True,
    'SIGNING_KEY': os.getenv('JWT_SECRET_KEY', SECRET_KEY),
    'ALGORITHM': 'HS256',
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
}

AUTH_USER_MODEL = 'users.CustomUser'
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/' 




LOG_DIR = os.path.join(BASE_DIR, 'logs')

# Ensure the directory exists
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simpleRe': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        }
    },
    'handlers': {
        'users_file': {
            'level': 'DEBUG' if DEBUG else 'INFO',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'users.log'),
            'formatter': 'simpleRe',
            'when': 'midnight',
            'backupCount': 7,
        },

        'console': {
            'level': 'DEBUG' if DEBUG else 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simpleRe',
        },
    },
    'loggers': {
        'users': {
            'handlers': ['users_file', 'console'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': True,
        },
}
}



MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

NOTIFICATION_SERVICE_URL = os.environ.setdefault('NOTIFICATION_SERVICE_URL', 'http://localhost:8070/api/v1/notifications/')

CSRF_TRUSTED_ORIGINS = [
    "https://users.up.railway.app",
    "http://localhost:8000",
    "https://localhost:8000",
    'https://talent-bridge.up.railway.app',
]

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173", 
    "https://talent-bridge.up.railway.app", 
    "https://users.up.railway.app",  
]
CORS_ALLOW_CREDENTIALS = True
users_logger.info("Django settings loaded successfully")

# # Add to INSTALLED_APPS
# INSTALLED_APPS = [
#     # ... other apps
#     'storages',
# ]

# # S3 Configuration
# AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
# AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
# AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
# AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME', 'us-east-1')

# # Optional: Configure S3 URL
# AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'

# # Static Files
# STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/static/'
# STATICFILES_STORAGE = 'storages.backends.s3boto3.S3StaticStorage'

# # Media Files
# DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
# MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'