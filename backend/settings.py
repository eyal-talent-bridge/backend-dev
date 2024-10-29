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
import os
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-m=&^=4vc0tsypar4p&vt_zp0szq1kb9hq-46_*yrcn5uq)c&*c'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


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
    'rest_framework_simplejwt.token_blacklist',
    'drf_yasg',
    'channels',
    'social_django',
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
    'social_django.middleware.SocialAuthExceptionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
]

CORS_ALLOWED_ORIGINS = [
   "http://localhost:5173",
   
]

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

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
                'social_django.context_processors.backends',
                'social_django.context_processors.login_redirect',
            ],
        },
    },
]

WSGI_APPLICATION = 'backend.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
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

STATIC_URL = 'static/'

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
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
}

AUTH_USER_MODEL = 'users.CustomUser'

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

AUTHENTICATION_BACKENDS = [
    # 'social_core.backends.facebook.FacebookOAuth2',
    # 'social_core.backends.google.GoogleOAuth2',
    'django.contrib.auth.backends.ModelBackend',
]

LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/' 


# SOCIAL_AUTH_FACEBOOK_KEY = '481516858047813'
# SOCIAL_AUTH_FACEBOOK_SECRET = '1b5d4c130a789740efed3b7d3168284f'
# SOCIAL_AUTH_FACEBOOK_SCOPE = ['email']  # Optional, but recommended
# SOCIAL_AUTH_FACEBOOK_PROFILE_EXTRA_PARAMS = {
#     'fields': 'id, name, email, picture.type(large)'
# }

# SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = '40192662847-17hkp60agk5k5at07dto52j7gboqrudh.apps.googleusercontent.com'  
# SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = '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'


# SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = [
#     'https://www.googleapis.com/auth/calendar',
#     'https://www.googleapis.com/auth/userinfo.email',
#     'https://www.googleapis.com/auth/userinfo.profile',
# ]

# Optional: If you want to store the tokens in the database
SOCIAL_AUTH_GOOGLE_OAUTH2_EXTRA_DATA = [
    ('refresh_token', 'refresh_token'),
    ('expires_in', 'expires'),
    ('access_token', 'access_token'),
]

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
            'filename': os.path.join(BASE_DIR, 'logs/users.log'),
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

USER_SERVICE_URL = os.getenv('USER_SERVICE_URL', 'http://localhost:8000/api/users/')
NOTIFICATION_SERVICE_URL = os.environ.setdefault('NOTIFICATION_SERVICE_URL', 'http://localhost:8070/api/v1/notifications/')
