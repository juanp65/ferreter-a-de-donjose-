from datetime import timedelta

from django.utils import timezone

from .models import Pedido


def _eliminar_cancelados_vencidos():
    """
    Elimina pedidos cancelados que llevan 24 horas o más.

    Se ejecuta cuando Django prepara una página HTML. Por eso no requiere
    configurar tareas externas en Render.
    """
    limite = timezone.now() - timedelta(days=1)

    Pedido.objects.filter(
        estado='cancelado',
        actualizado_en__lte=limite,
    ).delete()


def carrito_resumen(request):
    _eliminar_cancelados_vencidos()

    carrito = request.session.get('carrito', {})
    cantidad = sum(int(valor) for valor in carrito.values())

    cancelados_count = Pedido.objects.filter(
        estado='cancelado',
    ).count()

    return {
        'carrito_cantidad': cantidad,
        'cancelados_count': cancelados_count,
    }
