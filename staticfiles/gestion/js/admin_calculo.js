document.addEventListener('DOMContentLoaded', function () {
    const $ = django.jQuery; // Usamos la herramienta interna de Django

    function calcularTotal() {
        let granTotal = 0;

        // Recorremos todas las filas de productos
        $('tr[id^="detalles-"]').each(function () {
            // Buscamos los inputs de Cantidad y Precio en cada fila
            // NOTA: Django genera IDs como "id_detalles-0-cantidad"
            let cantidadInput = $(this).find('input[id$="-cantidad"]');
            let precioInput = $(this).find('input[id$="-precio_aplicado"]');

            let cantidad = parseFloat(cantidadInput.val()) || 0;
            let precio = parseFloat(precioInput.val()) || 0;

            granTotal += (cantidad * precio);
        });

        // Buscamos dónde mostrar el resultado
        // Intentamos buscar el campo de solo lectura
        let campoTotal = $('.field-total_venta .readonly');

        // Si no existe (porque es una guía nueva), creamos un espacio visual
        if (campoTotal.length === 0) {
            if ($('#total-preview').length === 0) {
                $('.field-total_venta').append('<div class="readonly" id="total-preview" style="font-weight:bold; font-size:1.5em; color:green; padding-top:5px;">S/. 0.00</div>');
            }
            campoTotal = $('#total-preview');
        }

        // Actualizamos el texto
        campoTotal.text('S/. ' + granTotal.toFixed(2) + ' (Pre-cálculo)');
    }

    // ACTUADORES: Ejecutar cuando escriban o cambien algo
    $(document).on('keyup change', 'input[id$="-cantidad"], input[id$="-precio_aplicado"]', function () {
        calcularTotal();
    });

    // Ejecutar cuando agreguen una linea nueva
    $(document).on('click', '.add-row', function () {
        setTimeout(calcularTotal, 1000);
    });
});