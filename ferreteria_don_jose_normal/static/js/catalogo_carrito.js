document.addEventListener("DOMContentLoaded", () => {
  "use strict";

  const forms = document.querySelectorAll(
    "[data-add-cart-form]"
  );

  const toast = document.querySelector(
    "#catalog-toast"
  );

  let toastTimer = null;


  const mostrarMensaje = (
    mensaje,
    esError = false
  ) => {
    if (!toast) {
      return;
    }

    toast.textContent = mensaje;

    toast.classList.toggle(
      "error",
      esError
    );

    toast.classList.add(
      "visible"
    );

    window.clearTimeout(
      toastTimer
    );

    toastTimer = window.setTimeout(
      () => {
        toast.classList.remove(
          "visible"
        );
      },
      2600
    );
  };


  const actualizarContadorCarrito = (
    cantidad
  ) => {
    const contadores = document.querySelectorAll(
      [
        "[data-cart-count]",
        "#carrito-cantidad",
        ".cart-count",
      ].join(",")
    );

    contadores.forEach(
      (contador) => {
        contador.textContent =
          String(cantidad);
      }
    );
  };


  const actualizarProducto = (
    productoId,
    stock
  ) => {
    const badges = document.querySelectorAll(
      `[data-stock-badge="${productoId}"]`
    );

    const botones = document.querySelectorAll(
      `[data-add-button="${productoId}"]`
    );

    badges.forEach(
      (badge) => {
        if (stock > 0) {
          badge.classList.add(
            "available"
          );

          badge.classList.remove(
            "unavailable"
          );

          badge.innerHTML =
            `✓ Disponible · ` +
            `<span data-product-stock="${productoId}">` +
            `${stock}` +
            `</span> un.`;
        } else {
          badge.classList.remove(
            "available"
          );

          badge.classList.add(
            "unavailable"
          );

          badge.textContent =
            "Sin stock";
        }
      }
    );

    botones.forEach(
      (boton) => {
        boton.disabled =
          stock <= 0;

        boton.textContent =
          stock > 0
            ? "+"
            : "×";
      }
    );
  };


  forms.forEach(
    (form) => {
      form.addEventListener(
        "submit",
        async (event) => {
          event.preventDefault();

          if (
            form.dataset.loading ===
            "true"
          ) {
            return;
          }

          const productoId =
            form.dataset.productId;

          const button =
            form.querySelector(
              "[data-add-button]"
            );

          const status =
            form.querySelector(
              "[data-add-status]"
            );

          if (!button) {
            return;
          }

          form.dataset.loading =
            "true";

          button.disabled = true;
          button.textContent = "…";

          if (status) {
            status.textContent =
              "Agregando…";
          }

          try {
            const response = await fetch(
              form.action,
              {
                method: "POST",

                body: new FormData(
                  form
                ),

                headers: {
                  "X-Requested-With":
                    "XMLHttpRequest",

                  Accept:
                    "application/json",
                },

                credentials:
                  "same-origin",
              }
            );

            let data = {};

            try {
              data = await response.json();
            } catch (jsonError) {
              throw new Error(
                "El servidor no devolvió una respuesta válida."
              );
            }

            if (
              !response.ok ||
              data.ok === false
            ) {
              if (
                typeof data.stock !==
                "undefined"
              ) {
                actualizarProducto(
                  productoId,
                  Number(data.stock)
                );
              }

              mostrarMensaje(
                data.mensaje ||
                  "No se pudo agregar el producto.",
                true
              );

              if (status) {
                status.textContent =
                  data.stock <= 0
                    ? "Agotado"
                    : "No agregado";
              }

              return;
            }

            actualizarProducto(
              data.producto_id,
              Number(data.stock)
            );

            actualizarContadorCarrito(
              Number(
                data.cantidad_carrito
              )
            );

            mostrarMensaje(
              data.mensaje ||
                "Producto agregado."
            );

            if (status) {
              status.textContent =
                data.stock > 0
                  ? "Agregado ✓"
                  : "Última unidad agregada";
            }

            button.textContent =
              data.stock > 0
                ? "✓"
                : "×";

            if (data.stock > 0) {
              window.setTimeout(
                () => {
                  button.textContent =
                    "+";

                  if (status) {
                    status.textContent =
                      "";
                  }
                },
                850
              );
            }
          } catch (error) {
            console.error(
              "Error al agregar al carrito:",
              error
            );

            /*
             * Respaldo:
             * si fetch falla, se envía el formulario tradicional.
             */
            form.dataset.loading =
              "fallback";

            HTMLFormElement.prototype.submit.call(
              form
            );

            return;
          } finally {
            if (
              form.dataset.loading !==
              "fallback"
            ) {
              form.dataset.loading =
                "false";

              const stockBadge =
                document.querySelector(
                  `[data-stock-badge="${productoId}"]`
                );

              const estaAgotado =
                stockBadge?.classList.contains(
                  "unavailable"
                );

              button.disabled =
                Boolean(estaAgotado);

              if (
                !estaAgotado &&
                button.textContent === "…"
              ) {
                button.textContent =
                  "+";
              }
            }
          }
        }
      );
    }
  );
});
