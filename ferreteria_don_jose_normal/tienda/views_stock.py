import json
import re
import unicodedata
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction
from django.shortcuts import redirect, render

from .models import Categoria, Producto


def _normalizar_nombre(valor):
    """
    Normaliza nombres para comparar productos sin considerar:

    - mayúsculas;
    - minúsculas;
    - tildes;
    - espacios repetidos;
    - símbolos.
    """

    texto = unicodedata.normalize(
        "NFD",
        str(valor or ""),
    )

    texto = "".join(
        caracter
        for caracter in texto
        if unicodedata.category(caracter) != "Mn"
    )

    texto = texto.lower().strip()

    texto = re.sub(
        r"[^a-z0-9]+",
        " ",
        texto,
    )

    return re.sub(
        r"\s+",
        " ",
        texto,
    ).strip()


def _entero_no_negativo(valor):
    """
    Convierte el stock a número entero y evita cantidades negativas.
    """

    try:
        numero = int(
            str(valor).strip()
        )

    except (TypeError, ValueError):
        raise ValueError(
            "El stock debe ser un número entero."
        )

    if numero < 0:
        raise ValueError(
            "El stock no puede ser negativo."
        )

    return numero


def _precio_opcional(valor):
    """
    Convierte el precio leído desde la fotografía.

    Un precio vacío significa:
    - conservar el precio actual, cuando se actualiza;
    - pedir el precio, cuando el producto es nuevo.
    """

    texto = str(valor or "").strip()

    if not texto:
        return None

    texto = (
        texto
        .replace("$", "")
        .replace(" ", "")
    )

    # Permite formatos como:
    # 12.990
    # 12990
    # 12.990,00

    if "," in texto:
        texto = (
            texto
            .replace(".", "")
            .replace(",", ".")
        )

    else:
        texto = texto.replace(".", "")

    try:
        precio = Decimal(texto)

    except InvalidOperation:
        raise ValueError(
            "El precio no es válido."
        )

    if precio < 0:
        raise ValueError(
            "El precio no puede ser negativo."
        )

    return precio.quantize(
        Decimal("1")
    )


@staff_member_required(login_url="login")
def importar_stock(request):
    """
    Importa las filas revisadas por Don José.

    El OCR ocurre en el navegador mediante Tesseract.js.
    Django solamente recibe las filas después de que el usuario
    revisa y confirma la información.
    """

    categorias = (
        Categoria.objects
        .all()
        .order_by("nombre")
    )

    productos = (
        Producto.objects
        .select_related("categoria")
        .order_by("nombre")
    )

    if request.method == "POST":

        datos_crudos = (
            request.POST
            .get("filas_json", "")
            .strip()
        )

        try:
            filas = json.loads(
                datos_crudos
            )

        except (
            TypeError,
            json.JSONDecodeError,
        ):
            messages.error(
                request,
                (
                    "No se pudo leer la tabla de importación. "
                    "Vuelve a procesar la fotografía."
                ),
            )

            return redirect(
                "importar_stock"
            )

        if (
            not isinstance(filas, list)
            or not filas
        ):
            messages.error(
                request,
                "No hay filas para importar.",
            )

            return redirect(
                "importar_stock"
            )

        actualizados = 0
        creados = 0
        ignorados = 0
        errores = []

        with transaction.atomic():

            categoria_default, _ = (
                Categoria.objects.get_or_create(
                    nombre="Sin categoría",
                    defaults={
                        "slug": "sin-categoria",
                    },
                )
            )

            productos_actuales = list(
                Producto.objects
                .select_related("categoria")
                .select_for_update()
            )

            por_id = {
                producto.id: producto
                for producto in productos_actuales
            }

            por_nombre = {
                _normalizar_nombre(
                    producto.nombre
                ): producto
                for producto in productos_actuales
            }

            for indice, fila in enumerate(
                filas,
                start=1,
            ):

                if not isinstance(fila, dict):
                    errores.append(
                        (
                            f"Fila {indice}: "
                            "formato no válido."
                        )
                    )

                    continue

                accion = (
                    str(
                        fila.get(
                            "accion",
                            "ignorar",
                        )
                    )
                    .strip()
                    .lower()
                )

                nombre = (
                    str(
                        fila.get(
                            "nombre",
                            "",
                        )
                    )
                    .strip()
                )

                if accion == "ignorar":
                    ignorados += 1
                    continue

                if not nombre:
                    errores.append(
                        (
                            f"Fila {indice}: "
                            "falta el nombre del producto."
                        )
                    )

                    continue

                try:
                    stock = _entero_no_negativo(
                        fila.get("stock")
                    )

                    precio = _precio_opcional(
                        fila.get("precio")
                    )

                except ValueError as error:
                    errores.append(
                        (
                            f"Fila {indice} "
                            f"({nombre}): "
                            f"{error}"
                        )
                    )

                    continue

                nombre_normalizado = (
                    _normalizar_nombre(nombre)
                )

                producto = None

                producto_id = fila.get(
                    "producto_id"
                )

                try:
                    producto_id = (
                        int(producto_id)
                        if producto_id
                        else None
                    )

                except (
                    TypeError,
                    ValueError,
                ):
                    producto_id = None

                if producto_id:
                    producto = por_id.get(
                        producto_id
                    )

                # Segunda protección contra duplicados.
                #
                # Aunque una fila venga marcada como "crear",
                # si el nombre normalizado coincide exactamente,
                # se actualiza el producto existente.

                if producto is None:
                    producto = por_nombre.get(
                        nombre_normalizado
                    )

                if (
                    accion == "actualizar"
                    or producto is not None
                ):

                    if producto is None:
                        errores.append(
                            (
                                f"Fila {indice} "
                                f"({nombre}): selecciona "
                                "el producto existente que "
                                "deseas actualizar."
                            )
                        )

                        continue

                    producto.stock = stock

                    # Precio vacío:
                    # conserva el precio actual.

                    if precio is not None:
                        producto.precio = precio

                    producto.save()

                    actualizados += 1

                    por_nombre[
                        _normalizar_nombre(
                            producto.nombre
                        )
                    ] = producto

                    continue

                if accion != "crear":
                    errores.append(
                        (
                            f"Fila {indice} "
                            f"({nombre}): "
                            "acción desconocida."
                        )
                    )

                    continue

                if precio is None:
                    errores.append(
                        (
                            f"Fila {indice} "
                            f"({nombre}): agrega un "
                            "precio para crear el "
                            "producto nuevo."
                        )
                    )

                    continue

                categoria = categoria_default

                categoria_id = fila.get(
                    "categoria_id"
                )

                if categoria_id:
                    try:
                        categoria = (
                            Categoria.objects.get(
                                pk=int(
                                    categoria_id
                                )
                            )
                        )

                    except (
                        Categoria.DoesNotExist,
                        TypeError,
                        ValueError,
                    ):
                        categoria = (
                            categoria_default
                        )

                producto = (
                    Producto.objects.create(
                        nombre=nombre,
                        categoria=categoria,
                        descripcion=(
                            "Producto agregado desde "
                            "importación de stock."
                        ),
                        precio=precio,
                        stock=stock,
                        activo=True,
                    )
                )

                por_id[
                    producto.id
                ] = producto

                por_nombre[
                    nombre_normalizado
                ] = producto

                creados += 1

        if actualizados or creados:
            messages.success(
                request,
                (
                    "Importación completada: "
                    f"{actualizados} actualizado(s), "
                    f"{creados} nuevo(s) y "
                    f"{ignorados} ignorado(s)."
                ),
            )

        elif ignorados:
            messages.info(
                request,
                (
                    "No se realizaron cambios. "
                    f"Se ignoraron {ignorados} fila(s)."
                ),
            )

        if errores:
            resumen = " ".join(
                errores[:5]
            )

            if len(errores) > 5:
                resumen += (
                    f" Además, hay "
                    f"{len(errores) - 5} "
                    "error(es) más."
                )

            messages.warning(
                request,
                resumen,
            )

        return redirect(
            "dashboard"
        )

    productos_json = [
        {
            "id": producto.id,
            "nombre": producto.nombre,
            "stock": producto.stock,
            "precio": int(
                producto.precio
            ),
            "categoria_id": (
                producto.categoria_id
            ),
            "categoria": (
                producto.categoria.nombre
            ),
        }
        for producto in productos
    ]

    categorias_json = [
        {
            "id": categoria.id,
            "nombre": categoria.nombre,
        }
        for categoria in categorias
    ]

    return render(
        request,
        "tienda/importar_stock.html",
        {
            "productos_json": (
                productos_json
            ),
            "categorias_json": (
                categorias_json
            ),
        },
    )
