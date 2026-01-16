from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone 
from django.http import HttpResponseRedirect 
from .models import Cliente, Producto, GuiaEntrega, DetalleGuia, Pago, Proveedor, Gasto

# --- 1. CONFIGURACIÓN DE PRODUCTOS ---
@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio_unitario', 'stock_actual', 'alerta_stock')
    search_fields = ('nombre',)
    list_editable = ('stock_actual', 'precio_unitario')
    list_per_page = 20

    def alerta_stock(self, obj):
        if obj.stock_actual <= 10:
            return format_html('<span style="color:red; font-weight:bold;">⚠️ BAJO ({})</span>', obj.stock_actual)
        return format_html('<span style="color:green; font-weight:bold;">✅ OK ({})</span>', obj.stock_actual)
    alerta_stock.short_description = "Estado Stock"

# --- 2. CONFIGURACIÓN DE CLIENTES ---
@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre_contacto', 'nombre_empresa', 'celular', 'ciudad')
    search_fields = ('nombre_contacto', 'nombre_empresa')
    list_filter = ('ciudad',)

# --- 3. CONFIGURACIÓN DE GUÍAS DE ENTREGA ---
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

    # --- CAMBIO: HACEMOS VISIBLES LOS TOTALES ---
    readonly_fields = ('total_venta', 'monto_cobrado')

    # ORGANIZAMOS EL FORMULARIO PARA QUE SE VEA ORDENADO
    fieldsets = (
        ('Información Principal', {
            'fields': ('cliente', 'asesor', 'numero_guia', 'fecha_emision')
        }),
        ('Detalles de Entrega', {
            'fields': ('direccion_entrega', 'observaciones')
        }),
        ('Totales y Estado', {
            'fields': ('total_venta', 'estado_pago', 'monto_cobrado')
        }),
    )

    # --- IMPORTANTE: CARGAMOS EL JAVASCRIPT AQUÍ ---
    class Media:
        js = ('gestion/js/custom_admin.js',)
    # -----------------------------------------------

    # --- LÓGICA DE CORRELATIVO ---
    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        
        # Solo calculamos si estamos añadiendo (add) una nueva guía
        if 'add' in request.path:
            anio_actual = timezone.now().year
            
            # Buscamos la última guía de ESTE año
            ultima_guia = GuiaEntrega.objects.filter(
                fecha_emision__year=anio_actual
            ).order_by('numero_guia').last()

            # Calculamos el siguiente
            if ultima_guia and ultima_guia.numero_guia.isdigit():
                try:
                    siguiente = int(ultima_guia.numero_guia) + 1
                    initial['numero_guia'] = str(siguiente).zfill(6) 
                except:
                    initial['numero_guia'] = '000001'
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

# --- 4. CONFIGURACIÓN DE FINANZAS ---
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