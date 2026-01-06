document.addEventListener("DOMContentLoaded", function () {
    const $ = django.jQuery; 

    // 1. LÓGICA DEL CLIENTE -> DIRECCIÓN (NUEVO)
    const selectCliente = $('#id_cliente');
    const inputDireccion = $('#id_direccion_entrega');

    selectCliente.on('change', function() {
        let clienteId = $(this).val();
        if (clienteId) {
            // Pedimos la dirección al servidor
            $.ajax({
                url: '/api/cliente/' + clienteId + '/direccion/',
                type: 'GET',
                success: function(data) {
                    if (data.direccion) {
                        inputDireccion.val(data.direccion);
                    }
                }
            });
        }
    });

    // 2. LÓGICA DEL DASHBOARD (Para arreglar el menú lateral)
    const links = document.querySelectorAll('.nav-sidebar .nav-link');
    for (let link of links) {
        if (link.textContent.trim() === "Dashboard") {
            link.href = "/dashboard/";
            link.innerHTML = `<i class="nav-icon fas fa-chart-pie text-warning"></i><p>Dashboard Gerencial</p>`;
            if (window.location.pathname === "/dashboard/") {
                link.classList.add("active");
            }
            break;
        }
    }

    // 3. LÓGICA DE PRECIOS AUTOMÁTICOS
    function actualizarFila(fila) {
        let selectProducto = fila.find('select[name$="-producto"]');
        let inputPrecio = fila.find('input[name$="-precio_aplicado"]');

        selectProducto.on('change', function() {
            let productoId = $(this).val();
            if (productoId) {
                $.ajax({
                    url: '/api/producto/' + productoId + '/',
                    success: function(data) {
                        inputPrecio.val(data.precio);
                    }
                });
            } else {
                inputPrecio.val('');
            }
        });
    }
    $(document).on('formset:added', function(event, $row) { actualizarFila($row); });
    $('.dynamic-detalles').each(function() { actualizarFila($(this)); });
});