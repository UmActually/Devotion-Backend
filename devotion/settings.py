"""
Django settings for devotion project.

Generated by 'django-admin startproject' using Django 5.0.4.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.0/ref/settings/
"""

import os
from pathlib import Path
from datetime import timedelta
import oracledb


# Cositas de config extras
ORACLE_LIB_DIR = "/app/vendor/oracle/instantclient_19_22"
TEST_DATABASE = False
ORACLE_THICK_MODE = False
DEFAULT_LIB_DIR = True

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


def read_env_file(name: str) -> str:
    with open(BASE_DIR / ".env") as file:
        for line in file.read().split("\n"):
            if line.startswith(name) and "='" in line:
                return line.split("='")[1][:-1]
        else:
            raise KeyError("Environment variable name not found in .env file.")


def env_variable(name: str) -> str:
    try:
        return os.environ[name].replace("'", "")
    except KeyError:
        return read_env_file(name)


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env_variable("SECRET_KEY")

ALLOWED_HOSTS = [
    "localhost",
    "umm-actually.com",
    "api.umm-actually.com",
    "devotion-450983c14f36.herokuapp.com",
    "159.54.140.58"
]

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    "users",
    "projects",
    "tasks",
    "dashboards"
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

ROOT_URLCONF = 'devotion.urls'

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

WSGI_APPLICATION = 'devotion.wsgi.application'

# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': "django.db.backends.oracle",
        'NAME': env_variable("DB_NAME"),
        "USER": env_variable("DB_USER"),
        "PASSWORD": env_variable("DB_PASSWORD")
    } if not TEST_DATABASE else {
        "ENGINE": "django.db.backends.postgresql",
        "HOST": env_variable("TEST_DB_HOST"),
        "PORT": "5432",
        "NAME": env_variable("TEST_DB_NAME"),
        "USER": env_variable("TEST_DB_USER"),
        "PASSWORD": env_variable("TEST_DB_PASSWORD")
    }
}

# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

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

# Token authentication

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=15),
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
}

# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_ROOT = BASE_DIR / 'static'
STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom user model
AUTH_USER_MODEL = "users.User"

if ORACLE_THICK_MODE:
    if DEFAULT_LIB_DIR:
        oracle_lib_dir = None
        print("Using default Oracle client library directory.")
    elif not os.path.exists(ORACLE_LIB_DIR):
        oracle_lib_dir = None
        print("Oracle client library directory not found.")
    else:
        oracle_lib_dir = ORACLE_LIB_DIR
    oracledb.init_oracle_client(lib_dir=oracle_lib_dir)
