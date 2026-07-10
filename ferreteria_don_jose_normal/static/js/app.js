document.addEventListener('DOMContentLoaded', () => {
  const toasts = document.querySelectorAll('.toast');
  toasts.forEach((toast, index) => {
    setTimeout(() => toast.classList.add('hide'), 3200 + index * 250);
  });

  const documentRadios = document.querySelectorAll('input[name="tipo_documento"]');
  const invoiceFields = document.querySelector('[data-invoice-fields]');

  const updateDocumentView = () => {
    const selected = document.querySelector('input[name="tipo_documento"]:checked');
    const isInvoice = selected?.value === 'factura';

    if (invoiceFields) {
      invoiceFields.classList.toggle('is-hidden', !isInvoice);
      invoiceFields.querySelectorAll('input').forEach((input) => {
        input.disabled = !isInvoice;
      });
    }
  };

  documentRadios.forEach((radio) => radio.addEventListener('change', updateDocumentView));
  updateDocumentView();

  const rutInput = document.querySelector('input[name="factura_rut"]');
  rutInput?.addEventListener('input', (event) => {
    const value = event.target.value.toUpperCase().replace(/[^0-9K]/g, '').slice(0, 9);
    if (value.length <= 1) {
      event.target.value = value;
      return;
    }
    const body = value.slice(0, -1);
    const dv = value.slice(-1);
    const bodyFormatted = body.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
    event.target.value = `${bodyFormatted}-${dv}`;
  });

  const paymentRadios = document.querySelectorAll('input[name="metodo_pago"]');
  const cardFields = document.querySelector('[data-card-fields]');
  const submitOrder = document.querySelector('[data-submit-order]');

  const updatePaymentView = () => {
    const selected = document.querySelector('input[name="metodo_pago"]:checked');
    const isCard = selected?.value === 'tarjeta';

    if (cardFields) {
      cardFields.classList.toggle('is-hidden', !isCard);
      cardFields.querySelectorAll('input').forEach((input) => {
        input.disabled = !isCard;
      });
    }

    if (submitOrder) {
      submitOrder.textContent = isCard
        ? 'Pagar y generar pedido'
        : 'Generar pedido para retiro';
    }
  };

  paymentRadios.forEach((radio) => radio.addEventListener('change', updatePaymentView));
  updatePaymentView();

  const cardNumber = document.querySelector('input[name="numero_tarjeta"]');
  const cardBrand = document.querySelector('[data-card-brand]');

  const detectCardBrand = (digits) => {
    if (!digits) return { key: 'empty', label: 'Sin detectar' };
    if (/^4/.test(digits)) return { key: 'visa', label: 'VISA' };

    const firstTwo = Number(digits.slice(0, 2));
    const firstFour = Number(digits.slice(0, 4));
    const mastercardClassic = digits.length >= 2 && firstTwo >= 51 && firstTwo <= 55;
    const mastercardNewRange = digits.length >= 4 && firstFour >= 2221 && firstFour <= 2720;

    if (mastercardClassic || mastercardNewRange) {
      return { key: 'mastercard', label: 'Mastercard' };
    }

    if ((digits.startsWith('2') && digits.length < 4) ||
        (digits.startsWith('5') && digits.length < 2)) {
      return { key: 'pending', label: 'Detectando…' };
    }

    return { key: 'other', label: 'Otra tarjeta' };
  };

  const updateCardNumber = () => {
    if (!cardNumber) return;

    const digits = cardNumber.value.replace(/\D/g, '').slice(0, 19);
    cardNumber.value = digits.replace(/(.{4})/g, '$1 ').trim();

    if (cardBrand) {
      const brand = detectCardBrand(digits);
      cardBrand.className = `card-brand-badge is-${brand.key}`;
      cardBrand.textContent = brand.label;
    }
  };

  cardNumber?.addEventListener('keydown', (event) => {
    const allowedKeys = [
      'Backspace', 'Delete', 'ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown',
      'Home', 'End', 'Tab', 'Enter'
    ];
    const isShortcut = event.ctrlKey || event.metaKey;
    const isDigit = /^\d$/.test(event.key);

    if (!isDigit && !allowedKeys.includes(event.key) && !isShortcut) {
      event.preventDefault();
    }
  });

  cardNumber?.addEventListener('input', updateCardNumber);
  cardNumber?.addEventListener('paste', () => requestAnimationFrame(updateCardNumber));
  updateCardNumber();

  const expiry = document.querySelector('input[name="vencimiento_tarjeta"]');
  expiry?.addEventListener('input', (event) => {
    const digits = event.target.value.replace(/\D/g, '').slice(0, 4);
    event.target.value = digits.length > 2
      ? `${digits.slice(0, 2)}/${digits.slice(2)}`
      : digits;
  });

  const productImageInput = document.querySelector('#id_imagen');
  const productFileName = document.querySelector('[data-product-file-name]');
  productImageInput?.addEventListener('change', () => {
    const selectedFile = productImageInput.files?.[0];
    if (productFileName) {
      productFileName.textContent = selectedFile
        ? selectedFile.name
        : 'No se ha seleccionado una imagen';
    }
  });

  const copyButton = document.querySelector('[data-copy-code]');
  copyButton?.addEventListener('click', async () => {
    const code = copyButton.dataset.copyCode;
    try {
      await navigator.clipboard.writeText(code);
      copyButton.textContent = 'Código copiado';
    } catch (error) {
      const temporary = document.createElement('textarea');
      temporary.value = code;
      document.body.appendChild(temporary);
      temporary.select();
      document.execCommand('copy');
      temporary.remove();
      copyButton.textContent = 'Código copiado';
    }
  });
});
