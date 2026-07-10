from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from .models import Pedido


@require_POST
@staff_member_required(login_url="login")
def eliminar_pedido_cancelado(request, pedido_id):
    """
    Elimina un pedido individual solamente cuando está cancelado.
    """

    pedido = get_object_or_404(
        Pedido,
        pk=pedido_id,
    )

    if pedido.estado != "cancelado":
        messages.error(
            request,
            "Solo se pueden eliminar pedidos cancelados.",
        )

        return redirect("pedidos_panel")

    codigo = pedido.codigo_retiro

    pedido.delete()

    messages.success(
        request,
        f"El pedido {codigo} fue eliminado definitivamente.",
    )

    return redirect("pedidos_panel")


@require_POST
@staff_member_required(login_url="login")
def eliminar_todos_cancelados(request):
    """
    Elimina todos los pedidos cuyo estado sea cancelado.
    """

    pedidos_cancelados = Pedido.objects.filter(
        estado="cancelado",
    )

    cantidad = pedidos_cancelados.count()

    if cantidad == 0:
        messages.info(
            request,
            "No hay pedidos cancelados para eliminar.",
        )

        return redirect("pedidos_panel")

    pedidos_cancelados.delete()

    messages.success(
        request,
        (
            f"Se eliminaron definitivamente "
            f"{cantidad} pedido(s) cancelado(s)."
        ),
    )

    return redirect("pedidos_panel")
