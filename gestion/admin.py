from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.utils import timezone 
from django.http import HttpResponseRedirect
from django.db.models import Sum
from datetime import datetime 
from .models import Cliente, Producto, GuiaEntrega, DetalleGuia, Pago, Proveedor, Gasto, Asistencia

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

# --- 2. CONFIGURACIÓN DE ASISTENCIA ---
@admin.register(Asistencia)
class AsistenciaAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'fecha_visual', 'hora_entrada', 'hora_salida', 'calculo_horas')
    list_filter = ('fecha', 'usuario')
    
    def fecha_visual(self, obj):
        return obj.fecha.strftime("%d/%m/%Y")
    fecha_visual.short_description = "Fecha"

    def calculo_horas(self, obj):
        horas = obj.horas_trabajadas()
        color = "green" if horas >= 8 else "orange"
        if horas == 0: color = "red"
        return format_html('<b style="color:{}">{} hrs</b>', color, horas)
    calculo_horas.short_description = "Jornada"

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

# --- 3. CONFIGURACIÓN DE CLIENTES (CORREGIDO ERROR FLOAT) ---
@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre_contacto', 'celular', 'ciudad', 'estado_deuda_visual', 'acciones_cobranza')
    search_fields = ('nombre_contacto', 'nombre_empresa')
    list_filter = ('ciudad',)
    list_per_page = 20

    # A. CÁLCULO DE DEUDA VISUAL
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
            # CORRECCIÓN CLAVE: Formateamos el número AQUÍ, afuera del HTML
            texto_deuda = f"{deuda:.2f}"
            
            return format_html(
                '<span style="color:#dc3545; font-weight:bold; font-size:1.1em;">S/. {}</span><br>'
                '<span style="font-size:0.8em; color:#666;">En {} guía(s)</span>',
                texto_deuda, guias_pendientes.count()
            )
        else:
            return mark_safe('<span style="color:#28a745; font-weight:bold;">✅ Al día</span>')
    
    estado_deuda_visual.short_description = "Deuda Total"

    # B. BOTONES DE ACCIÓN
    def acciones_cobranza(self, obj):
        guias_pendientes = obj.guiaentrega_set.exclude(estado_pago='PAGADO')
        deuda = 0
        if guias_pendientes.exists():
            datos = guias_pendientes.aggregate(t=Sum('total_venta'), a=Sum('monto_cobrado'))
            deuda = (datos['t'] or 0) - (datos['a'] or 0)

        botones = []

        if deuda > 0:
            # Formateamos el monto para el mensaje de WhatsApp
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