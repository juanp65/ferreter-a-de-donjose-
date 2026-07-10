from decimal import Decimal, ROUND_HALF_UP
import uuid
from django.conf import settings
from django.db import models, transaction
from django.utils import timezone
from django.utils.text import slugify


def generar_codigo_retiro():
    """Genera un código corto, legible y prácticamente único para retirar en tienda."""
    fecha = timezone.localdate().strftime('%y%m%d')
    aleatorio = uuid.uuid4().hex[:6].upper()
    return f'DJ-{fecha}-{aleatorio}'


class Categoria(models.Model):
    nombre = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=90, unique=True, blank=True)

    class Meta:
        ordering = ['nombre']
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name='productos')
    nombre = models.CharField(max_length=120)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=0)
    stock = models.PositiveIntegerField(default=0)
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)
    activo = models.BooleanField(default=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nombre']

    @property
    def disponible(self):
        return self.activo and self.stock > 0

    def __str__(self):
        return self.nombre


class Pedido(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pedidos',
        verbose_name='Cliente registrado',
    )
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('listo', 'Pedido listo'),
        ('entregado', 'Entregado'),
        ('cancelado', 'Cancelado'),
    ]
    METODOS_PAGO = [
        ('tienda', 'Pagar al retirar'),
        ('tarjeta', 'Tarjeta'),
    ]
    ESTADOS_PAGO = [
        ('pendiente', 'Pendiente'),
        ('pagado', 'Pagado'),
        ('rechazado', 'Rechazado'),
    ]
    TIPOS_DOCUMENTO = [
        ('boleta', 'Boleta'),
        ('factura', 'Factura'),
    ]

    codigo_retiro = models.CharField(
        max_length=20,
        unique=True,
        default=generar_codigo_retiro,
        editable=False,
    )
    cliente_nombre = models.CharField(max_length=120)
    cliente_telefono = models.CharField(max_length=30)
    observacion = models.TextField(blank=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    metodo_pago = models.CharField(max_length=20, choices=METODOS_PAGO, default='tienda')
    estado_pago = models.CharField(max_length=20, choices=ESTADOS_PAGO, default='pendiente')
    tarjeta_ultimos4 = models.CharField(max_length=4, blank=True)
    referencia_pago = models.CharField(max_length=40, blank=True)
    tipo_documento = models.CharField(max_length=20, choices=TIPOS_DOCUMENTO, default='boleta')
    factura_rut = models.CharField(max_length=20, blank=True)
    factura_razon_social = models.CharField(max_length=160, blank=True)
    factura_giro = models.CharField(max_length=160, blank=True)
    factura_direccion = models.CharField(max_length=220, blank=True)
    factura_email = models.EmailField(blank=True)
    total = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    stock_descontado = models.BooleanField(default=False)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-creado_en']

    def __str__(self):
        return f'{self.codigo_retiro} - {self.cliente_nombre}'

    @property
    def monto_neto(self):
        """Monto neto cuando el precio final ya incluye IVA."""
        total = Decimal(self.total or 0)
        return (total / Decimal('1.19')).quantize(Decimal('1'), rounding=ROUND_HALF_UP)

    @property
    def monto_iva(self):
        """IVA incluido en el total, calculado con una tasa de 19%."""
        return Decimal(self.total or 0) - self.monto_neto

    @transaction.atomic
    def reservar_stock(self):
        """Descuenta el stock una sola vez para reservar los productos del pedido."""
        if self.stock_descontado:
            return

        items = list(self.items.select_related('producto').select_for_update())
        for item in items:
            if item.producto.stock < item.cantidad:
                raise ValueError(f'Stock insuficiente para {item.producto.nombre}.')

        for item in items:
            producto = item.producto
            producto.stock -= item.cantidad
            producto.save(update_fields=['stock', 'actualizado_en'])

        self.stock_descontado = True
        self.save(update_fields=['stock_descontado', 'actualizado_en'])

    @transaction.atomic
    def liberar_stock(self):
        """Repone el stock cuando una reserva se cancela o vuelve a pendiente."""
        if not self.stock_descontado:
            return

        items = list(self.items.select_related('producto').select_for_update())
        for item in items:
            producto = item.producto
            producto.stock += item.cantidad
            producto.save(update_fields=['stock', 'actualizado_en'])

        self.stock_descontado = False
        self.save(update_fields=['stock_descontado', 'actualizado_en'])

    @transaction.atomic
    def marcar_pagado(self):
        """Registra el pago y reserva el stock, sin cambiar el estado de preparación."""
        self.reservar_stock()
        self.estado_pago = 'pagado'
        self.save(update_fields=['estado_pago', 'actualizado_en'])

    @transaction.atomic
    def marcar_listo(self):
        """Marca el pedido como listo para retirar y reserva los productos."""
        self.reservar_stock()
        self.estado = 'listo'
        self.save(update_fields=['estado', 'actualizado_en'])

    @transaction.atomic
    def marcar_pendiente(self):
        """Devuelve el pedido a pendiente; libera stock solo si aún no está pagado."""
        if self.metodo_pago == 'tienda' and self.estado_pago != 'pagado':
            self.liberar_stock()
        self.estado = 'pendiente'
        self.save(update_fields=['estado', 'actualizado_en'])

    @transaction.atomic
    def marcar_entregado(self):
        """Entrega el pedido, reserva stock y registra el pago al retirar."""
        self.reservar_stock()
        if self.metodo_pago == 'tienda':
            self.estado_pago = 'pagado'
        self.estado = 'entregado'
        self.save(update_fields=['estado', 'estado_pago', 'actualizado_en'])

    @transaction.atomic
    def cancelar(self):
        """Cancela el pedido y repone el stock si estaba reservado."""
        self.liberar_stock()
        self.estado = 'cancelado'
        self.save(update_fields=['estado', 'actualizado_en'])

    # Se conserva como alias para compatibilidad con código anterior.
    def confirmar(self):
        self.marcar_pagado()



class ItemPedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=0)

    @property
    def subtotal(self):
        return Decimal(self.cantidad) * self.precio_unitario

    def __str__(self):
        return f'{self.cantidad} x {self.producto.nombre}'
