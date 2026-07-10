from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from . import views_stock


urlpatterns = [
    path(
        "",
        views.catalogo,
        name="catalogo",
    ),

    path(
        "carrito/",
        views.carrito,
        name="carrito",
    ),

    path(
        "carrito/agregar/<int:producto_id>/",
        views.agregar_carrito,
        name="agregar_carrito",
    ),

    path(
        "carrito/actualizar/<int:producto_id>/",
        views.actualizar_carrito,
        name="actualizar_carrito",
    ),

    path(
        "carrito/eliminar/<int:producto_id>/",
        views.eliminar_carrito,
        name="eliminar_carrito",
    ),

    path(
        "pedido/crear/",
        views.crear_pedido,
        name="crear_pedido",
    ),

    path(
        "pedido/exito/<int:pedido_id>/",
        views.pedido_exito,
        name="pedido_exito",
    ),

    path(
        "login/",
        views.InicioSesionView.as_view(),
        name="login",
    ),

    path(
        "registro/",
        views.registro,
        name="registro",
    ),

    path(
        "cuenta/",
        views.cuenta,
        name="cuenta",
    ),

    path(
        "logout/",
        auth_views.LogoutView.as_view(),
        name="logout",
    ),

    path(
        "panel/",
        views.dashboard,
        name="dashboard",
    ),

    path(
        "panel/productos/nuevo/",
        views.producto_crear,
        name="producto_crear",
    ),

    path(
        "panel/productos/<int:producto_id>/editar/",
        views.producto_editar,
        name="producto_editar",
    ),

    path(
        "panel/productos/importar-stock/",
        views_stock.importar_stock,
        name="importar_stock",
    ),

    path(
        "panel/productos/exportar/",
        views.exportar_productos_csv,
        name="exportar_productos_csv",
    ),

    path(
        "panel/pedidos/",
        views.pedidos_panel,
        name="pedidos_panel",
    ),

    path(
        "panel/pedidos/<int:pedido_id>/estado/",
        views.cambiar_estado_pedido,
        name="cambiar_estado_pedido",
    ),

    path(
        "panel/pedidos/<int:pedido_id>/eliminar/",
        views.eliminar_pedido_cancelado,
        name="eliminar_pedido_cancelado",
    ),

    path(
        "panel/pedidos/eliminar-cancelados/",
        views.eliminar_todos_cancelados,
        name="eliminar_todos_cancelados",
    ),
]
