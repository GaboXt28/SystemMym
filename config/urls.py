from django.contrib import admin
from django.urls import path
# Importamos la vista del dashboard
from gestion.views import generar_pdf_guia, dashboard_analiticas, exportar_reporte_excel

urlpatterns = [
    # 1. ESTO HACE QUE EL PROGRAMA ABRA DIRECTO EN EL DASHBOARD (Home)
    path('', dashboard_analiticas, name='home'),
    
    # 2. El Panel Administrativo (Tablas) lo movemos a esta ruta
    path('adminconfiguracion/', admin.site.urls),
    
    # 3. Rutas auxiliares (necesarias para que funcionen los botones)
    path('dashboard/', dashboard_analiticas, name='dashboard_analytics'),
    path('imprimir/guia/<int:guia_id>/', generar_pdf_guia, name='imprimir_guia'),
    path('reporte/excel/', exportar_reporte_excel, name='exportar_excel'),
]