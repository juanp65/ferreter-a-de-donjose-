import uuid
from decimal import Decimal, ROUND_HALF_UP

from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import PedidoForm
from .models import ItemPedido, Pedido, Producto


def _desglosar_iva(total):
    """
    Calcula el neto y el IVA incluido en el total.
    """

    total = Decimal(total or 0)

    neto = (
        total / Decimal("1.19")
    ).quantize(
        Decimal("1"),
        rounding=ROUND_HALF_UP,
    )

    iva = total - neto

    return neto, iva


def _carrito_sesion(request):
    """
    Obtiene el carrito y elimina valores inválidos.
    """

    carrito = request.session.get(
        "carrito",
        {},
    )

    carrito_limpio = {}

    for producto_id, cantidad in carrito.items():

        try:
            producto_id = str(
                int(producto_id)
            )

            cantidad = int(cantidad)

        except (TypeError, ValueError):
            continue

        if cantidad > 0:
            carrito_limpio[
                producto_id
            ] = cantidad

    if carrito_limpio != carrito:

        request.session[
            "carrito"
        ] = carrito_limpio

        request.session.modified = True

    return carrito_limpio


def _items_carrito(request):
    """
    Construye los productos reservados en el carrito.

    producto.stock:
        unidades que continúan disponibles.

    cantidad:
        unidades reservadas por este carrito.
    """

    carrito = _carrito_sesion(request)

    productos = (
        Producto.objects
        .filter(id__in=carrito.keys())
        .select_related("categoria")
    )

    productos_por_id = {
        str(producto.id): producto
        for producto in productos
    }

    items = []
    total = Decimal("0")

    for producto_id, cantidad in carrito.items():

        producto = productos_por_id.get(
            producto_id
        )

        if producto is None:
            continue

        subtotal = (
            producto.precio * cantidad
        )

        items.append(
            {
                "producto": producto,
                "cantidad": cantidad,

                # Cantidad reservada actualmente
                # más las unidades todavía disponibles.
                "max_cantidad": (
                    cantidad + producto.stock
                ),

                "subtotal": subtotal,
            }
        )

        total += subtotal

    return items, total


@require_POST
@transaction.atomic
def agregar_carrito(request, producto_id):
    """
    Agrega una unidad al carrito y la descuenta
    inmediatamente del stock.
    """

    producto = get_object_or_404(
        Producto.objects.select_for_update(),
        pk=producto_id,
        activo=True,
    )

    if producto.stock <= 0:

        messages.error(
            request,
            "Este producto ya no tiene stock disponible.",
        )

        return redirect(
            request.POST.get("next")
            or "catalogo"
        )

    # Se reserva una unidad inmediatamente.
    producto.stock -= 1

    producto.save(
        update_fields=[
            "stock",
            "actualizado_en",
        ]
    )

    carrito = _carrito_sesion(request)

    clave = str(producto.id)

    cantidad_actual = int(
        carrito.get(clave, 0)
    )

    carrito[clave] = (
        cantidad_actual + 1
    )

    request.session[
        "carrito"
    ] = carrito

    request.session.modified = True

    messages.success(
        request,
        (
            f"{producto.nombre} fue agregado "
            "y quedó reservado."
        ),
    )

    return redirect(
        request.POST.get("next")
        or "catalogo"
    )


def carrito(request):
    """
    Muestra el carrito y el formulario del pedido.
    """

    items, total = _items_carrito(
        request
    )

    neto, iva = _desglosar_iva(
        total
    )

    inicial = {}

    if request.user.is_authenticated:

        inicial["cliente_nombre"] = (
            request.user.get_full_name()
            or request.user.first_name
            or request.user.username
        )

        inicial["factura_email"] = (
            request.user.email
        )

    return render(
        request,
        "tienda/carrito.html",
        {
            "items": items,
            "total": total,
            "neto": neto,
            "iva": iva,
            "form": PedidoForm(
                initial=inicial
            ),
        },
    )


@require_POST
@transaction.atomic
def actualizar_carrito(request, producto_id):
    """
    Actualiza automáticamente la cantidad reservada.

    Si aumenta:
        descuenta la diferencia.

    Si disminuye:
        devuelve la diferencia.

    Si llega a cero:
        elimina el producto y devuelve todo.
    """

    producto = get_object_or_404(
        Producto.objects.select_for_update(),
        pk=producto_id,
    )

    carrito = _carrito_sesion(
        request
    )

    clave = str(producto.id)

    cantidad_actual = int(
        carrito.get(clave, 0)
    )

    if cantidad_actual <= 0:

        messages.error(
            request,
            "El producto ya no está en el carrito.",
        )

        return redirect(
            "carrito"
        )

    try:
        cantidad_nueva = int(
            request.POST.get(
                "cantidad",
                cantidad_actual,
            )
        )

    except (TypeError, ValueError):
        cantidad_nueva = cantidad_actual

    cantidad_nueva = max(
        0,
        cantidad_nueva,
    )

    diferencia = (
        cantidad_nueva
        - cantidad_actual
    )

    # El cliente quiere aumentar la cantidad.
    if diferencia > 0:

        if producto.stock < diferencia:

            messages.error(
                request,
                (
                    f"Solo quedan {producto.stock} "
                    f"unidad(es) adicionales de "
                    f"{producto.nombre}."
                ),
            )

            return redirect(
                "carrito"
            )

        producto.stock -= diferencia

        producto.save(
            update_fields=[
                "stock",
                "actualizado_en",
            ]
        )

    # El cliente quiere disminuir la cantidad.
    elif diferencia < 0:

        unidades_a_devolver = abs(
            diferencia
        )

        producto.stock += (
            unidades_a_devolver
        )

        producto.save(
            update_fields=[
                "stock",
                "actualizado_en",
            ]
        )

    # Si llega a cero, se elimina del carrito.
    if cantidad_nueva == 0:

        carrito.pop(
            clave,
            None,
        )

        messages.success(
            request,
            (
                f"{producto.nombre} fue eliminado "
                "y el stock fue repuesto."
            ),
        )

    else:

        carrito[
            clave
        ] = cantidad_nueva

    request.session[
        "carrito"
    ] = carrito

    request.session.modified = True

    return redirect(
        "carrito"
    )


@require_POST
@transaction.atomic
def eliminar_carrito(request, producto_id):
    """
    Elimina el producto y devuelve automáticamente
    todas sus unidades al stock.
    """

    producto = get_object_or_404(
        Producto.objects.select_for_update(),
        pk=producto_id,
    )

    carrito = _carrito_sesion(
        request
    )

    clave = str(producto.id)

    cantidad = int(
        carrito.pop(clave, 0)
    )

    if cantidad > 0:

        producto.stock += cantidad

        producto.save(
            update_fields=[
                "stock",
                "actualizado_en",
            ]
        )

        messages.success(
            request,
            (
                f"{producto.nombre} fue eliminado. "
                f"Se devolvieron {cantidad} "
                "unidad(es) al stock."
            ),
        )

    request.session[
        "carrito"
    ] = carrito

    request.session.modified = True

    return redirect(
        "carrito"
    )


@require_POST
@transaction.atomic
def crear_pedido(request):
    """
    Convierte la reserva del carrito en un pedido.

    El stock ya fue descontado cuando los productos
    fueron agregados, por lo que no se vuelve a descontar.
    """

    items, total = _items_carrito(
        request
    )

    form = PedidoForm(
        request.POST
    )

    if not items:

        messages.error(
            request,
            "El carrito está vacío.",
        )

        return redirect(
            "catalogo"
        )

    if not form.is_valid():

        neto, iva = _desglosar_iva(
            total
        )

        return render(
            request,
            "tienda/carrito.html",
            {
                "items": items,
                "total": total,
                "neto": neto,
                "iva": iva,
                "form": form,
            },
        )

    metodo_pago = form.cleaned_data[
        "metodo_pago"
    ]

    numero_tarjeta = (
        form.cleaned_data.get(
            "numero_tarjeta",
            "",
        )
    )

    pedido = Pedido.objects.create(
        usuario=(
            request.user
            if request.user.is_authenticated
            else None
        ),

        cliente_nombre=(
            form.cleaned_data[
                "cliente_nombre"
            ]
        ),

        cliente_telefono=(
            form.cleaned_data[
                "cliente_telefono"
            ]
        ),

        observacion=(
            form.cleaned_data.get(
                "observacion",
                "",
            )
        ),

        estado="pendiente",

        metodo_pago=metodo_pago,

        estado_pago=(
            "pagado"
            if metodo_pago == "tarjeta"
            else "pendiente"
        ),

        tarjeta_ultimos4=(
            numero_tarjeta[-4:]
            if metodo_pago == "tarjeta"
            else ""
        ),

        referencia_pago=(
            f"DEMO-{uuid.uuid4().hex[:12].upper()}"
            if metodo_pago == "tarjeta"
            else ""
        ),

        tipo_documento=(
            form.cleaned_data[
                "tipo_documento"
            ]
        ),

        factura_rut=(
            form.cleaned_data.get(
                "factura_rut",
                "",
            )
        ),

        factura_razon_social=(
            form.cleaned_data.get(
                "factura_razon_social",
                "",
            )
        ),

        factura_giro=(
            form.cleaned_data.get(
                "factura_giro",
                "",
            )
        ),

        factura_direccion=(
            form.cleaned_data.get(
                "factura_direccion",
                "",
            )
        ),

        factura_email=(
            form.cleaned_data.get(
                "factura_email",
                "",
            )
        ),

        total=total,

        # El inventario ya fue reservado.
        stock_descontado=True,
    )

    ItemPedido.objects.bulk_create(
        [
            ItemPedido(
                pedido=pedido,
                producto=item[
                    "producto"
                ],
                cantidad=item[
                    "cantidad"
                ],
                precio_unitario=item[
                    "producto"
                ].precio,
            )
            for item in items
        ]
    )

    # Se limpia el carrito sin devolver stock,
    # porque ahora pertenece al pedido.
    request.session[
        "carrito"
    ] = {}

    pedidos_sesion = (
        request.session.get(
            "pedidos_sesion",
            [],
        )
    )

    if pedido.id not in pedidos_sesion:
        pedidos_sesion.append(
            pedido.id
        )

    request.session[
        "pedidos_sesion"
    ] = pedidos_sesion[-20:]

    request.session[
        "ultimo_pedido_id"
    ] = pedido.id

    request.session.modified = True

    return redirect(
        "pedido_exito",
        pedido_id=pedido.id,
    )
