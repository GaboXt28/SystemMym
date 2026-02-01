from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, datetime # <--- OJO: Importamos datetime también
from django.contrib.auth.models import User

# 1. CATALOGO DE PRODUCTOS
class Producto(models.Model):
    nombre = models.CharField(max_length=200, verbose_name="Nombre del Producto")
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stock_actual = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.nombre} - S/. {self.precio_unitario}"

# 2. DIRECTORIO DE CLIENTES
class Cliente(models.Model):
    nombre_contacto = models.CharField(max_length=150, verbose_name="Nombre Persona")
    nombre_empresa = models.CharField(max_length=150, blank=True, null=True, verbose_name="Razón Social / Empresa")
    celular = models.CharField(max_length=20, blank=True)
    direccion_principal = models.CharField(max_length=255, blank=True)
    ciudad = models.CharField(max_length=100, default="Lima")
    
    def __str__(self):
        return f"{self.nombre_contacto} ({self.nombre_empresa or 'Particular'})"

# 3. LA GUÍA DE ENTREGA (Cabecera)
class GuiaEntrega(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT)
    asesor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    # Sin unique=True para permitir repetir números en años distintos
    numero_guia = models.CharField(max_length=20) 
    
    fecha_emision = models.DateField(default=timezone.now)
    direccion_entrega = models.CharField(max_length=255)
    
    total_venta = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)
    
    ESTADOS_PAGO = [
        ('PENDIENTE', 'Pendiente de Pago'),
        ('PARCIAL', 'Pago Parcial'),
        ('PAGADO', 'Pagado Completo'),
    ]
    estado_pago = models.CharField(max_length=20, choices=ESTADOS_PAGO, default='PENDIENTE')
    
    monto_cobrado = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)
    observaciones = models.TextField(blank=True, default="No hay devoluciones.")

    def actualizar_estado_pago(self):
        total_pagado = sum([p.monto for p in self.pagos.all()])
        self.monto_cobrado = total_pagado

        if self.monto_cobrado >= self.total_venta and self.total_venta > 0:
            self.estado_pago = 'PAGADO'
        elif self.monto_cobrado > 0:
            self.estado_pago = 'PARCIAL'
        else:
            self.estado_pago = 'PENDIENTE'
        
        self.save(update_fields=['monto_cobrado', 'estado_pago'])

    def save(self, *args, **kwargs):
        # Lógica de autonumeración por año
        if not self.pk and not self.numero_guia:
            anio_actual = self.fecha_emision.year
            ultima = GuiaEntrega.objects.filter(
                fecha_emision__year=anio_actual
            ).order_by('numero_guia').last()
            
            if ultima and ultima.numero_guia.isdigit():
                nuevo = int(ultima.numero_guia) + 1
                self.numero_guia = str(nuevo).zfill(6)
            else:
                self.numero_guia = '000001'
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Guía #{self.numero_guia} ({self.fecha_emision.year}) - {self.cliente}"
    
    class Meta:
        verbose_name = "Guía de Entrega"
        verbose_name_plural = "Guías de Entrega"

# --- HISTORIAL DE PAGOS ---
class Pago(models.Model):
    guia = models.ForeignKey(GuiaEntrega, related_name='pagos', on_delete=models.CASCADE)
    fecha = models.DateField(default=timezone.now)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    comprobante_banco = models.CharField(max_length=100, blank=True, help_text="Código de operación o Yape")

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.guia.actualizar_estado_pago()
    
    def delete(self, *args, **kwargs):
        guia_ref = self.guia
        super().delete(*args, **kwargs)
        guia_ref.actualizar_estado_pago()

    def __str__(self):
        return f"Pago de {self.monto}"

# 4. DETALLE DE GUIA
class DetalleGuia(models.Model):
    guia = models.ForeignKey(GuiaEntrega, related_name='detalles', on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField()
    precio_aplicado = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    
    @property
    def total_linea(self):
        precio = self.precio_aplicado if self.precio_aplicado else 0
        return self.cantidad * precio

    def save(self, *args, **kwargs):
        if not self.precio_aplicado:
            self.precio_aplicado = self.producto.precio_unitario
        if not self.pk: 
            self.producto.stock_actual -= self.cantidad
            self.producto.save()
        super().save(*args, **kwargs)
        
        total = sum([d.total_linea for d in self.guia.detalles.all()])
        self.guia.total_venta = total
        self.guia.save()
        self.guia.actualizar_estado_pago()

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre}"

# --- MÓDULO DE FINANZAS Y PROVEEDORES ---

class Proveedor(models.Model):
    TIPOS = [
        ('INSUMOS', 'Proveedor de Insumos/Material'),
        ('SERVICIOS', 'Servicios (Luz, Agua, Internet)'),
        ('BANCO', 'Entidad Bancaria / Prestamista'),
        ('OTROS', 'Otros Gastos'),
    ]
    razon_social = models.CharField(max_length=150, verbose_name="Empresa / Nombre")
    tipo = models.CharField(max_length=20, choices=TIPOS, default='INSUMOS')
    ruc_dni = models.CharField(max_length=20, blank=True, verbose_name="RUC/DNI")
    telefono = models.CharField(max_length=20, blank=True)
    
    def __str__(self):
        return f"{self.razon_social} ({self.get_tipo_display()})"
    
    class Meta:
        verbose_name_plural = "Proveedores"

class Gasto(models.Model):
    CATEGORIAS = [
        ('SUMINISTRO', 'Compra de Material/Insumos'), 
        ('OPERATIVO', 'Gasto Operativo (Luz, Local, Personal)'), 
        ('DEUDA', 'Pago de Deuda/Préstamo'), 
    ]
    
    ESTADOS = [
        ('PENDIENTE', '⛔ Por Pagar (Deuda)'),
        ('PAGADO', '✅ Pagado'),
    ]

    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT)
    descripcion = models.CharField(max_length=200, help_text="Ej: Compra de 50 planchas, Recibo de Luz Agosto")
    categoria = models.CharField(max_length=20, choices=CATEGORIAS, default='SUMINISTRO')
    
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_emision = models.DateField(default=timezone.now, verbose_name="Fecha del Gasto")
    fecha_vencimiento = models.DateField(blank=True, null=True, verbose_name="Fecha Límite de Pago")
    
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')
    comprobante = models.CharField(max_length=50, blank=True, help_text="N° Factura o Boleta recibida")
    archivo_adjunto = models.FileField(upload_to='facturas_gastos/', blank=True, null=True, help_text="Foto o PDF de la factura")

    def esta_vencido(self):
        if self.estado == 'PENDIENTE' and self.fecha_vencimiento:
            return date.today() > self.fecha_vencimiento
        return False

    def __str__(self):
        return f"{self.descripcion} - S/. {self.monto}"

# --- NUEVO: CONTROL DE ASISTENCIA (ESTO ES LO QUE FALTABA) ---
class Asistencia(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Colaborador")
    fecha = models.DateField(default=timezone.now)
    hora_entrada = models.TimeField(blank=True, null=True)
    hora_salida = models.TimeField(blank=True, null=True)
    
    def horas_trabajadas(self):
        if self.hora_entrada and self.hora_salida:
            # Calculo básico de horas
            entrada = datetime.combine(date.today(), self.hora_entrada)
            salida = datetime.combine(date.today(), self.hora_salida)
            diferencia = salida - entrada
            total_segundos = diferencia.total_seconds()
            horas = total_segundos / 3600
            return round(horas, 2)
        return 0.00
    
    def __str__(self):
        return f"{self.usuario.username} - {self.fecha}"

    class Meta:
        verbose_name = "Registro de Asistencia"
        verbose_name_plural = "Control de Asistencias"
    
    class PerfilColaborador(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    tarifa_por_hora = models.DecimalField(max_digits=6, decimal_places=2, default=0.00, verbose_name="Tarifa x Hora (S/.)")
    celular = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"Perfil de {self.usuario.username}"

    class Meta:
        verbose_name = "Perfil de Colaborador"
        verbose_name_plural = "Perfiles de Colaboradores"