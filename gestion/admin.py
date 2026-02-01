from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.utils import timezone 
from django.http import HttpResponseRedirect, HttpResponse # <--- AGREGADO HttpResponse para recibos
from django.db.models import Sum
from datetime import datetime
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

# Importamos tus modelos (incluyendo el nuevo PerfilColaborador)
from .models import Cliente, Producto, GuiaEntrega, DetalleGuia, Pago, Proveedor, Gasto, Asistencia, PerfilColaborador

# --- 0. CONFIGURACIÓN DE USUARIOS (NÓMINA) ---
class PerfilInline(admin.StackedInline):
    model = PerfilColaborador
    can_delete = False
    verbose_name_plural = 'Datos de Nómina'
    fk_name = 'usuario'

class UserAdmin(BaseUserAdmin):
    inlines = [PerfilInline]

try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass
admin.site.register(User, UserAdmin)

# --- 1. CONFIGURACIÓN DE PRODUCTOS ---
@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio_unitario', 'stock_actual', 'alerta_stock')
    search_fields = ('nombre',)
    list_per_page = 20

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            return []
        return ['nombre', 'precio_unitario']

    def alerta_stock(self, obj):
        if obj.stock_actual <= 10:
            return format_html('<span style="color:red; font-weight:bold;">⚠️ BAJO ({})</span>', obj.stock_actual)
        return format_html('<span style="color:green; font-weight:bold;">✅ OK ({})</span>', obj.stock_actual)
    alerta_stock.short_description = "Estado Stock"

# --- 2. CONFIGURACIÓN DE ASISTENCIA (CON RECIBO SEGURO) ---

# --- FUNCIÓN GENERADORA DE RECIBOS ---
@admin.action(description="📄 Generar Recibo de Pago (Días seleccionados)")
def generar_recibo_pago(modeladmin, request, queryset):
    # Ordenamos por fecha
    seleccion = queryset.order_by('fecha')
    
    # Identificamos usuarios únicos seleccionados
    usuarios_seleccionados = set(asistencia.usuario for asistencia in seleccion)
    
    # Estilos CSS para el recibo (Diseño limpio y profesional)
    html_content = """
    <html>
    <head>
        <title>Recibo de Nómina</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; padding: 40px; background: #f9f9f9; }
            .contenedor-recibo { 
                background: white; 
                border: 1px solid #ccc; 
                padding: 30px; 
                margin-bottom: 40px; 
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
                page-break-inside: avoid; /* Evita que el recibo se corte al imprimir */
            }
            .header { text-align: center; border-bottom: 2px solid #333; padding-bottom: 10px; margin-bottom: 20px; }
            .header h1 { margin: 0; color: #2c3e50; font-size: 24px; }
            .header p { margin: 5px 0 0; color: #7f8c8d; font-size: 14px; }
            
            .info-empleado { margin-bottom: 20px; font-size: 15px; }
            .info-empleado strong { color: #333; }
            
            table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 14px; }
            th, td { border: 1px solid #e0e0e0; padding: 10px; text-align: center; }
            th { background-color: #f8f9fa; color: #333; font-weight: bold; }
            tr:nth-child(even) { background-color: #fcfcfc; }
            
            .total-row { background-color: #2c3e50 !important; color: white; font-weight: bold; font-size: 16px; }
            .total-row td { border: 1px solid #2c3e50; }
            
            .firmas { margin-top: 60px; display: flex; justify-content: space-between; }
            .firma-box { width: 40%; border-top: 1px solid #333; text-align: center; padding-top: 10px; font-size: 14px; color: #333; }
            
            /* Botones que no salen en la impresión */
            @media print { .no-print { display: none; } body { background: white; padding: 0; } .contenedor-recibo { border: none; box-shadow: none; } }
            
            .btn { padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold; margin-right: 10px; display: inline-block; cursor: pointer; border: none;}
            .btn-print { background: #28a745; color: white; }
            .btn-back { background: #6c757d; color: white; }
        </style>
    </head>
    <body>
        <div class="no-print">
            <button onclick="window.print()" class="btn btn-print">🖨️ Imprimir Recibo</button>
            <a href="javascript:history.back()" class="btn btn-back">⬅️ Volver</a>
            <br><br>
        </div>
    """

    for usuario in usuarios_seleccionados:
        # Filtramos días de este usuario
        asistencias_usuario = seleccion.filter(usuario=usuario)
        
        nombre_completo = f"{usuario.first_name} {usuario.last_name}"
        if len(nombre_completo.strip()) < 2:
            nombre_completo = usuario.username # Si no tiene nombre real, usa el usuario

        # Obtener tarifa
        try:
            tarifa = usuario.perfil.tarifa_por_hora
        except:
            tarifa = 0

        total_dinero = 0
        total_horas = 0

        # Encabezado del recibo
        html_content += f"""
        <div class="contenedor-recibo">
            <div class="header">
                <h1>RECIBO DE PAGO</h1>
                <p>CREACIONES MYM - Control Interno</p>
            </div>
            
            <div class="info-empleado">
                <p><strong>Colaborador:</strong> {nombre_completo}</p>
                <p><strong>Fecha de Emisión:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
                <p><strong>Tarifa por Hora:</strong> S/. {tarifa}</p>
            </div>
            
            <table>
                <thead>
                    <tr>
                        <th>Fecha</th>
                        <th>Entrada</th>
                        <th>Salida</th>
                        <th>Horas Trab.</th>
                        <th>Total Día</th>
                    </tr>
                </thead>
                <tbody>
        """

        # Filas de días
        for asistencia in asistencias_usuario:
            horas = asistencia.horas_trabajadas()
            pago_dia = float(horas) * float(tarifa)
            
            total_dinero += pago_dia
            total_horas += horas

            html_content += f"""
                <tr>
                    <td>{asistencia.fecha.strftime('%d/%m/%Y')}</td>
                    <td>{asistencia.hora_entrada.strftime('%H:%M') if asistencia.hora_entrada else '-'}</td>
                    <td>{asistencia.hora_salida.strftime('%H:%M') if asistencia.hora_salida else '-'}</td>
                    <td>{horas} hrs</td>
                    <td>S/. {pago_dia:.2f}</td>
                </tr>
            """

        # Fila de Totales
        html_content += f"""
                <tr class="total-row">
                    <td colspan="3" style="text-align: right; padding-right: 20px;">TOTAL A PAGAR:</td>
                    <td>{total_horas:.2f} hrs</td>
                    <td>S/. {total_dinero:.2f}</td>
                </tr>
                </tbody>
            </table>

            <div class="firmas">
                <div class="firma-box">
                    <br>
                    Administración
                </div>
                <div class="firma-box">
                    <br>
                    Recibí Conforme<br>
                    {nombre_completo}
                </div>
            </div>
        </div>
        """

    html_content += "</body></html>"
    return HttpResponse(html_content)


@admin.register(Asistencia)
class AsistenciaAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'fecha_visual', 'hora_entrada', 'hora_salida', 'calculo_horas', 'pago_estimado')
    list_filter = ('fecha', 'usuario')
    actions = [generar_recibo_pago] # <--- ACTIVAMOS LA ACCIÓN
    
    # --- FILTRO DE SEGURIDAD PARA ACCIONES ---
    def get_actions(self, request):
        actions = super().get_actions(request)
        # Si el usuario NO es superusuario, eliminamos la opción de generar recibo
        if not request.user.is_superuser:
            if 'generar_recibo_pago' in actions:
                del actions['generar_recibo_pago']
        return actions
    # -----------------------------------------

    def fecha_visual(self, obj):
        return obj.fecha.strftime("%d/%m/%Y")
    fecha_visual.short_description = "Fecha"

    def calculo_horas(self, obj):
        horas = obj.horas_trabajadas()
        color = "green" if horas >= 8 else "orange"
        if horas == 0: color = "red"
        return format_html('<b style="color:{}">{} hrs</b>', color, horas)
    calculo_horas.short_description = "Jornada"

    def pago_estimado(self, obj):
        try:
            horas = obj.horas_trabajadas()
            tarifa = obj.usuario.perfil.tarifa_por_hora
            total = float(horas) * float(tarifa)
            return f"S/. {total:.2f}"
        except:
            return "-"
    pago_estimado.short_description = "Pago (Día)"

    def save_model(self, request, obj, form, change):
        ahora_lima = timezone.localtime(timezone.now())
        if not change: 
            obj.usuario = request.user
            obj.fecha = ahora_lima.date()
            obj.hora_entrada = ahora_lima.time()
        else:
            if not obj.hora_salida:
                obj.hora_salida = ahora_lima.time()
        super().save_model(request, obj, form, change)

    def get_readonly_fields(self, request, obj=None):
        return ['usuario', 'fecha', 'hora_entrada', 'hora_salida']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs 
        return qs.filter(usuario=request.user)

# --- 3. CONFIGURACIÓN DE CLIENTES ---
@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre_contacto', 'celular', 'ciudad', 'estado_deuda_visual', 'acciones_cobranza')
    search_fields = ('nombre_contacto', 'nombre_empresa')
    list_filter = ('ciudad',)
    list_per_page = 20

    def estado_deuda_visual(self, obj):
        guias_pendientes = obj.guiaentrega_set.exclude(estado_pago='PAGADO')
        datos = guias_pendientes.aggregate(
            total_vendido=Sum('total_venta'),
            total_abonado=Sum('monto_cobrado')
        )
        vendido = datos['total_vendido'] or 0
        abonado = datos['total_abonado'] or 0
        deuda = vendido - abonado

        if deuda > 0:
            texto_deuda = f"{deuda:.2f}"
            return format_html(
                '<span style="color:#dc3545; font-weight:bold; font-size:1.1em;">S/. {}</span><br>'
                '<span style="font-size:0.8em; color:#666;">En {} guía(s)</span>',
                texto_deuda, guias_pendientes.count()
            )
        else:
            return mark_safe('<span style="color:#28a745; font-weight:bold;">✅ Al día</span>')
    
    estado_deuda_visual.short_description = "Deuda Total"

    def acciones_cobranza(self, obj):
        guias_pendientes = obj.guiaentrega_set.exclude(estado_pago='PAGADO')
        deuda = 0
        if guias_pendientes.exists():
            datos = guias_pendientes.aggregate(t=Sum('total_venta'), a=Sum('monto_cobrado'))
            deuda = (datos['t'] or 0) - (datos['a'] or 0)

        botones = []

        if deuda > 0:
            texto_deuda = f"{deuda:.2f}"
            url_pagar = reverse('admin:gestion_guiaentrega_changelist') + f'?cliente__id__exact={obj.id}&estado_pago__in=PENDIENTE,PARCIAL'
            botones.append(
                f'<a class="button" href="{url_pagar}" style="background-color:#ffc107; color:#000; font-weight:bold; padding:4px 8px; border-radius:4px;">💰 Pagar</a>'
            )
            if obj.celular:
                msg = f"Hola {obj.nombre_contacto}, le escribimos de MyM. Le recordamos que tiene un saldo pendiente de S/. {texto_deuda}. Saludos."
                url_wsp = f"https://wa.me/51{obj.celular}?text={msg}"
                botones.append(
                    f'<a class="button" href="{url_wsp}" target="_blank" style="background-color:#25D366; color:white; padding:4px 8px; border-radius:4px; margin-left:5px;">'
                    f'<i class="fab fa-whatsapp"></i> Cobrar</a>'
                )
        else:
            url_historial = reverse('admin:gestion_guiaentrega_changelist') + f'?cliente__id__exact={obj.id}'
            botones.append(
                f'<a class="button" href="{url_historial}" style="background-color:#17a2b8; color:white; padding:4px 8px; border-radius:4px;">📋 Historial</a>'
            )

        return mark_safe("".join(botones))

    acciones_cobranza.short_description = "Acciones Rápidas"

# --- 4. CONFIGURACIÓN DE GUÍAS DE ENTREGA ---
class DetalleGuiaInline(admin.TabularInline):
    model = DetalleGuia
    extra = 1
    autocomplete_fields = ['producto']
    min_num = 1 

class PagoInline(admin.TabularInline):
    model = Pago
    extra = 0

@admin.register(GuiaEntrega)
class GuiaEntregaAdmin(admin.ModelAdmin):
    list_display = ('numero_guia_visual', 'cliente', 'fecha_emision', 'total_venta', 'estado_pago_color', 'acciones_pdf')
    list_filter = ('estado_pago', 'fecha_emision') 
    search_fields = ('numero_guia', 'cliente__nombre_contacto', 'cliente__nombre_empresa')
    date_hierarchy = 'fecha_emision' 
    inlines = [DetalleGuiaInline, PagoInline]
    autocomplete_fields = ['cliente']
    ordering = ('-fecha_emision', '-numero_guia')

    class Media:
        js = ('gestion/js/custom_admin.js',)

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        anio_actual = timezone.now().year
        ultima_guia = GuiaEntrega.objects.filter(
            fecha_emision__year=anio_actual
        ).order_by('numero_guia').last()

        if ultima_guia and ultima_guia.numero_guia.isdigit():
            siguiente = int(ultima_guia.numero_guia) + 1
            initial['numero_guia'] = str(siguiente).zfill(6) 
        else:
            initial['numero_guia'] = '000001' 
        return initial

    def changelist_view(self, request, extra_context=None):
        referer = request.META.get('HTTP_REFERER', '')
        path_actual = request.path
        if not request.GET and path_actual not in referer:
            anio_actual = timezone.now().year
            q = request.GET.copy()
            q['fecha_emision__year'] = anio_actual
            return HttpResponseRedirect(f"{request.path}?{q.urlencode()}")
        return super().changelist_view(request, extra_context)

    def numero_guia_visual(self, obj):
        return format_html('<b style="color: #2c3e50;">#{}</b>', obj.numero_guia)
    numero_guia_visual.short_description = "N° Guía"

    def estado_pago_color(self, obj):
        colores = {'PENDIENTE': 'red', 'PARCIAL': 'orange', 'PAGADO': 'green'}
        color = colores.get(obj.estado_pago, 'black')
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, obj.get_estado_pago_display())
    estado_pago_color.short_description = "Estado Pago"

    def acciones_pdf(self, obj):
        try:
            url_base = reverse('imprimir_guia', args=[obj.id])
            url_ver = f"{url_base}?ver=true"
            return format_html(
                '<a class="button ver-pdf-modal" href="{}" style="cursor:pointer; background-color:#17a2b8; color:white; padding:3px 8px; border-radius:3px;">👁️ Ver</a>&nbsp;'
                '<a class="button" href="{}" style="background-color:#6c757d; color:white; padding:3px 8px; border-radius:3px;">📥 PDF</a>',
                url_ver, url_base
            )
        except: return "-"
    acciones_pdf.short_description = "Documentos"

# --- 5. CONFIGURACIÓN DE FINANZAS ---
@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ('razon_social', 'tipo', 'telefono', 'ruc_dni')
    search_fields = ('razon_social', 'ruc_dni')
    list_filter = ('tipo',)

@admin.register(Gasto)
class GastoAdmin(admin.ModelAdmin):
    list_display = ('descripcion', 'proveedor', 'fecha_emision', 'monto', 'estado_color')
    list_filter = ('estado', 'categoria', 'fecha_emision')
    search_fields = ('descripcion', 'proveedor__razon_social')
    date_hierarchy = 'fecha_emision' 

    def estado_color(self, obj):
        color = 'green' if obj.estado == 'PAGADO' else 'red'
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, obj.get_estado_display())
    estado_color.short_description = "Estado"