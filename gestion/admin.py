from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Producto, Cliente, GuiaEntrega, DetalleGuia, Pago, Proveedor, Gasto

# --- CONFIGURACIÓN DE PANELES (INLINES) ---
class DetalleGuiaInline(admin.TabularInline):
    model = DetalleGuia
    extra = 1
    autocomplete_fields = ['producto']

class PagoInline(admin.TabularInline):
    model = Pago
    extra = 0
    verbose_name = "Abono / Pago"
    verbose_name_plural = "Historial de Pagos"

# --- ADMINISTRACIÓN DE GUÍA ---
@admin.register(GuiaEntrega)
class GuiaEntregaAdmin(admin.ModelAdmin):
    list_display = ('numero_guia', 'fecha_emision', 'cliente', 'estado_pago', 'boton_pdf')
    list_filter = ('estado_pago', 'fecha_emision', 'asesor')
    search_fields = ('numero_guia', 'cliente__nombre_contacto')
    readonly_fields = ('boton_pdf', 'total_venta', 'monto_cobrado', 'estado_pago')
    inlines = [DetalleGuiaInline, PagoInline]

    def save_model(self, request, obj, form, change):
        if not obj.asesor:
            obj.asesor = request.user
        super().save_model(request, obj, form, change)

    def boton_pdf(self, obj):
        if obj.pk:
            url = reverse('imprimir_guia', args=[obj.pk])
            # Usamos {} para el enlace también, es más seguro
            return format_html('<a class="button" href="{}" target="_blank" style="background-color:#e74c3c; color:white; padding:5px 10px;">{}</a>', url, 'Descargar PDF')
        return "Guardar primero"
    
    boton_pdf.short_description = "PDF"
    boton_pdf.allow_tags = True

    class Media:
        js = ('gestion/js/admin_calculo.js',)

# --- OTROS MODELOS ---
@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio_unitario', 'stock_actual')
    search_fields = ('nombre',)

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre_contacto', 'nombre_empresa', 'ver_deuda_total')
    
    def ver_deuda_total(self, obj):
        deuda = 0
        for guia in obj.guiaentrega_set.all():
            if guia.estado_pago != 'PAGADO':
                deuda += (guia.total_venta - guia.monto_cobrado)
        return f"S/. {deuda}"
    
    ver_deuda_total.short_description = "Deuda Total"

# --- MÓDULO DE FINANZAS (NUEVO) ---
@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ('razon_social', 'tipo', 'telefono')
    list_filter = ('tipo',)
    search_fields = ('razon_social',)

@admin.register(Gasto)
class GastoAdmin(admin.ModelAdmin):
    # 1. Agregamos 'estado' a la lista para ver el desplegable
    list_display = ('descripcion', 'proveedor', 'fecha_emision', 'monto', 'estado', 'estado_coloreado', 'fecha_vencimiento')
    
    # 2. ESTO ES LA MAGIA: Permite editar el estado directamente desde la lista
    list_editable = ('estado',) 
    
    list_filter = ('estado', 'categoria', 'fecha_emision', 'proveedor') 
    search_fields = ('descripcion', 'proveedor__razon_social')
    date_hierarchy = 'fecha_emision'

    # 3. ACCIÓN EN LOTE: Para marcar 10 gastos como pagados de un golpe
    actions = ['marcar_como_pagado']

    def marcar_como_pagado(self, request, queryset):
        # Actualiza todos los seleccionados a PAGADO
        filas_actualizadas = queryset.update(estado='PAGADO')
        # Muestra un mensaje de éxito arriba
        self.message_user(request, f"{filas_actualizadas} gastos han sido marcados como PAGADOS exitosamente.")
    
    marcar_como_pagado.short_description = "✅ Marcar seleccionados como PAGADOS"

    def estado_coloreado(self, obj):
        if obj.estado == 'PAGADO':
            return format_html('<span style="color: green; font-weight:bold;">{}</span>', 'LISTO')
        elif obj.esta_vencido(): 
            return format_html('<span style="color: red; font-weight:bold; background-color: #ffddd0; padding:3px;">{}</span>', 'VENCIDO')
        else:
            return format_html('<span style="color: orange; font-weight:bold;">{}</span>', 'PENDIENTE')
    
    estado_coloreado.short_description = "Alerta"