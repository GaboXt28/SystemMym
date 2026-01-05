import openpyxl 
from openpyxl.styles import Font, PatternFill
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.template.loader import get_template
from django.db.models import Sum
from django.utils import timezone
from datetime import datetime
from xhtml2pdf import pisa
from .models import GuiaEntrega, Producto, Gasto, Cliente # <--- Confirmado que existen
from django.contrib import admin
from django.contrib.auth.decorators import login_required

# --- VISTA 1: GENERADOR DE PDF ---
def generar_pdf_guia(request, guia_id):
    guia = get_object_or_404(GuiaEntrega, pk=guia_id)
    detalles = guia.detalles.all()
    saldo_pendiente = guia.total_venta - guia.monto_cobrado
    
    context = {
        'guia': guia,
        'detalles': detalles,
        'saldo_pendiente': saldo_pendiente,
    }
    
    template_path = 'gestion/guia_pdf.html'
    response = HttpResponse(content_type='application/pdf')
    
    tipo_visualizacion = 'inline' if request.GET.get('ver') == 'true' else 'attachment'
    response['Content-Disposition'] = f'{tipo_visualizacion}; filename="Guia-{guia.numero_guia}.pdf"'
    
    template = get_template(template_path)
    html = template.render(context)

    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('Error generando PDF')
    return response

# --- VISTA 2: DASHBOARD GERENCIAL (A PRUEBA DE FALLOS) ---
@login_required(login_url='/adminconfiguracion/login/') 
def dashboard_analiticas(request):
    # 1. Detectar Año
    anio_actual = timezone.now().year
    try:
        anio_seleccionado = int(request.GET.get('anio', anio_actual))
    except ValueError:
        anio_seleccionado = anio_actual

    # 2. Consultar Datos (Usando los nombres exactos de tu models.py)
    ventas = GuiaEntrega.objects.filter(fecha_emision__year=anio_seleccionado)
    gastos = Gasto.objects.filter(fecha_emision__year=anio_seleccionado)

    # 3. Preparar lista de años (SEGURA)
    fechas_disponibles = GuiaEntrega.objects.dates('fecha_emision', 'year', order='DESC')
    # Convertimos a lista de enteros simple [2026, 2025]
    lista_anios = [f.year for f in fechas_disponibles]
    
    if anio_seleccionado not in lista_anios:
        lista_anios.insert(0, anio_seleccionado)

    # 4. Cálculos
    total_ventas = ventas.aggregate(total=Sum('total_venta'))['total'] or 0
    total_cobrado = ventas.aggregate(total=Sum('monto_cobrado'))['total'] or 0
    total_gastos = gastos.aggregate(total=Sum('monto'))['total'] or 0
    
    # Deuda (Histórico global, no por año)
    deuda_calle = 0
    for g in GuiaEntrega.objects.exclude(estado_pago='PAGADO'):
        deuda_calle += (g.total_venta - g.monto_cobrado)

    ganancia_neta = total_ventas - total_gastos

    # Productos bajo stock (Tu modelo dice 'stock_actual', así que esto está bien)
    productos_bajo_stock = Producto.objects.filter(stock_actual__lte=10).order_by('stock_actual')[:5]
    
    ultimas_ventas = ventas.order_by('-fecha_emision', '-numero_guia')[:10]

    # 5. Contexto
    context = admin.site.each_context(request) 
    context.update({
        'total_ventas': total_ventas,
        'total_cobrado': total_cobrado,
        'total_gastos': total_gastos,
        'ganancia_neta': ganancia_neta,
        'deuda_calle': deuda_calle,
        'productos_bajo_stock': productos_bajo_stock,
        'ultimas_ventas': ultimas_ventas,
        'anio_seleccionado': anio_seleccionado,
        'anios_disponibles': lista_anios, # Enviamos la lista segura
    })
    
    return render(request, 'gestion/dashboard.html', context)

# --- VISTA 3: API AUXILIARES ---
def health_check(request):
    return HttpResponse("OK")

def obtener_direccion_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    return JsonResponse({'direccion': cliente.direccion_principal}) # Corregido: en tu modelo es 'direccion_principal'

# --- VISTA 4: EXCEL ---
@login_required(login_url='/adminconfiguracion/login/')
def exportar_reporte_excel(request):
    # Lógica simplificada de Excel
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=Reporte_MyM.xlsx'
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Resumen"
    ws['A1'] = "Reporte generado exitosamente"
    wb.save(response)
    return response