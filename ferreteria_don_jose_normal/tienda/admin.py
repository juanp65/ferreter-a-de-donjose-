from django.contrib import admin
from .models import Categoria, ItemPedido, Pedido, Producto


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('nombre',)}
    search_fields = ('nombre',)


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'precio', 'stock', 'activo', 'actualizado_en')
    list_filter = ('categoria', 'activo')
    search_fields = ('nombre', 'descripcion')


class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 0
    readonly_fields = ('precio_unitario',)


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ('codigo_retiro', 'usuario', 'cliente_nombre', 'cliente_telefono', 'tipo_documento', 'metodo_pago', 'estado_pago', 'estado', 'total', 'creado_en')
    list_filter = ('estado', 'tipo_documento', 'metodo_pago', 'estado_pago', 'creado_en')
    search_fields = ('codigo_retiro', 'usuario__username', 'usuario__email', 'cliente_nombre', 'cliente_telefono', 'referencia_pago', 'factura_rut', 'factura_razon_social')
    inlines = [ItemPedidoInline]
