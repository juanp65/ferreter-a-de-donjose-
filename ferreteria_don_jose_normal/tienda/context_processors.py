def carrito_resumen(request):
    carrito = request.session.get('carrito', {})
    cantidad = sum(int(valor) for valor in carrito.values())
    return {'carrito_cantidad': cantidad}
