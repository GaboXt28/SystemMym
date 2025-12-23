import os
import django

# Configurar el entorno de Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

def crear_admin():
    username = "admin"           # Tu usuario
    password = "admin123"        # Tu contraseña temporal
    email = "ggabogarcia28@gmail.com"

    if not User.objects.filter(username=username).exists():
        print("------------------------------------------------")
        print(f"⚠️  CREANDO SUPERUSUARIO: {username}")
        print("------------------------------------------------")
        User.objects.create_superuser(username, email, password)
    else:
        print("✅ El superusuario ya existe. No es necesario crearlo.")

if __name__ == "__main__":
    crear_admin()