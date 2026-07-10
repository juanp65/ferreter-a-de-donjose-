(() => {
  "use strict";

  const photoInput =
    document.querySelector("#stock-photo");

  const readButton =
    document.querySelector("#read-stock-photo");

  const previewImage =
    document.querySelector("#stock-photo-preview");

  const previewEmpty =
    document.querySelector("#stock-preview-empty");

  const progressBox =
    document.querySelector("#stock-progress");

  const progressFill =
    document.querySelector("#stock-progress-fill");

  const progressText =
    document.querySelector("#stock-progress-text");

  const rawText =
    document.querySelector("#stock-raw-text");

  const processButton =
    document.querySelector("#process-stock-text");

  const reviewSection =
    document.querySelector("#stock-review-section");

  const reviewBody =
    document.querySelector("#stock-review-body");

  const rowCounter =
    document.querySelector("#stock-row-counter");

  const reviewAlert =
    document.querySelector("#stock-review-alert");

  const importForm =
    document.querySelector("#stock-import-form");

  const rowsJson =
    document.querySelector("#stock-rows-json");

  const saveButton =
    document.querySelector("#save-stock-import");


  if (!photoInput || !importForm) {
    return;
  }


  const products = JSON.parse(
    document
      .querySelector("#stock-products-data")
      ?.textContent || "[]"
  );


  const categories = JSON.parse(
    document
      .querySelector("#stock-categories-data")
      ?.textContent || "[]"
  );


  let parsedRows = [];


  const normalize = (value) => (
    value || ""
  )
    .toString()
    .normalize("NFD")
    .replace(
      /[\u0300-\u036f]/g,
      ""
    )
    .toLowerCase()
    .replace(
      /[^a-z0-9]+/g,
      " "
    )
    .trim()
    .replace(
      /\s+/g,
      " "
    );


  const levenshtein = (
    first,
    second
  ) => {

    if (first === second) {
      return 0;
    }

    if (!first.length) {
      return second.length;
    }

    if (!second.length) {
      return first.length;
    }


    const previous = Array.from(
      {
        length:
          second.length + 1
      },
      (_, index) => index
    );


    const current = new Array(
      second.length + 1
    );


    for (
      let firstIndex = 1;
      firstIndex <= first.length;
      firstIndex += 1
    ) {

      current[0] = firstIndex;


      for (
        let secondIndex = 1;
        secondIndex <= second.length;
        secondIndex += 1
      ) {

        const cost =
          first[firstIndex - 1] ===
          second[secondIndex - 1]
            ? 0
            : 1;


        current[secondIndex] =
          Math.min(

            current[
              secondIndex - 1
            ] + 1,

            previous[
              secondIndex
            ] + 1,

            previous[
              secondIndex - 1
            ] + cost

          );

      }


      for (
        let index = 0;
        index <= second.length;
        index += 1
      ) {

        previous[index] =
          current[index];

      }

    }


    return previous[
      second.length
    ];

  };


  const similarity = (
    first,
    second
  ) => {

    const normalizedFirst =
      normalize(first);

    const normalizedSecond =
      normalize(second);


    if (
      !normalizedFirst ||
      !normalizedSecond
    ) {
      return 0;
    }


    if (
      normalizedFirst ===
      normalizedSecond
    ) {
      return 1;
    }


    if (
      normalizedFirst.includes(
        normalizedSecond
      ) ||
      normalizedSecond.includes(
        normalizedFirst
      )
    ) {
      return 0.94;
    }


    const distance =
      levenshtein(
        normalizedFirst,
        normalizedSecond
      );


    const baseScore =
      1 -
      distance /
      Math.max(
        normalizedFirst.length,
        normalizedSecond.length
      );


    const wordsFirst =
      new Set(
        normalizedFirst.split(" ")
      );


    const wordsSecond =
      new Set(
        normalizedSecond.split(" ")
      );


    const common = [
      ...wordsFirst
    ].filter(
      (word) =>
        wordsSecond.has(word)
    ).length;


    const union =
      new Set([
        ...wordsFirst,
        ...wordsSecond,
      ]).size || 1;


    const tokenScore =
      common / union;


    return Math.max(
      baseScore,
      tokenScore * 0.92
    );

  };


  const bestProductMatch = (
    name
  ) => {

    let best = null;
    let score = 0;


    products.forEach(
      (product) => {

        const currentScore =
          similarity(
            name,
            product.nombre
          );


        if (
          currentScore > score
        ) {

          score =
            currentScore;

          best =
            product;

        }

      }
    );


    return {
      product: best,
      score,
    };

  };


  const cleanNumber = (
    value
  ) => (
    value || ""
  )
    .toString()
    .replace(
      /[^0-9]/g,
      ""
    );


  const parseLine = (
    line
  ) => {

    const cleaned = line
      .replace(
        /[•·]/g,
        " "
      )
      .replace(
        /\s+/g,
        " "
      )
      .trim();


    if (!cleaned) {
      return null;
    }


    const header =
      normalize(cleaned);


    if (
      header ===
        "producto stock precio" ||
      header ===
        "nombre stock precio" ||
      header.startsWith(
        "codigo producto"
      )
    ) {
      return null;
    }


    let name = "";
    let stock = "";
    let price = "";


    const separated = cleaned
      .split(
        /\s*[|;\t]\s*/
      )
      .map(
        (part) =>
          part.trim()
      )
      .filter(Boolean);


    if (
      separated.length >= 3
    ) {

      name = separated
        .slice(0, -2)
        .join(" ");


      stock = cleanNumber(
        separated[
          separated.length - 2
        ]
      );


      price = cleanNumber(
        separated[
          separated.length - 1
        ]
      );

    } else if (
      separated.length === 2
    ) {

      name =
        separated[0];


      stock =
        cleanNumber(
          separated[1]
        );

    } else {

      /*
       * Se analiza desde el final.
       *
       * Esto evita confundir medidas como:
       * Cemento 50 kg
       * Tubo PVC 110 mm
       * Tornillo 2 pulgadas
       */

      const withPrice =
        cleaned.match(
          /^(.*?)\s+(\d+)\s+\$?([\d.]+)$/
        );


      const stockOnly =
        cleaned.match(
          /^(.*?)\s+(\d+)$/
        );


      if (withPrice) {

        name =
          withPrice[1].trim();

        stock =
          cleanNumber(
            withPrice[2]
          );

        price =
          cleanNumber(
            withPrice[3]
          );

      } else if (
        stockOnly
      ) {

        name =
          stockOnly[1].trim();

        stock =
          cleanNumber(
            stockOnly[2]
          );

      } else {

        return null;

      }

    }


    name = name
      .replace(
        /^\s*\d+[.)-]?\s*/,
        ""
      )
      .replace(
        /\s+-\s*$/,
        ""
      )
      .trim();


    if (
      !name ||
      stock === ""
    ) {
      return null;
    }


    const match =
      bestProductMatch(name);


    const shouldUpdate =
      Boolean(
        match.product &&
        match.score >= 0.78
      );


    return {

      nombre:
        name,

      stock,

      precio:
        price,

      accion:
        shouldUpdate
          ? "actualizar"
          : "crear",

      producto_id:
        shouldUpdate
          ? String(
              match.product.id
            )
          : "",

      categoria_id:
        shouldUpdate
          ? String(
              match.product
                .categoria_id
            )
          : String(
              categories[0]?.id ||
              ""
            ),

      match_score:
        match.score,

    };

  };


  const parseText = (
    text
  ) => {

    const seen =
      new Set();

    const rows =
      [];


    text
      .split(/\r?\n/)
      .map(parseLine)
      .filter(Boolean)
      .forEach(
        (row) => {

          const key =
            `${normalize(
              row.nombre
            )}|${row.stock}|${row.precio}`;


          if (
            !seen.has(key)
          ) {

            seen.add(key);

            rows.push(row);

          }

        }
      );


    return rows;

  };


  function escapeHtml(
    value
  ) {

    return (
      value || ""
    )
      .toString()
      .replace(
        /&/g,
        "&amp;"
      )
      .replace(
        /</g,
        "&lt;"
      )
      .replace(
        />/g,
        "&gt;"
      )
      .replace(
        /"/g,
        "&quot;"
      )
      .replace(
        /'/g,
        "&#039;"
      );

  }


  const productOptions = (
    selectedId
  ) => {

    const options = [
      (
        '<option value="">' +
        "Seleccionar producto…" +
        "</option>"
      ),
    ];


    products.forEach(
      (product) => {

        const selected =
          String(product.id) ===
          String(selectedId)
            ? " selected"
            : "";


        options.push(
          (
            `<option ` +
            `value="${product.id}"` +
            `${selected}>` +
            `${escapeHtml(
              product.nombre
            )} — stock ${product.stock}` +
            `</option>`
          )
        );

      }
    );


    return options.join("");

  };


  const categoryOptions = (
    selectedId
  ) => {

    const options = [];


    categories.forEach(
      (category) => {

        const selected =
          String(category.id) ===
          String(selectedId)
            ? " selected"
            : "";


        options.push(
          (
            `<option ` +
            `value="${category.id}"` +
            `${selected}>` +
            `${escapeHtml(
              category.nombre
            )}` +
            `</option>`
          )
        );

      }
    );


    return options.join("");

  };


  const updateRowVisibility = (
    rowElement
  ) => {

    const action =
      rowElement
        .querySelector(
          '[data-field="accion"]'
        )
        ?.value;


    const existing =
      rowElement
        .querySelector(
          ".stock-existing-select"
        );


    const category =
      rowElement
        .querySelector(
          ".stock-category-select"
        );


    if (existing) {
      existing.hidden =
        action !== "actualizar";
    }


    if (category) {
      category.hidden =
        action !== "crear";
    }


    rowElement.classList.toggle(
      "is-ignored",
      action === "ignorar"
    );

  };


  const renderRows = () => {

    reviewBody.innerHTML =
      "";


    parsedRows.forEach(
      (row, index) => {

        const tr =
          document.createElement(
            "tr"
          );


        tr.dataset.rowIndex =
          String(index);


        const matchMessage =
          row.accion === "actualizar"
            ? (
                "Coincidencia estimada: " +
                `${Math.round(
                  row.match_score * 100
                )}%`
              )
            : (
                "No se encontró una " +
                "coincidencia segura"
              );


        tr.innerHTML = `

          <td>

            <input
              class="stock-cell-input"
              type="text"
              data-field="nombre"
              value="${escapeHtml(
                row.nombre
              )}"
              aria-label="Nombre del producto"
            >

            <small class="stock-match-help">
              ${matchMessage}
            </small>

          </td>


          <td>

            <input
              class="stock-cell-input stock-number-input"
              type="number"
              min="0"
              step="1"
              data-field="stock"
              value="${escapeHtml(
                row.stock
              )}"
              aria-label="Stock"
            >

          </td>


          <td>

            <input
              class="stock-cell-input stock-number-input"
              type="number"
              min="0"
              step="1"
              data-field="precio"
              value="${escapeHtml(
                row.precio
              )}"
              placeholder="Mantener / ingresar"
              aria-label="Precio"
            >

          </td>


          <td>

            <select
              class="stock-cell-select"
              data-field="accion"
              aria-label="Acción"
            >

              <option
                value="actualizar"
                ${
                  row.accion ===
                  "actualizar"
                    ? "selected"
                    : ""
                }
              >
                Actualizar
              </option>

              <option
                value="crear"
                ${
                  row.accion ===
                  "crear"
                    ? "selected"
                    : ""
                }
              >
                Crear nuevo
              </option>

              <option
                value="ignorar"
                ${
                  row.accion ===
                  "ignorar"
                    ? "selected"
                    : ""
                }
              >
                Ignorar
              </option>

            </select>

          </td>


          <td>

            <select
              class="stock-cell-select stock-existing-select"
              data-field="producto_id"
              aria-label="Producto existente"
            >
              ${productOptions(
                row.producto_id
              )}
            </select>


            <select
              class="stock-cell-select stock-category-select"
              data-field="categoria_id"
              aria-label="Categoría"
            >
              ${categoryOptions(
                row.categoria_id
              )}
            </select>

          </td>


          <td>

            <button
              type="button"
              class="stock-remove-row"
              aria-label="Quitar fila"
            >
              ×
            </button>

          </td>

        `;


        reviewBody.appendChild(
          tr
        );


        updateRowVisibility(
          tr
        );

      }
    );


    rowCounter.textContent =
      (
        `${parsedRows.length} ` +
        (
          parsedRows.length === 1
            ? "fila"
            : "filas"
        )
      );


    reviewSection.hidden =
      parsedRows.length === 0;

  };


  const syncRowsFromTable =
    () => {

      const rows = [];


      reviewBody
        .querySelectorAll("tr")
        .forEach(
          (tr) => {

            const row = {};


            tr
              .querySelectorAll(
                "[data-field]"
              )
              .forEach(
                (field) => {

                  row[
                    field.dataset.field
                  ] = field.value;

                }
              );


            rows.push(row);

          }
        );


      parsedRows = rows;

      return rows;

    };


  const validateRows = (
    rows
  ) => {

    const errors = [];


    rows.forEach(
      (row, index) => {

        const line =
          index + 1;


        if (
          row.accion ===
          "ignorar"
        ) {
          return;
        }


        if (
          !row.nombre.trim()
        ) {

          errors.push(
            (
              `Fila ${line}: ` +
              "falta el nombre."
            )
          );

        }


        if (
          row.stock === "" ||
          Number(row.stock) < 0
        ) {

          errors.push(
            (
              `Fila ${line}: ` +
              "stock no válido."
            )
          );

        }


        if (
          row.accion ===
            "actualizar" &&
          !row.producto_id
        ) {

          errors.push(
            (
              `Fila ${line}: ` +
              "selecciona el producto " +
              "que deseas actualizar."
            )
          );

        }


        if (
          row.accion ===
            "crear" &&
          (
            row.precio === "" ||
            Number(row.precio) < 0
          )
        ) {

          errors.push(
            (
              `Fila ${line}: ` +
              "agrega el precio del " +
              "producto nuevo."
            )
          );

        }

      }
    );


    return errors;

  };


  photoInput.addEventListener(
    "change",
    () => {

      const file =
        photoInput.files?.[0];


      if (!file) {

        previewImage.hidden =
          true;

        previewEmpty.hidden =
          false;

        return;

      }


      const url =
        URL.createObjectURL(
          file
        );


      previewImage.src =
        url;

      previewImage.hidden =
        false;

      previewEmpty.hidden =
        true;

    }
  );


  readButton.addEventListener(
    "click",
    async () => {

      const file =
        photoInput.files?.[0];


      if (!file) {

        window.alert(
          (
            "Primero selecciona " +
            "una fotografía."
          )
        );

        return;

      }


      if (!window.Tesseract) {

        window.alert(
          (
            "No se pudo cargar el lector OCR. " +
            "Revisa tu conexión e intenta nuevamente."
          )
        );

        return;

      }


      readButton.disabled =
        true;

      progressBox.hidden =
        false;

      progressFill.style.width =
        "0%";

      progressText.textContent =
        "Cargando lector…";


      let worker;


      try {

        worker =
          await window.Tesseract
            .createWorker(
              "spa",
              1,
              {
                logger: (
                  message
                ) => {

                  const progress =
                    Math.round(
                      (
                        message.progress ||
                        0
                      ) * 100
                    );


                  progressFill
                    .style
                    .width =
                      `${progress}%`;


                  progressText
                    .textContent =
                      (
                        `${message.status || "Procesando"} ` +
                        `${progress}%`
                      );

                },
              }
            );


        const result =
          await worker.recognize(
            file
          );


        rawText.value =
          result.data.text.trim();


        progressFill
          .style
          .width =
            "100%";


        progressText
          .textContent =
            "Lectura terminada";


        parsedRows =
          parseText(
            rawText.value
          );


        renderRows();


        if (
          !parsedRows.length
        ) {

          reviewAlert.hidden =
            false;

          reviewAlert.textContent =
            (
              "No se detectaron filas completas. " +
              "Corrige el texto y presiona " +
              "“Procesar texto”."
            );

        } else {

          reviewAlert.hidden =
            true;

          reviewSection
            .scrollIntoView(
              {
                behavior:
                  "smooth",
                block:
                  "start",
              }
            );

        }

      } catch (error) {

        console.error(error);


        progressText
          .textContent =
            (
              "No se pudo completar " +
              "la lectura"
            );


        window.alert(
          (
            "No se pudo leer la fotografía. " +
            "Puedes escribir o pegar el texto " +
            "manualmente en el recuadro."
          )
        );

      } finally {

        if (worker) {
          await worker.terminate();
        }


        readButton.disabled =
          false;

      }

    }
  );


  processButton.addEventListener(
    "click",
    () => {

      parsedRows =
        parseText(
          rawText.value
        );


      renderRows();


      if (
        !parsedRows.length
      ) {

        reviewAlert.hidden =
          false;

        reviewAlert.textContent =
          (
            "No se detectaron filas. " +
            "Usa el formato: " +
            "Producto | stock | precio."
          );

      } else {

        reviewAlert.hidden =
          true;


        reviewSection
          .scrollIntoView(
            {
              behavior:
                "smooth",
              block:
                "start",
            }
          );

      }

    }
  );


  reviewBody.addEventListener(
    "change",
    (event) => {

      const tr =
        event.target.closest("tr");


      if (!tr) {
        return;
      }


      if (
        event.target.matches(
          '[data-field="accion"]'
        )
      ) {

        updateRowVisibility(
          tr
        );

      }


      if (
        event.target.matches(
          '[data-field="producto_id"]'
        )
      ) {

        const selected =
          products.find(
            (product) =>
              String(product.id) ===
              event.target.value
          );


        if (selected) {

          const priceInput =
            tr.querySelector(
              '[data-field="precio"]'
            );


          if (
            priceInput &&
            !priceInput.value
          ) {

            priceInput.value =
              selected.precio;

          }

        }

      }

    }
  );


  reviewBody.addEventListener(
    "click",
    (event) => {

      const button =
        event.target.closest(
          ".stock-remove-row"
        );


      if (!button) {
        return;
      }


      const tr =
        button.closest("tr");


      if (tr) {
        tr.remove();
      }


      syncRowsFromTable();


      rowCounter.textContent =
        (
          `${parsedRows.length} ` +
          (
            parsedRows.length === 1
              ? "fila"
              : "filas"
          )
        );


      reviewSection.hidden =
        parsedRows.length === 0;

    }
  );


  importForm.addEventListener(
    "submit",
    (event) => {

      const rows =
        syncRowsFromTable();


      const errors =
        validateRows(rows);


      if (
        errors.length
      ) {

        event.preventDefault();


        reviewAlert.hidden =
          false;


        reviewAlert.innerHTML =
          errors
            .slice(0, 5)
            .map(
              (error) =>
                (
                  `<div>` +
                  `${escapeHtml(error)}` +
                  `</div>`
                )
            )
            .join("");


        reviewAlert
          .scrollIntoView(
            {
              behavior:
                "smooth",
              block:
                "center",
            }
          );


        return;

      }


      if (
        !rows.some(
          (row) =>
            row.accion !==
            "ignorar"
        )
      ) {

        event.preventDefault();


        window.alert(
          (
            "No hay filas seleccionadas " +
            "para guardar."
          )
        );


        return;

      }


      if (
        !window.confirm(
          (
            "¿Guardar estos cambios " +
            "en el inventario?"
          )
        )
      ) {

        event.preventDefault();
        return;

      }


      rowsJson.value =
        JSON.stringify(rows);


      saveButton.disabled =
        true;


      saveButton.textContent =
        "Guardando…";

    }
  );

})();
