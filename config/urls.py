from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

# Importamos las vistas (incluyendo el health_check)
from gestion.views import (
    health_check, 
    generar_pdf_guia, 
    dashboard_analiticas, 
    exportar_reporte_excel
)

urlpatterns = [
    # 1. ESTO HACE QUE EL PROGRAMA ABRA DIRECTO EN EL DASHBOARD (Home)
    path('', dashboard_analiticas, name='home'),
    
    # 2. El Panel Administrativo
    path('adminconfiguracion/', admin.site.urls),
    
    # 3. Rutas auxiliares
    path('dashboard/', dashboard_analiticas, name='dashboard_analytics'),
    path('imprimir/guia/<int:guia_id>/', generar_pdf_guia, name='imprimir_guia'),
    path('reporte/excel/', exportar_reporte_excel, name='exportar_excel'),

    # 4. RUTA PARA EL "LATIDO DEL CORAZÓN" (CRON JOB)
    # Esta es la que visitará cron-job.org para despertar al servidor
    path('health/', health_check, name='health_check'),
]

# --- CONFIGURACIÓN PARA IMÁGENES ---
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)