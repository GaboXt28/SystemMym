"""
Django settings for config project.
Optimized for SystemMyM - Production.
"""
import os
import dj_database_url
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-nae_=9++)5)-(_!6me6c_!^5ot_aj@r^vjkmpdt1=l0ovn*wz6')

# --- SEGURIDAD: MODO PRODUCCIÓN ---
# Lo ponemos en False para seguridad. Solo cámbialo a True si hay un error grave que necesitas investigar.
DEBUG = True

ALLOWED_HOSTS = ['*']

# --- ORIGENES DE CONFIANZA (HTTPS) ---
CSRF_TRUSTED_ORIGINS = [
    'https://systemmym.onrender.com',
]

# Application definition
INSTALLED_APPS = [
    'jazzmin',                  # <--- JAZZMIN SIEMPRE PRIMERO
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'gestion',                  # Tu aplicación principal
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # <--- ESENCIAL PARA ESTILOS
    'django.contrib.sessions.middleware.SessionMiddleware',
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

WSGI_APPLICATION = 'config.wsgi.application'

# --- BASE DE DATOS ---
DATABASES = {
    'default': dj_database_url.config(
        default='sqlite:///' + str(BASE_DIR / 'db.sqlite3'),
        conn_max_age=600
    )
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    { 'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator', },
]

# --- INTERNACIONALIZACIÓN (PERÚ) ---
LANGUAGE_CODE = 'es-pe'  
TIME_ZONE = 'America/Lima'   # <--- HORA PERUANA CONFIRMADA
USE_I18N = True
USE_TZ = True

# --- ARCHIVOS ESTÁTICOS Y MEDIA ---
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# --- SISTEMA DE LOGS (PARA VER ERRORES EN RENDER) ---
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

# --- CONFIGURACIÓN DE JAZZMIN (PANEL ADMIN) ---
JAZZMIN_SETTINGS = {
    "site_title": "Admin MyM",
    "site_header": "Sistema MyM",
    "site_brand": "Creaciones MyM",
    "welcome_sign": "Bienvenido al ERP",
    "search_model": ["gestion.Cliente", "gestion.GuiaEntrega"],

    # Menú superior
    "topmenu_links": [
        {"name": "🏠 Dashboard",  "url": "home", "permissions": ["auth.view_user"]}, # Solo Admin ve esto gracias a views.py
        {"name": "⚙️ Panel Admin", "url": "admin:index", "permissions": ["auth.view_user"]},
    ],

    "show_sidebar": True,
    "navigation_expanded": True,
    
    # --- ICONOS DEL MENÚ LATERAL ---
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "gestion.Cliente": "fas fa-user-tie",
        "gestion.Producto": "fas fa-box-open",
        "gestion.GuiaEntrega": "fas fa-file-invoice-dollar",
        "gestion.Pago": "fas fa-hand-holding-usd",
        "gestion.Proveedor": "fas fa-truck",
        "gestion.Gasto": "fas fa-money-bill-wave",
        "gestion.Asistencia": "fas fa-clock", # <--- NUEVO ICONO PARA ASISTENCIA
    },
    
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",
    "show_ui_builder": False,
    "changeform_format": "horizontal_tabs",
    
    # Enlazamos tu JS personalizado
    "custom_js": "gestion/js/custom_admin.js",
}

# Redirección al login
LOGIN_REDIRECT_URL = 'home' 
LOGOUT_REDIRECT_URL = '/adminconfiguracion/login/'

JAZZMIN_UI_TWEAKS = {
    "theme": "flatly",
    "navbar": "navbar-dark",
}