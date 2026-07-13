document.addEventListener(
  "DOMContentLoaded",
  () => {
    "use strict";

    const forms =
      document.querySelectorAll(
        "[data-add-cart-form]"
      );


    /**
     * Muestra un mensaje usando el mismo sistema
     * visual de mensajes que ya tiene el proyecto.
     */
    const mostrarMensaje = (
      mensaje,
      tipo = "success"
    ) => {
      let contenedor =
        document.querySelector(
          ".toast-stack"
        );

      if (!contenedor) {
        contenedor =
          document.createElement(
            "div"
          );

        contenedor.className =
          "toast-stack";

        document.body.appendChild(
          contenedor
        );
      }

      const aviso =
        document.createElement(
          "div"
        );

      aviso.className =
        `toast toast-${tipo}`;

      aviso.textContent =
        mensaje;

      contenedor.appendChild(
        aviso
      );

      window.setTimeout(
        () => {
          aviso.remove();

          if (
            contenedor &&
            !contenedor.children.length
          ) {
            contenedor.remove();
          }
        },
        2800
      );
    };


    /**
     * Actualiza todos los números que muestran
     * la cantidad total del carrito.
     */
    const actualizarContadoresCarrito = (
      cantidad
    ) => {
      const contadores =
        document.querySelectorAll(
          "[data-cart-count]"
        );

      contadores.forEach(
        (contador) => {
          contador.textContent =
            String(cantidad);
        }
      );
    };


    /**
     * Actualiza el stock mostrado en la tarjeta
     * sin recargar la página.
     */
    const actualizarStockProducto = (
      productoId,
      stock
    ) => {
      const badges =
        document.querySelectorAll(
          `[data-stock-badge="${productoId}"]`
        );

      const botones =
        document.querySelectorAll(
          `[data-add-button="${productoId}"]`
        );


      badges.forEach(
        (badge) => {
          if (stock > 0) {
            badge.className =
              "status success";

            badge.innerHTML =
              `✓ Disponible - ` +
              `<span data-product-stock="${productoId}">` +
              `${stock}` +
              `</span> un.`;
          } else {
            badge.className =
              "status danger";

            badge.textContent =
              "✕ Sin stock";
          }
        }
      );


      botones.forEach(
        (boton) => {
          if (stock > 0) {
            boton.disabled =
              false;

            boton.textContent =
              "+";
          } else {
            boton.disabled =
              true;

            boton.textContent =
              "×";
          }
        }
      );
    };


    forms.forEach(
      (form) => {
        form.addEventListener(
          "submit",
          async (event) => {
            /*
             * Esta instrucción impide que el formulario
             * recargue la página.
             */
            event.preventDefault();


            if (
              form.dataset.enviando ===
              "true"
            ) {
              return;
            }


            const productoId =
              form.dataset.productId;

            const boton =
              form.querySelector(
                "[data-add-button]"
              );


            if (!boton) {
              return;
            }


            form.dataset.enviando =
              "true";

            boton.disabled =
              true;

            boton.textContent =
              "…";


            try {
              const respuesta =
                await fetch(
                  form.action,
                  {
                    method:
                      "POST",

                    body:
                      new FormData(
                        form
                      ),

                    headers: {
                      "X-Requested-With":
                        "XMLHttpRequest",

                      "Accept":
                        "application/json",
                    },

                    credentials:
                      "same-origin",
                  }
                );


              const tipoContenido =
                respuesta.headers.get(
                  "content-type"
                ) || "";


              if (
                !tipoContenido.includes(
                  "application/json"
                )
              ) {
                throw new Error(
                  "El servidor no devolvió una respuesta JSON."
                );
              }


              const datos =
                await respuesta.json();


              if (
                !respuesta.ok ||
                datos.ok === false
              ) {
                if (
                  datos.stock !==
                  undefined
                ) {
                  actualizarStockProducto(
                    productoId,
                    Number(
                      datos.stock
                    )
                  );
                }


                mostrarMensaje(
                  datos.mensaje ||
                    "No se pudo agregar el producto.",
                  "error"
                );

                return;
              }


              actualizarStockProducto(
                String(
                  datos.producto_id
                ),
                Number(
                  datos.stock
                )
              );


              actualizarContadoresCarrito(
                Number(
                  datos.cantidad_carrito
                )
              );


              mostrarMensaje(
                datos.mensaje ||
                  "Producto agregado.",
                "success"
              );


              if (
                Number(datos.stock) > 0
              ) {
                boton.textContent =
                  "✓";

                window.setTimeout(
                  () => {
                    boton.textContent =
                      "+";

                    boton.disabled =
                      false;
                  },
                  650
                );
              } else {
                boton.textContent =
                  "×";

                boton.disabled =
                  true;
              }

            } catch (error) {
              console.error(
                "Error al agregar al carrito:",
                error
              );


              /*
               * No se envía el formulario tradicional.
               * Así se evita completamente que la página
               * se refresque si ocurre un error.
               */
              mostrarMensaje(
                (
                  "No se pudo agregar el producto. " +
                  "Revisa la conexión e intenta nuevamente."
                ),
                "error"
              );


              boton.disabled =
                false;

              boton.textContent =
                "+";

            } finally {
              form.dataset.enviando =
                "false";
            }
          }
        );
      }
    );
  }
);
