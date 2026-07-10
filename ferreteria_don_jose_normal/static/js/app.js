document.addEventListener('DOMContentLoaded', () => {

  // =====================================================
  // Mensajes temporales
  // =====================================================

  const toasts = document.querySelectorAll('.toast');

  toasts.forEach((toast, index) => {
    setTimeout(() => {
      toast.classList.add('hide');
    }, 3200 + index * 250);
  });


  // =====================================================
  // Selección entre boleta y factura
  // =====================================================

  const documentRadios = document.querySelectorAll(
    'input[name="tipo_documento"]'
  );

  const invoiceFields = document.querySelector(
    '[data-invoice-fields]'
  );


  const updateDocumentView = () => {

    const selected = document.querySelector(
      'input[name="tipo_documento"]:checked'
    );

    const isInvoice = selected?.value === 'factura';


    if (invoiceFields) {

      invoiceFields.classList.toggle(
        'is-hidden',
        !isInvoice
      );

      invoiceFields
        .querySelectorAll('input')
        .forEach((input) => {
          input.disabled = !isInvoice;
        });

    }

  };


  documentRadios.forEach((radio) => {

    radio.addEventListener(
      'change',
      updateDocumentView
    );

  });


  updateDocumentView();


  // =====================================================
  // Formato automático de RUT
  // =====================================================

  const rutInput = document.querySelector(
    'input[name="factura_rut"]'
  );


  rutInput?.addEventListener('input', (event) => {

    const value = event.target.value
      .toUpperCase()
      .replace(/[^0-9K]/g, '')
      .slice(0, 9);


    if (value.length <= 1) {

      event.target.value = value;
      return;

    }


    const body = value.slice(0, -1);
    const dv = value.slice(-1);

    const bodyFormatted = body.replace(
      /\B(?=(\d{3})+(?!\d))/g,
      '.'
    );

    event.target.value = `${bodyFormatted}-${dv}`;

  });


  // =====================================================
  // Forma de pago
  // =====================================================

  const paymentRadios = document.querySelectorAll(
    'input[name="metodo_pago"]'
  );

  const cardFields = document.querySelector(
    '[data-card-fields]'
  );

  const submitOrder = document.querySelector(
    '[data-submit-order]'
  );


  const updatePaymentView = () => {

    const selected = document.querySelector(
      'input[name="metodo_pago"]:checked'
    );

    const isCard = selected?.value === 'tarjeta';


    if (cardFields) {

      cardFields.classList.toggle(
        'is-hidden',
        !isCard
      );

      cardFields
        .querySelectorAll('input')
        .forEach((input) => {
          input.disabled = !isCard;
        });

    }


    if (submitOrder) {

      submitOrder.textContent = isCard
        ? 'Pagar y generar pedido'
        : 'Generar pedido para retiro';

    }

  };


  paymentRadios.forEach((radio) => {

    radio.addEventListener(
      'change',
      updatePaymentView
    );

  });


  updatePaymentView();


  // =====================================================
  // Número de tarjeta y detección de marca
  // =====================================================

  const cardNumber = document.querySelector(
    'input[name="numero_tarjeta"]'
  );

  const cardBrand = document.querySelector(
    '[data-card-brand]'
  );


  const detectCardBrand = (digits) => {

    if (!digits) {
      return {
        key: 'empty',
        label: 'Sin detectar'
      };
    }


    // VISA
    if (/^4/.test(digits)) {
      return {
        key: 'visa',
        label: 'VISA'
      };
    }


    const firstTwo = Number(
      digits.slice(0, 2)
    );

    const firstFour = Number(
      digits.slice(0, 4)
    );


    // Mastercard 51 a 55
    const mastercardClassic =
      digits.length >= 2 &&
      firstTwo >= 51 &&
      firstTwo <= 55;


    // Mastercard 2221 a 2720
    const mastercardNewRange =
      digits.length >= 4 &&
      firstFour >= 2221 &&
      firstFour <= 2720;


    if (
      mastercardClassic ||
      mastercardNewRange
    ) {

      return {
        key: 'mastercard',
        label: 'Mastercard'
      };

    }


    if (
      (
        digits.startsWith('2') &&
        digits.length < 4
      ) ||
      (
        digits.startsWith('5') &&
        digits.length < 2
      )
    ) {

      return {
        key: 'pending',
        label: 'Detectando…'
      };

    }


    return {
      key: 'other',
      label: 'Otra tarjeta'
    };

  };


  const updateCardNumber = () => {

    if (!cardNumber) {
      return;
    }


    // Elimina letras y símbolos
    const digits = cardNumber.value
      .replace(/\D/g, '')
      .slice(0, 19);


    // Separa el número cada cuatro dígitos
    cardNumber.value = digits
      .replace(/(.{4})/g, '$1 ')
      .trim();


    if (cardBrand) {

      const brand = detectCardBrand(digits);

      cardBrand.className =
        `card-brand-badge is-${brand.key}`;

      cardBrand.textContent =
        brand.label;

    }

  };


  cardNumber?.addEventListener(
    'keydown',
    (event) => {

      const allowedKeys = [
        'Backspace',
        'Delete',
        'ArrowLeft',
        'ArrowRight',
        'ArrowUp',
        'ArrowDown',
        'Home',
        'End',
        'Tab',
        'Enter'
      ];


      const isShortcut =
        event.ctrlKey ||
        event.metaKey;


      const isDigit =
        /^\d$/.test(event.key);


      if (
        !isDigit &&
        !allowedKeys.includes(event.key) &&
        !isShortcut
      ) {

        event.preventDefault();

      }

    }
  );


  cardNumber?.addEventListener(
    'input',
    updateCardNumber
  );


  cardNumber?.addEventListener(
    'paste',
    () => {
      requestAnimationFrame(
        updateCardNumber
      );
    }
  );


  updateCardNumber();


  // =====================================================
  // Fecha de vencimiento de tarjeta
  // =====================================================

  const expiry = document.querySelector(
    'input[name="vencimiento_tarjeta"]'
  );


  expiry?.addEventListener('input', (event) => {

    const digits = event.target.value
      .replace(/\D/g, '')
      .slice(0, 4);


    event.target.value =
      digits.length > 2
        ? `${digits.slice(0, 2)}/${digits.slice(2)}`
        : digits;

  });


  // =====================================================
  // Nombre del archivo de imagen seleccionado
  // =====================================================

  const productImageInput = document.querySelector(
    '#id_imagen'
  );

  const productFileName = document.querySelector(
    '[data-product-file-name]'
  );


  productImageInput?.addEventListener(
    'change',
    () => {

      const selectedFile =
        productImageInput.files?.[0];


      if (productFileName) {

        productFileName.textContent =
          selectedFile
            ? selectedFile.name
            : 'No se ha seleccionado una imagen';

      }

    }
  );


  // =====================================================
  // Copiar código del pedido
  // =====================================================

  const copyButton = document.querySelector(
    '[data-copy-code]'
  );


  copyButton?.addEventListener(
    'click',
    async () => {

      const code =
        copyButton.dataset.copyCode;


      try {

        await navigator.clipboard.writeText(
          code
        );

        copyButton.textContent =
          'Código copiado';

      } catch (error) {

        const temporary =
          document.createElement('textarea');

        temporary.value = code;

        document.body.appendChild(
          temporary
        );

        temporary.select();

        document.execCommand(
          'copy'
        );

        temporary.remove();

        copyButton.textContent =
          'Código copiado';

      }

    }
  );


  // =====================================================
  // BUSCADOR INTELIGENTE EN TIEMPO REAL
  // =====================================================

  const liveSearchForm = document.querySelector(
    '[data-live-search-form]'
  );

  const liveSearchInput = document.querySelector(
    '[data-live-product-search]'
  );

  const productCards = Array.from(
    document.querySelectorAll(
      '[data-product-card]'
    )
  );

  const liveResultsCount = document.querySelector(
    '[data-live-results-count]'
  );

  const liveSearchEmpty = document.querySelector(
    '[data-live-search-empty]'
  );


  // Convierte el texto a minúsculas y elimina tildes.
  // Ejemplo:
  // "Carpintería" pasa a ser "carpinteria".
  const normalizeSearchText = (value) => {

    return (value || '')
      .toString()
      .normalize('NFD')
      .replace(
        /[\u0300-\u036f]/g,
        ''
      )
      .toLowerCase()
      .replace(
        /[^a-z0-9]+/g,
        ' '
      )
      .trim();

  };


  // Calcula cuántas letras iniciales coinciden.
  // Permite relacionar:
  // carpinteria con carpintero.
  const commonPrefixLength = (
    firstWord,
    secondWord
  ) => {

    const limit = Math.min(
      firstWord.length,
      secondWord.length
    );

    let index = 0;


    while (
      index < limit &&
      firstWord[index] === secondWord[index]
    ) {

      index += 1;

    }


    return index;

  };


  // Calcula la diferencia entre dos palabras.
  // Permite tolerar pequeños errores al escribir.
  const levenshteinDistance = (
    firstWord,
    secondWord
  ) => {

    if (firstWord === secondWord) {
      return 0;
    }


    if (!firstWord.length) {
      return secondWord.length;
    }


    if (!secondWord.length) {
      return firstWord.length;
    }


    const previous = Array.from(
      {
        length: secondWord.length + 1
      },
      (_, index) => index
    );


    const current = new Array(
      secondWord.length + 1
    );


    for (
      let firstIndex = 1;
      firstIndex <= firstWord.length;
      firstIndex += 1
    ) {

      current[0] = firstIndex;


      for (
        let secondIndex = 1;
        secondIndex <= secondWord.length;
        secondIndex += 1
      ) {

        const cost =
          firstWord[firstIndex - 1] ===
          secondWord[secondIndex - 1]
            ? 0
            : 1;


        current[secondIndex] = Math.min(

          current[secondIndex - 1] + 1,

          previous[secondIndex] + 1,

          previous[secondIndex - 1] + cost

        );

      }


      for (
        let index = 0;
        index <= secondWord.length;
        index += 1
      ) {

        previous[index] =
          current[index];

      }

    }


    return previous[
      secondWord.length
    ];

  };


  const wordMatchesQuery = (
    word,
    queryToken
  ) => {

    if (!word || !queryToken) {
      return false;
    }


    // Al escribir una sola letra:
    // "t" muestra Taladro, Tornillo y Tubo.
    if (queryToken.length === 1) {

      return word.startsWith(
        queryToken
      );

    }


    // Coincidencia directa.
    if (
      word.includes(queryToken) ||
      queryToken.includes(word)
    ) {

      return true;

    }


    // Coincidencia por comienzo de palabra.
    if (
      word.startsWith(queryToken) ||
      queryToken.startsWith(word)
    ) {

      return true;

    }


    // Coincidencia por palabras relacionadas.
    // carpinteria encuentra carpintero.
    const prefix = commonPrefixLength(
      word,
      queryToken
    );


    const shortest = Math.min(
      word.length,
      queryToken.length
    );


    if (
      shortest >= 5 &&
      prefix >= Math.max(
        5,
        Math.floor(shortest * 0.7)
      )
    ) {

      return true;

    }


    // Tolera uno o dos errores de escritura.
    if (
      shortest >= 5 &&
      Math.abs(
        word.length -
        queryToken.length
      ) <= 2
    ) {

      const maximumDistance =
        shortest >= 8
          ? 2
          : 1;


      return levenshteinDistance(
        word,
        queryToken
      ) <= maximumDistance;

    }


    return false;

  };


  const productMatchesSearch = (
    card,
    normalizedQuery
  ) => {

    if (!normalizedQuery) {
      return true;
    }


    const searchableText =
      normalizeSearchText(
        card.dataset.search
      );


    const productWords =
      searchableText
        .split(' ')
        .filter(Boolean);


    const queryTokens =
      normalizedQuery
        .split(' ')
        .filter(Boolean);


    // Todas las palabras escritas deben coincidir
    // con algún dato del producto.
    return queryTokens.every(
      (queryToken) => {

        return productWords.some(
          (productWord) => {

            return wordMatchesQuery(
              productWord,
              queryToken
            );

          }
        );

      }
    );

  };


  const updateLiveSearch = () => {

    if (
      !liveSearchInput ||
      !productCards.length
    ) {

      return;

    }


    const normalizedQuery =
      normalizeSearchText(
        liveSearchInput.value
      );


    let visibleProducts = 0;


    productCards.forEach((card) => {

      const visible =
        productMatchesSearch(
          card,
          normalizedQuery
        );


      card.hidden = !visible;


      if (visible) {

        visibleProducts += 1;

      }

    });


    // Actualiza el contador.
    if (liveResultsCount) {

      liveResultsCount.textContent =
        `${visibleProducts} ${
          visibleProducts === 1
            ? 'resultado'
            : 'resultados'
        }`;

    }


    // Muestra mensaje si no se encuentra nada.
    if (liveSearchEmpty) {

      liveSearchEmpty.hidden =
        visibleProducts !== 0;

    }

  };


  // Busca automáticamente al escribir.
  liveSearchInput?.addEventListener(
    'input',
    updateLiveSearch
  );


  // También detecta cuando se limpia
  // el campo con la X del navegador.
  liveSearchInput?.addEventListener(
    'search',
    updateLiveSearch
  );


  // El botón Buscar no recarga la página.
  liveSearchForm?.addEventListener(
    'submit',
    (event) => {

      event.preventDefault();

      updateLiveSearch();

      liveSearchInput?.focus();

    }
  );


  // Inicializa el contador.
  updateLiveSearch();

});
