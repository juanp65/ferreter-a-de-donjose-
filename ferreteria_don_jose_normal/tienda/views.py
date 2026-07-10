import csv
import re
import uuid
from decimal import Decimal, ROUND_HALF_UP
from urllib.parse import quote, urlparse

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction
from django.db.models import Q, Sum
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import InicioSesionForm, PedidoForm, ProductoForm, RegistroClienteForm
from .models import Categoria, ItemPedido, Pedido, Producto


def _desglosar_iva(total):
    """Desglosa un precio final que ya incluye IVA de 19%."""
    total = Decimal(total or 0)
    neto = (total / Decimal('1.19')).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
    return neto, total - neto


def _normalizar_numero_whatsapp(numero):
    """Convierte un teléfono escrito por el cliente a un formato útil para wa.me."""
    digitos = re.sub(r'\D', '', numero or '')
    if digitos.startswith('00'):
        digitos = digitos[2:]
    if digitos.startswith('56'):
        return digitos
    if len(digitos) == 9:
        return f'56{digitos}'
    if len(digitos) == 8:
        return f'569{digitos}'
    return digitos


def _whatsapp_pedido_listo(pedido):
    numero = _normalizar_numero_whatsapp(pedido.cliente_telefono)
    texto = quote(
        f'Hola {pedido.cliente_nombre}, tu pedido {pedido.codigo_retiro} está listo para retirar '
        'en Ferretería Don José.'
    )
    return f'https://wa.me/{numero}?text={texto}' if numero else ''


class InicioSesionView(LoginView):
    template_name = 'registration/login.html'
    authentication_form = InicioSesionForm
    redirect_authenticated_user = True

    def get_success_url(self):
        siguiente = self.get_redirect_url()
        if siguiente:
            ruta = urlparse(siguiente).path
            if ruta.startswith('/panel') and not self.request.user.is_staff:
                messages.error(self.request, 'Tu cuenta no tiene acceso al panel administrativo.')
                return reverse('cuenta')
            return siguiente
        if self.request.user.is_staff:
            return reverse('dashboard')
        return reverse('cuenta')


def registro(request):
    siguiente = request.POST.get('next') or request.GET.get('next') or ''
    if request.user.is_authenticated:
        if siguiente and url_has_allowed_host_and_scheme(
            url=siguiente,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            return redirect(siguiente)
        return redirect('dashboard' if request.user.is_staff else 'cuenta')

    form = RegistroClienteForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        usuario = form.save()
        login(request, usuario)
        messages.success(request, 'Tu cuenta fue creada correctamente.')
        if siguiente and url_has_allowed_host_and_scheme(
            url=siguiente,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            return redirect(siguiente)
        return redirect('cuenta')

    return render(request, 'registration/registro.html', {'form': form, 'next': siguiente})


@login_required
def cuenta(request):
    if request.user.is_staff:
        return redirect('dashboard')

    pedidos = Pedido.objects.filter(usuario=request.user).prefetch_related('items__producto')
    return render(request, 'tienda/cuenta.html', {'pedidos': pedidos})


def _items_carrito(request):
    carrito = request.session.get('carrito', {})
    productos = Producto.objects.filter(id__in=carrito.keys(), activo=True).select_related('categoria')
    items = []
    total = Decimal('0')

    for producto in productos:
        cantidad = max(1, int(carrito.get(str(producto.id), 1)))
        subtotal = producto.precio * cantidad
        items.append({'producto': producto, 'cantidad': cantidad, 'subtotal': subtotal})
        total += subtotal

    return items, total


def catalogo(request):
    productos = Producto.objects.filter(activo=True).select_related('categoria')
    categorias = Categoria.objects.all()
    q = request.GET.get('q', '').strip()
    categoria = request.GET.get('categoria', '').strip()

    if q:
        productos = productos.filter(Q(nombre__icontains=q) | Q(descripcion__icontains=q))
    if categoria:
        productos = productos.filter(categoria__slug=categoria)

    whatsapp_texto = quote('Hola, quisiera consultar por un producto de la Ferretería Don José.')
    whatsapp_url = f'https://wa.me/{settings.FERRETERIA_WHATSAPP}?text={whatsapp_texto}'

    return render(request, 'tienda/catalogo.html', {
        'productos': productos,
        'categorias': categorias,
        'q': q,
        'categoria_seleccionada': categoria,
        'whatsapp_url': whatsapp_url,
    })


@require_POST
def agregar_carrito(request, producto_id):
    producto = get_object_or_404(Producto, pk=producto_id, activo=True)
    if producto.stock <= 0:
        messages.error(request, 'Este producto no tiene stock disponible.')
        return redirect('catalogo')

    carrito = request.session.get('carrito', {})
    clave = str(producto.id)
    cantidad_actual = int(carrito.get(clave, 0))
    carrito[clave] = min(cantidad_actual + 1, producto.stock)
    request.session['carrito'] = carrito
    request.session.modified = True
    messages.success(request, f'{producto.nombre} fue agregado al carrito.')
    return redirect(request.POST.get('next') or 'catalogo')


def carrito(request):
    items, total = _items_carrito(request)
    neto, iva = _desglosar_iva(total)
    inicial = {}
    if request.user.is_authenticated:
        inicial['cliente_nombre'] = request.user.get_full_name() or request.user.first_name or request.user.username
        inicial['factura_email'] = request.user.email
    return render(request, 'tienda/carrito.html', {
        'items': items,
        'total': total,
        'neto': neto,
        'iva': iva,
        'form': PedidoForm(initial=inicial),
    })


@require_POST
def actualizar_carrito(request, producto_id):
    producto = get_object_or_404(Producto, pk=producto_id, activo=True)
    try:
        cantidad = int(request.POST.get('cantidad', 1))
    except (TypeError, ValueError):
        cantidad = 1

    carrito = request.session.get('carrito', {})
    clave = str(producto.id)
    if cantidad <= 0:
        carrito.pop(clave, None)
    else:
        carrito[clave] = min(cantidad, producto.stock)

    request.session['carrito'] = carrito
    request.session.modified = True
    return redirect('carrito')


@require_POST
def eliminar_carrito(request, producto_id):
    carrito = request.session.get('carrito', {})
    carrito.pop(str(producto_id), None)
    request.session['carrito'] = carrito
    request.session.modified = True
    return redirect('carrito')


@require_POST
@transaction.atomic
def crear_pedido(request):
    items, total = _items_carrito(request)
    form = PedidoForm(request.POST)

    if not items:
        messages.error(request, 'El carrito está vacío.')
        return redirect('catalogo')

    if not form.is_valid():
        neto, iva = _desglosar_iva(total)
        return render(request, 'tienda/carrito.html', {
            'items': items,
            'total': total,
            'neto': neto,
            'iva': iva,
            'form': form,
        })

    for item in items:
        if item['cantidad'] > item['producto'].stock:
            messages.error(request, f'No hay stock suficiente de {item["producto"].nombre}.')
            return redirect('carrito')

    metodo_pago = form.cleaned_data['metodo_pago']
    numero_tarjeta = form.cleaned_data.get('numero_tarjeta', '')

    pedido = Pedido.objects.create(
        usuario=request.user if request.user.is_authenticated else None,
        cliente_nombre=form.cleaned_data['cliente_nombre'],
        cliente_telefono=form.cleaned_data['cliente_telefono'],
        observacion=form.cleaned_data.get('observacion', ''),
        metodo_pago=metodo_pago,
        estado_pago='pagado' if metodo_pago == 'tarjeta' else 'pendiente',
        tarjeta_ultimos4=numero_tarjeta[-4:] if metodo_pago == 'tarjeta' else '',
        referencia_pago=(f'DEMO-{uuid.uuid4().hex[:12].upper()}' if metodo_pago == 'tarjeta' else ''),
        tipo_documento=form.cleaned_data['tipo_documento'],
        factura_rut=form.cleaned_data.get('factura_rut', ''),
        factura_razon_social=form.cleaned_data.get('factura_razon_social', ''),
        factura_giro=form.cleaned_data.get('factura_giro', ''),
        factura_direccion=form.cleaned_data.get('factura_direccion', ''),
        factura_email=form.cleaned_data.get('factura_email', ''),
        total=total,
    )
    ItemPedido.objects.bulk_create([
        ItemPedido(
            pedido=pedido,
            producto=item['producto'],
            cantidad=item['cantidad'],
            precio_unitario=item['producto'].precio,
        )
        for item in items
    ])

    # En el prototipo, el pago con tarjeta se aprueba de inmediato y reserva el stock,
    # pero el estado de preparación del pedido permanece en Pendiente.
    # Para producción, reemplaza esta simulación por Webpay, Mercado Pago o Flow.
    if metodo_pago == 'tarjeta':
        pedido.marcar_pagado()

    request.session['carrito'] = {}
    pedidos_sesion = request.session.get('pedidos_sesion', [])
    if pedido.id not in pedidos_sesion:
        pedidos_sesion.append(pedido.id)
    request.session['pedidos_sesion'] = pedidos_sesion[-20:]
    request.session['ultimo_pedido_id'] = pedido.id
    request.session.modified = True
    return redirect('pedido_exito', pedido_id=pedido.id)


def pedido_exito(request, pedido_id):
    pedido = get_object_or_404(Pedido.objects.prefetch_related('items__producto'), pk=pedido_id)
    pedidos_sesion = request.session.get('pedidos_sesion', [])
    acceso_por_sesion = pedido.id in pedidos_sesion or request.session.get('ultimo_pedido_id') == pedido.id
    acceso_por_usuario = request.user.is_authenticated and pedido.usuario_id == request.user.id
    acceso_administrador = request.user.is_authenticated and request.user.is_staff

    if not (acceso_por_sesion or acceso_por_usuario or acceso_administrador):
        raise Http404('Pedido no encontrado.')

    texto = quote(
        f'Hola, realicé el pedido {pedido.codigo_retiro} a nombre de {pedido.cliente_nombre}. '
        f'El total es ${pedido.total:,.0f}, el documento solicitado es {pedido.get_tipo_documento_display()} '
        f'y el método de pago es {pedido.get_metodo_pago_display()}.'.replace(',', '.')
    )
    whatsapp_url = f'https://wa.me/{settings.FERRETERIA_WHATSAPP}?text={texto}'
    return render(request, 'tienda/pedido_exito.html', {'pedido': pedido, 'whatsapp_url': whatsapp_url})


@staff_member_required(login_url='login')
def dashboard(request):
    productos = Producto.objects.select_related('categoria')
    q = request.GET.get('q', '').strip()
    categoria = request.GET.get('categoria', '').strip()

    if q:
        productos = productos.filter(Q(nombre__icontains=q) | Q(categoria__nombre__icontains=q))
    if categoria:
        productos = productos.filter(categoria__slug=categoria)

    hoy = timezone.localdate()
    ventas_hoy = Pedido.objects.filter(
        estado_pago='pagado',
        creado_en__date=hoy,
    ).exclude(estado='cancelado').aggregate(total=Sum('total'))['total'] or 0

    contexto = {
        'productos': productos,
        'categorias': Categoria.objects.all(),
        'categoria_seleccionada': categoria,
        'q': q,
        'total_productos': Producto.objects.filter(activo=True).count(),
        'ventas_hoy': ventas_hoy,
        'cantidad_ventas_hoy': Pedido.objects.filter(estado_pago='pagado', creado_en__date=hoy).exclude(estado='cancelado').count(),
        'pedidos_pendientes': Pedido.objects.filter(estado='pendiente').count(),
        'stock_bajo': Producto.objects.filter(activo=True, stock__lte=5).count(),
        'ultimos_pedidos': Pedido.objects.prefetch_related('items__producto')[:5],
    }
    return render(request, 'tienda/dashboard.html', contexto)


@staff_member_required(login_url='login')
def producto_crear(request):
    form = ProductoForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Producto creado correctamente.')
        return redirect('dashboard')
    return render(request, 'tienda/producto_form.html', {'form': form, 'titulo': 'Agregar producto'})


@staff_member_required(login_url='login')
def producto_editar(request, producto_id):
    producto = get_object_or_404(Producto, pk=producto_id)
    form = ProductoForm(request.POST or None, request.FILES or None, instance=producto)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Producto actualizado correctamente.')
        return redirect('dashboard')
    return render(request, 'tienda/producto_form.html', {'form': form, 'titulo': 'Editar producto', 'producto': producto})


@staff_member_required(login_url='login')
def pedidos_panel(request):
    estado = request.GET.get('estado', '').strip()
    con_mensaje = request.GET.get('con_mensaje', '').strip()
    pedidos = Pedido.objects.prefetch_related('items__producto')

    if estado:
        pedidos = pedidos.filter(estado=estado)
    if con_mensaje == 'si':
        pedidos = pedidos.exclude(observacion='')
    elif con_mensaje == 'no':
        pedidos = pedidos.filter(observacion='')

    mensajes_count = pedidos.exclude(observacion='').count()
    whatsapp_listo_url = request.session.pop('whatsapp_listo_url', '')
    whatsapp_listo_codigo = request.session.pop('whatsapp_listo_codigo', '')
    return render(request, 'tienda/pedidos_panel.html', {
        'pedidos': pedidos,
        'estado': estado,
        'con_mensaje': con_mensaje,
        'mensajes_count': mensajes_count,
        'estados_pedido': Pedido.ESTADOS,
        'whatsapp_listo_url': whatsapp_listo_url,
        'whatsapp_listo_codigo': whatsapp_listo_codigo,
    })


@require_POST
@staff_member_required(login_url='login')
def cambiar_estado_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    nuevo_estado = request.POST.get('estado')
    estados_validos = {valor for valor, _ in Pedido.ESTADOS}
    siguiente = request.POST.get('next') or reverse('pedidos_panel')

    if nuevo_estado not in estados_validos:
        messages.error(request, 'Estado no válido.')
        return redirect('pedidos_panel')

    try:
        if nuevo_estado == 'listo':
            pedido.marcar_listo()
            whatsapp_url = _whatsapp_pedido_listo(pedido)
            if whatsapp_url:
                request.session['whatsapp_listo_url'] = whatsapp_url
                request.session['whatsapp_listo_codigo'] = pedido.codigo_retiro
            messages.success(
                request,
                f'Pedido {pedido.codigo_retiro} marcado como listo. Abre WhatsApp para avisar al cliente.',
            )
        elif nuevo_estado == 'entregado':
            pedido.marcar_entregado()
            messages.success(request, f'Pedido {pedido.codigo_retiro} marcado como entregado.')
        elif nuevo_estado == 'cancelado':
            pedido.cancelar()
            messages.success(request, f'Pedido {pedido.codigo_retiro} cancelado.')
        else:
            pedido.marcar_pendiente()
            messages.success(request, f'Pedido {pedido.codigo_retiro} actualizado a Pendiente.')
    except ValueError as exc:
        messages.error(request, str(exc))

    return redirect(siguiente)


@staff_member_required(login_url='login')
def exportar_productos_csv(request):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="inventario_ferreteria.csv"'
    response.write('\ufeff')
    writer = csv.writer(response, delimiter=';')
    writer.writerow(['Producto', 'Categoría', 'Stock', 'Precio', 'Estado', 'Última actualización'])

    for producto in Producto.objects.select_related('categoria'):
        writer.writerow([
            producto.nombre,
            producto.categoria.nombre,
            producto.stock,
            producto.precio,
            'Disponible' if producto.disponible else 'Sin stock / inactivo',
            timezone.localtime(producto.actualizado_en).strftime('%d/%m/%Y %H:%M'),
        ])
    return response
