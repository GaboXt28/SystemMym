
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Cliente, Producto, GuiaEntrega, DetalleGuia, Pago, Proveedor, Gasto

# --- 1. CONFIGURACIÓN DE PRODUCTOS (Con Alerta de Colores) ---
@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio_unitario', 'stock_actual', 'alerta_stock')
    search_fields = ('nombre',)
    list_editable = ('stock_actual', 'precio_unitario')
    list_per_page = 20

    def alerta_stock(self, obj):
        # Si el stock es 10 o menos, sale rojo. Si no, verde.
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

# --- 3. CONFIGURACIÓN DE GUÍAS DE ENTREGA (El Cerebro del Sistema) ---
class DetalleGuiaInline(admin.TabularInline):
    model = DetalleGuia
    extra = 1
    autocomplete_fields = ['producto']
    min_num = 1 # Obliga a poner al menos 1 producto

class PagoInline(admin.TabularInline):
    model = Pago
    extra = 0

@admin.register(GuiaEntrega)
class GuiaEntregaAdmin(admin.ModelAdmin):
    # Columnas visibles
    list_display = ('numero_guia_visual', 'cliente', 'fecha_emision', 'total_venta', 'estado_pago_color', 'acciones_pdf')
    
    # Filtros laterales y Búsqueda
    list_filter = ('estado_pago', 'fecha_emision') 
    search_fields = ('numero_guia', 'cliente__nombre_contacto', 'cliente__nombre_empresa')
    
    # --- LA MAGIA: Navegación por Años ---
    # Esto crea las pestañas de años arriba de la tabla
    date_hierarchy = 'fecha_emision' 
    
    # Componentes dentro del formulario
    inlines = [DetalleGuiaInline, PagoInline]
    autocomplete_fields = ['cliente']
    
    # Orden: Lo más reciente primero
    ordering = ('-fecha_emision', '-numero_guia')

    # Campo visual para el número de guía
    def numero_guia_visual(self, obj):
        return format_html('<b style="color: #2c3e50;">#{}</b>', obj.numero_guia)
    numero_guia_visual.short_description = "N° Guía"

    # Colorear el estado de pago
    def estado_pago_color(self, obj):
        colores = {
            'PENDIENTE': 'red',
            'PARCIAL': 'orange',
            'PAGADO': 'green',
        }
        color = colores.get(obj.estado_pago, 'black')
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, obj.get_estado_pago_display())
    estado_pago_color.short_description = "Estado Pago"

    # Botones de Acción (PDF)
    def acciones_pdf(self, obj):
        # Generamos las URLs usando el ID de la guía
        try:
            url_descargar = reverse('imprimir_guia', args=[obj.id])
            url_ver = f"{url_descargar}?ver=true"
            return format_html(
                '<a class="button" href="{}" target="_blank" style="background-color:#17a2b8; color:white; padding:3px 8px; border-radius:3px;">👁️ Ver</a>&nbsp;'
                '<a class="button" href="{}" style="background-color:#6c757d; color:white; padding:3px 8px; border-radius:3px;">📥 PDF</a>',
                url_ver, url_descargar
            )
        except:
            return "-"
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
    date_hierarchy = 'fecha_emision' # También organizamos gastos por año

    def estado_color(self, obj):
        color = 'green' if obj.estado == 'PAGADO' else 'red'
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, obj.get_estado_display())
    estado_color.short_description = "Estado"