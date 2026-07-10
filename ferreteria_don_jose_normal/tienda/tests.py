from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Categoria, Pedido, Producto


class AutenticacionTests(TestCase):
    def test_registro_crea_usuario_e_inicia_sesion(self):
        response = self.client.post(reverse('registro'), {
            'first_name': 'María González',
            'email': 'maria@example.com',
            'password1': 'ClaveSegura123!',
            'password2': 'ClaveSegura123!',
        })
        self.assertRedirects(response, reverse('cuenta'))
        usuario = get_user_model().objects.get(username='maria@example.com')
        self.assertEqual(usuario.email, 'maria@example.com')
        self.assertEqual(int(self.client.session['_auth_user_id']), usuario.id)

    def test_cliente_es_redirigido_a_su_cuenta_al_ingresar(self):
        usuario = get_user_model().objects.create_user(
            username='cliente@example.com',
            email='cliente@example.com',
            password='Cliente123!',
        )
        response = self.client.post(reverse('login'), {
            'username': usuario.username,
            'password': 'Cliente123!',
        })
        self.assertRedirects(response, reverse('cuenta'))

    def test_administrador_es_redirigido_al_panel(self):
        administrador = get_user_model().objects.create_user(
            username='219370237',
            password='1905',
            is_staff=True,
        )
        response = self.client.post(reverse('login'), {
            'username': administrador.username,
            'password': '1905',
        })
        self.assertRedirects(response, reverse('dashboard'))


class FlujoCompraTests(TestCase):
    def setUp(self):
        categoria = Categoria.objects.create(nombre='Herramientas')
        self.producto = Producto.objects.create(
            categoria=categoria,
            nombre='Martillo',
            precio=10000,
            stock=5,
        )
        self.usuario = get_user_model().objects.create_user(
            username='cliente@demo.cl',
            email='cliente@demo.cl',
            first_name='Cliente Demo',
            password='Cliente123!',
        )

    def _iniciar_sesion(self):
        self.client.login(username='cliente@demo.cl', password='Cliente123!')

    def _agregar_al_carrito(self):
        response = self.client.post(reverse('agregar_carrito', args=[self.producto.id]))
        self.assertEqual(response.status_code, 302)

    def test_invitado_puede_finalizar_pedido_sin_iniciar_sesion(self):
        self._agregar_al_carrito()
        response = self.client.post(reverse('crear_pedido'), {
            'cliente_nombre': 'Cliente Invitado',
            'cliente_telefono': '912345678',
            'metodo_pago': 'tienda',
            'observacion': '',
        })
        pedido = Pedido.objects.get()
        self.assertRedirects(response, reverse('pedido_exito', args=[pedido.id]))
        self.assertIsNone(pedido.usuario)
        self.assertTrue(pedido.codigo_retiro.startswith('DJ-'))
        self.assertContains(self.client.get(reverse('pedido_exito', args=[pedido.id])), pedido.codigo_retiro)

    def test_pedido_pago_en_tienda_genera_codigo_y_se_asocia_al_cliente(self):
        self._iniciar_sesion()
        self._agregar_al_carrito()
        response = self.client.post(reverse('crear_pedido'), {
            'cliente_nombre': 'Cliente Prueba',
            'cliente_telefono': '912345678',
            'metodo_pago': 'tienda',
            'observacion': '',
        })
        pedido = Pedido.objects.get()
        self.assertRedirects(response, reverse('pedido_exito', args=[pedido.id]))
        self.assertTrue(pedido.codigo_retiro.startswith('DJ-'))
        self.assertEqual(pedido.estado_pago, 'pendiente')
        self.assertEqual(pedido.estado, 'pendiente')
        self.assertEqual(pedido.usuario, self.usuario)

    def test_pago_tarjeta_no_guarda_datos_sensibles_y_confirma(self):
        self._iniciar_sesion()
        self._agregar_al_carrito()
        response = self.client.post(reverse('crear_pedido'), {
            'cliente_nombre': 'Cliente Tarjeta',
            'cliente_telefono': '912345678',
            'metodo_pago': 'tarjeta',
            'titular_tarjeta': 'CLIENTE TARJETA',
            'numero_tarjeta': '4111 1111 1111 1111',
            'vencimiento_tarjeta': '12/30',
            'cvv_tarjeta': '123',
            'observacion': '',
        })
        pedido = Pedido.objects.get()
        self.assertRedirects(response, reverse('pedido_exito', args=[pedido.id]))
        self.assertEqual(pedido.estado_pago, 'pagado')
        self.assertEqual(pedido.estado, 'pendiente')
        self.assertEqual(pedido.tarjeta_ultimos4, '1111')
        self.assertTrue(pedido.referencia_pago.startswith('DEMO-'))
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 4)

    def test_tarjeta_invalida_muestra_error(self):
        self._iniciar_sesion()
        self._agregar_al_carrito()
        response = self.client.post(reverse('crear_pedido'), {
            'cliente_nombre': 'Cliente Error',
            'cliente_telefono': '912345678',
            'metodo_pago': 'tarjeta',
            'titular_tarjeta': 'CLIENTE ERROR',
            'numero_tarjeta': '1234',
            'vencimiento_tarjeta': '01/20',
            'cvv_tarjeta': '1',
            'observacion': '',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'El número de tarjeta debe tener entre 13 y 19 dígitos.')
        self.assertEqual(Pedido.objects.count(), 0)

    def test_tarjeta_acepta_numero_numerico_de_19_digitos(self):
        self._agregar_al_carrito()
        response = self.client.post(reverse('crear_pedido'), {
            'cliente_nombre': 'Cliente 19 Dígitos',
            'cliente_telefono': '912345678',
            'metodo_pago': 'tarjeta',
            'titular_tarjeta': 'CLIENTE PRUEBA',
            'numero_tarjeta': '4000 0000 0000 0000 001',
            'vencimiento_tarjeta': '12/30',
            'cvv_tarjeta': '123',
            'observacion': '',
        })
        pedido = Pedido.objects.get()
        self.assertRedirects(response, reverse('pedido_exito', args=[pedido.id]))
        self.assertEqual(pedido.tarjeta_ultimos4, '0001')

    def test_numero_tarjeta_rechaza_letras(self):
        self._agregar_al_carrito()
        response = self.client.post(reverse('crear_pedido'), {
            'cliente_nombre': 'Cliente Letras',
            'cliente_telefono': '912345678',
            'metodo_pago': 'tarjeta',
            'titular_tarjeta': 'CLIENTE PRUEBA',
            'numero_tarjeta': '4111 ABCD 1111 1111',
            'vencimiento_tarjeta': '12/30',
            'cvv_tarjeta': '123',
            'observacion': '',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'El número de tarjeta solo puede contener números.')
        self.assertEqual(Pedido.objects.count(), 0)

    def test_boleta_calcula_neto_e_iva_incluido(self):
        self._agregar_al_carrito()
        response = self.client.post(reverse('crear_pedido'), {
            'cliente_nombre': 'Cliente Boleta',
            'cliente_telefono': '912345678',
            'tipo_documento': 'boleta',
            'metodo_pago': 'tienda',
            'observacion': '',
        })
        pedido = Pedido.objects.get()
        self.assertRedirects(response, reverse('pedido_exito', args=[pedido.id]))
        self.assertEqual(pedido.tipo_documento, 'boleta')
        self.assertEqual(pedido.monto_neto, 8403)
        self.assertEqual(pedido.monto_iva, 1597)
        self.assertEqual(pedido.monto_neto + pedido.monto_iva, pedido.total)

    def test_factura_exige_datos_tributarios(self):
        self._agregar_al_carrito()
        response = self.client.post(reverse('crear_pedido'), {
            'cliente_nombre': 'Cliente Factura',
            'cliente_telefono': '912345678',
            'tipo_documento': 'factura',
            'metodo_pago': 'tienda',
            'observacion': '',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ingresa el RUT para la factura.')
        self.assertContains(response, 'Ingresa la razón social.')
        self.assertEqual(Pedido.objects.count(), 0)

    def test_factura_guarda_datos_y_desglose_iva(self):
        self._agregar_al_carrito()
        response = self.client.post(reverse('crear_pedido'), {
            'cliente_nombre': 'Compras Empresa',
            'cliente_telefono': '912345678',
            'tipo_documento': 'factura',
            'factura_rut': '76.123.456-0',
            'factura_razon_social': 'Empresa de Prueba SpA',
            'factura_giro': 'Construcción',
            'factura_direccion': 'Avenida Prueba 123, Valdivia',
            'factura_email': 'facturas@empresa.cl',
            'metodo_pago': 'tienda',
            'observacion': '',
        })
        pedido = Pedido.objects.get()
        self.assertRedirects(response, reverse('pedido_exito', args=[pedido.id]))
        self.assertEqual(pedido.tipo_documento, 'factura')
        self.assertEqual(pedido.factura_rut, '76.123.456-0')
        self.assertEqual(pedido.factura_razon_social, 'Empresa de Prueba SpA')
        self.assertContains(self.client.get(reverse('pedido_exito', args=[pedido.id])), 'IVA (19%)')

    def test_invitado_no_puede_ver_un_pedido_ajeno(self):
        pedido = Pedido.objects.create(
            cliente_nombre='Invitado ajeno',
            cliente_telefono='911111111',
            total=10000,
        )
        response = self.client.get(reverse('pedido_exito', args=[pedido.id]))
        self.assertEqual(response.status_code, 404)

    def test_cliente_no_puede_ver_pedido_de_otro_usuario(self):
        otro = get_user_model().objects.create_user(
            username='otro@example.com',
            password='OtroCliente123!',
        )
        pedido = Pedido.objects.create(
            usuario=otro,
            cliente_nombre='Otro cliente',
            cliente_telefono='911111111',
            total=10000,
        )
        self._iniciar_sesion()
        response = self.client.get(reverse('pedido_exito', args=[pedido.id]))
        self.assertEqual(response.status_code, 404)


class EstadosPedidoTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_user(
            username='admin-estados',
            password='1905',
            is_staff=True,
        )
        categoria = Categoria.objects.create(nombre='Pruebas de estado')
        self.producto = Producto.objects.create(
            categoria=categoria,
            nombre='Producto de prueba',
            precio=5000,
            stock=10,
        )

    def _crear_pedido(self, metodo_pago='tienda'):
        pedido = Pedido.objects.create(
            cliente_nombre='Cliente Estado',
            cliente_telefono='912345678',
            metodo_pago=metodo_pago,
            estado_pago='pagado' if metodo_pago == 'tarjeta' else 'pendiente',
            total=5000,
        )
        pedido.items.create(producto=self.producto, cantidad=1, precio_unitario=5000)
        if metodo_pago == 'tarjeta':
            pedido.marcar_pagado()
        return pedido

    def test_tarjeta_queda_pagada_pero_pedido_pendiente(self):
        pedido = self._crear_pedido('tarjeta')
        pedido.refresh_from_db()
        self.assertEqual(pedido.estado, 'pendiente')
        self.assertEqual(pedido.estado_pago, 'pagado')
        self.assertTrue(pedido.stock_descontado)

    def test_panel_ofrece_pedido_listo_en_ambos_metodos(self):
        pedido_tienda = self._crear_pedido('tienda')
        pedido_tarjeta = self._crear_pedido('tarjeta')
        self.client.login(username='admin-estados', password='1905')
        response = self.client.get(reverse('pedidos_panel'))
        contenido = response.content.decode()
        for pedido in (pedido_tienda, pedido_tarjeta):
            selector = contenido.split(
                f'Cambiar estado del pedido {pedido.codigo_retiro}', 1
            )[1].split('</select>', 1)[0]
            self.assertIn('value="pendiente"', selector)
            self.assertIn('value="listo"', selector)
            self.assertIn('value="entregado"', selector)
            self.assertIn('value="cancelado"', selector)

    def test_marcar_listo_prepara_whatsapp_y_reserva_stock(self):
        pedido = self._crear_pedido('tienda')
        self.client.login(username='admin-estados', password='1905')
        response = self.client.post(
            reverse('cambiar_estado_pedido', args=[pedido.id]),
            {'estado': 'listo'},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('pedidos_panel'))
        pedido.refresh_from_db()
        self.producto.refresh_from_db()
        self.assertEqual(pedido.estado, 'listo')
        self.assertEqual(pedido.estado_pago, 'pendiente')
        self.assertEqual(self.producto.stock, 9)
        self.assertIn('whatsapp_listo_url', self.client.session)
        self.assertIn('tu%20pedido', self.client.session['whatsapp_listo_url'])

    def test_tarjeta_tambien_puede_marcarse_lista(self):
        pedido = self._crear_pedido('tarjeta')
        self.client.login(username='admin-estados', password='1905')
        response = self.client.post(
            reverse('cambiar_estado_pedido', args=[pedido.id]),
            {'estado': 'listo'},
        )
        self.assertRedirects(response, reverse('pedidos_panel'))
        pedido.refresh_from_db()
        self.assertEqual(pedido.estado, 'listo')
        self.assertEqual(pedido.estado_pago, 'pagado')

    def test_entregado_en_tienda_registra_pago(self):
        pedido = self._crear_pedido('tienda')
        self.client.login(username='admin-estados', password='1905')
        response = self.client.post(
            reverse('cambiar_estado_pedido', args=[pedido.id]),
            {'estado': 'entregado'},
        )
        self.assertRedirects(response, reverse('pedidos_panel'))
        pedido.refresh_from_db()
        self.assertEqual(pedido.estado, 'entregado')
        self.assertEqual(pedido.estado_pago, 'pagado')

