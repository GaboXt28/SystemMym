from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

# Importamos todas las vistas desde tu aplicación 'gestion'
# Esto asegura que los nombres coincidan con lo que pusimos en views.py
from gestion.views import (
    dashboard_analiticas,
    generar_pdf_guia,
    exportar_reporte_excel,
    health_check,
    api_info_producto,
    api_info_cliente,
    reporte_asesores  # <--- AGREGADO: La nueva vista
)

urlpatterns = [
    # 1. PÁGINA DE INICIO (DASHBOARD)
    # Redirigimos tanto la ruta vacía como 'home/' al dashboard para evitar errores
    path('', dashboard_analiticas, name='home'),
    path('home/', dashboard_analiticas, name='home_alias'),

    # 2. PANEL ADMINISTRATIVO
    path('adminconfiguracion/', admin.site.urls),

    # 3. RUTAS DE REPORTES Y PDF
    path('dashboard/', dashboard_analiticas, name='dashboard_analytics'),
    path('imprimir/guia/<int:guia_id>/', generar_pdf_guia, name='imprimir_guia'),
    path('reporte/excel/', exportar_reporte_excel, name='exportar_excel'),
    
    # --- NUEVA RUTA: REPORTE DE ASESORES ---
    path('reporte/asesores/', reporte_asesores, name='reporte_asesores'),

    # 4. SALUD DEL SISTEMA (CRON JOBS)
    path('health/', health_check, name='health_check'),

    # 5. APIs PARA EL JAVASCRIPT (EL CEREBRO DEL CÁLCULO)
    # Estas rutas son las que llama tu archivo custom_admin.js
    path('api/cliente/<int:cliente_id>/', api_info_cliente, name='api_info_cliente'),
    path('api/producto/<int:producto_id>/', api_info_producto, name='api_info_producto'),
]

# --- CONFIGURACIÓN PARA IMÁGENES (SOLO EN MODO DEBUG) ---
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)