"""
Django settings for config project.
Updated for Production and Jazzmin customization.
"""
import os
import dj_database_url
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
# En producción idealmente esto viene de una variable de entorno, pero por ahora lo dejamos así.
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-nae_=9++)5)-(_!6me6c_!^5ot_aj@r^vjkmpdt1=l0ovn*wz6')

# SECURITY WARNING: don't run with debug turned on in production!
# Esto detecta si estás en Render/Railway para desactivar el modo Debug automáticamente
DEBUG = 'RENDER' not in os.environ

# Permitimos todos los hosts para evitar errores al desplegar
ALLOWED_HOSTS = ['*']

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
    'whitenoise.middleware.WhiteNoiseMiddleware',  # <--- ESENCIAL PARA ESTILOS EN LA NUBE
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


# --- BASE DE DATOS (Configuración Híbrida) ---
# Si hay una URL de base de datos en el entorno (Nube), usa esa (PostgreSQL).
# Si no, usa el archivo db.sqlite3 local.
DATABASES = {
    'default': dj_database_url.config(
        default='sqlite:///' + str(BASE_DIR / 'db.sqlite3'),
        conn_max_age=600
    )
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


# --- INTERNACIONALIZACIÓN (Configuración para Perú) ---
LANGUAGE_CODE = 'es-pe'  # Español Perú

TIME_ZONE = 'America/Lima' # Hora de Perú

USE_I18N = True

USE_TZ = True


# --- ARCHIVOS ESTÁTICOS Y MEDIA ---

STATIC_URL = 'static/'

# Esto le dice a Django dónde reunir todos los archivos estáticos al desplegar
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Configuración de WhiteNoise para comprimir y servir archivos eficientemente
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Configuración para subir imágenes (Productos, logos, etc.)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# --- CONFIGURACIÓN DE JAZZMIN (INTERFAZ) ---
JAZZMIN_SETTINGS = {
    "site_title": "Admin MyM",
    "site_header": "Sistema MyM",
    "site_brand": "Creaciones MyM",
    "welcome_sign": "Bienvenido al ERP",
    "search_model": ["gestion.Cliente", "gestion.GuiaEntrega"],

    "topmenu_links": [
        {"name": "🏠 Inicio (Dashboard)",  "url": "home", "permissions": ["auth.view_user"]},
        {"name": "⚙️ Configurar Tablas", "url": "admin:index", "permissions": ["auth.view_user"]},
    ],

    "show_sidebar": True,
    "navigation_expanded": True,
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "gestion.Cliente": "fas fa-user-tie",
        "gestion.Producto": "fas fa-box-open",
        "gestion.GuiaEntrega": "fas fa-file-invoice-dollar",
        "gestion.Pago": "fas fa-hand-holding-usd",
        "gestion.Proveedor": "fas fa-truck",
        "gestion.Gasto": "fas fa-money-bill-wave",
    },
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",
    "show_ui_builder": False,
    "changeform_format": "horizontal_tabs",
    
    # Custom JS
    "custom_js": "gestion/js/custom_admin.js",
}

# --- REDIRECCIONES CLAVE ---
LOGIN_REDIRECT_URL = 'home' 
LOGOUT_REDIRECT_URL = '/adminconfiguracion/login/'

# Colores y Tema
JAZZMIN_UI_TWEAKS = {
    "theme": "flatly",
    "navbar": "navbar-dark",
}