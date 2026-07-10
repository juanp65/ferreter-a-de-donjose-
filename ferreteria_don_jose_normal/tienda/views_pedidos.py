from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.http import require_POST

from .models import Pedido


@require_POST
@staff_member_required(login_url='login')
def eliminar_pedido_cancelado(request, pedido_id):
    """
    Elimina manualmente un pedido solamente si su estado es cancelado.
    """
    pedido = get_object_or_404(
        Pedido,
        pk=pedido_id,
    )

    siguiente = (
        request.POST.get('next')
        or reverse('pedidos_panel')
    )

    if pedido.estado != 'cancelado':
        messages.error(
            request,
            'Solo se pueden eliminar pedidos que estén cancelados.',
        )
        return redirect(siguiente)

    codigo = pedido.codigo_retiro

    pedido.delete()

    messages.success(
        request,
        f'Pedido {codigo} eliminado definitivamente.',
    )

    return redirect(siguiente)


@require_POST
@staff_member_required(login_url='login')
def eliminar_todos_cancelados(request):
    """
    Elimina manualmente todos los pedidos cancelados.
    """
    cancelados = Pedido.objects.filter(
        estado='cancelado',
    )

    cantidad = cancelados.count()

    if cantidad == 0:
        messages.info(
            request,
            'No hay pedidos cancelados para eliminar.',
        )
        return redirect('pedidos_panel')

    cancelados.delete()

    messages.success(
        request,
        (
            f'Se eliminaron definitivamente '
            f'{cantidad} pedido(s) cancelado(s).'
        ),
    )

    return redirect('pedidos_panel')
