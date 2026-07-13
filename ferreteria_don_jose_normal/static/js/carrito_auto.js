document.addEventListener("DOMContentLoaded", () => {
  const quantityForms = document.querySelectorAll(
    "[data-auto-quantity-form]"
  );

  quantityForms.forEach((form) => {
    const input = form.querySelector(
      "[data-quantity-input]"
    );

    const decreaseButton = form.querySelector(
      "[data-quantity-decrease]"
    );

    const increaseButton = form.querySelector(
      "[data-quantity-increase]"
    );

    const status = form.querySelector(
      "[data-auto-status]"
    );

    if (
      !input ||
      !decreaseButton ||
      !increaseButton
    ) {
      return;
    }

    const minimum = Number(
      input.min || 0
    );

    const maximum = Number(
      input.max || 0
    );

    const submitAutomatically = () => {
      decreaseButton.disabled = true;
      increaseButton.disabled = true;
      input.readOnly = true;

      if (status) {
        status.hidden = false;
        status.textContent =
          "Actualizando stock…";
      }

      form.requestSubmit();
    };

    decreaseButton.addEventListener(
      "click",
      () => {
        const current = Number(
          input.value || 0
        );

        const next = Math.max(
          minimum,
          current - 1
        );

        if (next === current) {
          return;
        }

        input.value = String(next);

        submitAutomatically();
      }
    );

    increaseButton.addEventListener(
      "click",
      () => {
        const current = Number(
          input.value || 0
        );

        const next = Math.min(
          maximum,
          current + 1
        );

        if (next === current) {
          return;
        }

        input.value = String(next);

        submitAutomatically();
      }
    );

    input.addEventListener(
      "change",
      () => {
        let value = Number(
          input.value || 0
        );

        if (!Number.isInteger(value)) {
          value = Number.parseInt(
            value,
            10
          );
        }

        if (Number.isNaN(value)) {
          value = minimum;
        }

        value = Math.max(
          minimum,
          Math.min(maximum, value)
        );

        input.value = String(value);

        submitAutomatically();
      }
    );
  });
});
