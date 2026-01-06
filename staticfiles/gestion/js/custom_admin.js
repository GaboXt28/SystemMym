document.addEventListener("DOMContentLoaded", function () {
    
    // --- PARTE 1: ARREGLAR EL ENLACE DEL DASHBOARD (Tu código original) ---
    const links = document.querySelectorAll('.nav-sidebar .nav-link');

    for (let link of links) {
        if (link.textContent.trim() === "Dashboard") {
            link.href = "/dashboard/";
            link.innerHTML = `
                <i class="nav-icon fas fa-chart-pie text-warning"></i>
                <p>Dashboard Gerencial</p>
            `;
            if (window.location.pathname === "/dashboard/") {
                link.classList.add("active");
            }
            break;
        }
    }

    // --- PARTE 2: ACTUALIZAR PRECIOS AUTOMÁTICAMENTE ---
    // Usamos django.jQuery para asegurar compatibilidad con el Admin
    const $ = django.jQuery; 

    // Función para actualizar el precio de una fila específica
    function actualizarFila(fila) {
        let selectProducto = fila.find('select[name$="-producto"]');
        let inputPrecio = fila.find('input[name$="-precio_aplicado"]');
        
        // Cuando cambian el producto
        selectProducto.on('change', function() {
            let productoId = $(this).val();
            if (productoId) {
                $.ajax({
                    url: '/api/producto/' + productoId + '/',
                    success: function(data) {
                        // Ponemos el precio automáticamente
                        inputPrecio.val(data.precio);
                    }
                });
            } else {
                inputPrecio.val(''); // Si borran el producto, borramos el precio
            }
        });
    }

    // A. Detectar cuando se añaden filas nuevas (botón "Añadir otro Detalle")
    $(document).on('formset:added', function(event, $row, formsetName) {
        actualizarFila($row);
    });

    // B. Aplicar a las filas que ya existen al cargar la página
    $('.dynamic-detalles').each(function() {
        actualizarFila($(this));
    });

});