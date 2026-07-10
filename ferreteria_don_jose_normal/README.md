# Ferretería Don José — Django

Sistema responsive basado en el boceto entregado, optimizado para computador, tablet y celular.

## Funciones principales

### Clientes

- Catálogo con buscador y categorías.
- Diseño de ancho completo en computador.
- Carrito de compra.
- Inicio de sesión y registro de clientes.
- Cuenta personal con historial de pedidos.
- Retiro en tienda mediante código único.
- Pago al retirar.
- Pago con tarjeta en modo demostración.
- Comprobante imprimible y envío del código por WhatsApp.

### Don José

- Inicio de sesión desde la misma pantalla.
- Panel administrativo protegido.
- Gestión de productos, inventario y stock.
- Gestión de pedidos y estados.
- Visualización del código de retiro.
- Método y estado del pago.
- Descuento automático de stock.
- Exportación del inventario a CSV.

## Instalación

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

Linux o macOS:

```bash
source .venv/bin/activate
```

Luego ejecuta:

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

## Direcciones

- Catálogo: `http://127.0.0.1:8000/`
- Inicio de sesión: `http://127.0.0.1:8000/login/`
- Registro de clientes: `http://127.0.0.1:8000/registro/`
- Mi cuenta: `http://127.0.0.1:8000/cuenta/`
- Panel Don José: `http://127.0.0.1:8000/panel/`
- Administración Django: `http://127.0.0.1:8000/admin/`

## Usuarios de demostración

### Cliente

```text
Correo: cliente@demo.cl
Contraseña: Cliente123!
```

### Don José

```text
Usuario: 219370237
Contraseña: 1905
```

El sistema reconoce automáticamente el tipo de usuario:

- Los clientes son enviados a **Mi cuenta**.
- Don José es enviado al **panel administrativo**.

Para finalizar una compra, el cliente debe iniciar sesión. El carrito se conserva mientras inicia sesión o crea su cuenta.

## Pago con tarjeta

El pago incluido es una simulación para el prototipo y no realiza cobros bancarios reales.

Datos de prueba:

```text
Número: 4111 1111 1111 1111
Vencimiento: 12/30
CVV: 123
```

El sistema guarda únicamente los últimos cuatro dígitos de la tarjeta. Para producción se debe integrar Webpay, Mercado Pago, Flow u otra pasarela certificada.

## WhatsApp

Cambia el número en `ferreteria/settings.py`:

```python
FERRETERIA_WHATSAPP = "56912345678"
```

Usa el número sin `+`, espacios ni guiones.

## Formulario de productos simplificado

La pantalla para agregar y editar productos muestra primero solo los datos principales:

- Nombre del producto
- Categoría
- Precio de venta
- Cantidad disponible

La descripción, imagen y visibilidad quedaron dentro de **Opciones adicionales**, para que Don José pueda completar el inventario de forma más rápida y sin ver demasiados campos al mismo tiempo.


## Compra como invitado

El cliente puede agregar productos, seleccionar pago al retirar o tarjeta y generar su código de retiro sin iniciar sesión. El inicio de sesión queda como opción para consultar el historial de pedidos.

## Estados de preparación y aviso por WhatsApp

Los pedidos usan los estados `Pendiente`, `Pedido listo`, `Entregado` y `Cancelado`.
Los pagos con tarjeta quedan con el pago registrado como `Pagado`, pero el pedido comienza en `Pendiente` mientras se prepara.
Al seleccionar `Pedido listo` desde el panel, el sistema abre WhatsApp con el mensaje preparado para el teléfono del cliente: “Tu pedido está listo para retirar”. El envío final se confirma desde WhatsApp.


## IVA, boleta y factura

- Los precios de venta se consideran finales e incluyen IVA.
- El carrito muestra el monto neto, el IVA de 19% incluido y el total.
- El cliente puede solicitar boleta o factura.
- Para factura se solicitan RUT, razón social, giro, dirección y correo.
- El comprobante generado por el prototipo no reemplaza un DTE emitido ante el SII. Para emitir boletas o facturas tributarias válidas se requiere integrar un sistema de facturación electrónica autorizado.
