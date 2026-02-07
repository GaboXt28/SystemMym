/* gestion/static/gestion/js/custom_admin.js */

document.addEventListener("DOMContentLoaded", function () {
    const $ = django.jQuery; // Usamos el jQuery de Django para asegurar compatibilidad

    // =======================================================
    // 0. BOTÓN DE "VOLVER" FLOTANTE (ARRIBA IZQUIERDA)
    // =======================================================
    // Solo mostramos el botón si NO estamos en el Dashboard (Home)
    if (!window.location.pathname.includes("/home/") && window.location.pathname !== "/") {
        const btnVolver = document.createElement("button");
        btnVolver.id = "btn-volver-flotante"; // Este ID usa el CSS que creamos
        // Icono de flecha izquierda + Texto
        btnVolver.innerHTML = '<i class="fas fa-arrow-left"></i> <span>Atrás</span>';
        
        btnVolver.onclick = function(e) {
            e.preventDefault();
            window.history.back(); // Regresa a la página anterior
        };
        
        document.body.appendChild(btnVolver);
    }

    // =======================================================
    // 1. ARREGLAR ENLACE DEL DASHBOARD (Menú Lateral)
    // =======================================================
    const links = document.querySelectorAll('.nav-sidebar .nav-link');
    for (let link of links) {
        if (link.textContent.trim() === "Dashboard") {
            link.href = "/home/"; // Ajustado a tu URL real 'home'
            link.innerHTML = `
                <i class="nav-icon fas fa-chart-pie text-warning"></i>
                <p>Dashboard Gerencial</p>
            `;
            // Marcar activo si estamos en el dashboard
            if (window.location.pathname.includes("/home/") || window.location.pathname === "/") {
                link.classList.add("active");
            }
            break;
        }
    }

    // =======================================================
    // 2. LÓGICA MAESTRA: CÁLCULOS Y AUTOCOMPLETADO
    // =======================================================
    
    // --- Referencias a campos principales ---
    const selectCliente = $('#id_cliente');
    const inputDireccion = $('#id_direccion_entrega'); // Asegúrate que este ID coincida con tu HTML
    const inputTotalVenta = $('#id_total_venta');

    // Bloquear el campo total para que sea solo lectura (visual)
    if (inputTotalVenta.length) {
        inputTotalVenta.attr('readonly', true).css('background-color', 'rgba(0,0,0,0.05)');
    }

    // --- A. AUTO-COMPLETAR DIRECCIÓN DEL CLIENTE ---
    if (selectCliente.length > 0) {
        selectCliente.on('change', function() {
            let clienteId = $(this).val();
            if (clienteId) {
                // Usamos la ruta /api/ definida en urls.py
                $.ajax({
                    url: `/api/cliente/${clienteId}/`, 
                    type: 'GET',
                    success: function(data) {
                        if (data.direccion) {
                            // Rellenamos el campo si está vacío o si el usuario cambia de cliente
                            inputDireccion.val(data.direccion);
                        }
                    },
                    error: function(xhr) {
                        console.error("Error obteniendo cliente:", xhr.status);
                    }
                });
            }
        });
    }

    // --- B. FUNCIÓN PARA CALCULAR EL TOTAL EN TIEMPO REAL ---
    function calcularTotalGeneral() {
        let totalAcumulado = 0;

        // Recorremos todas las filas visibles de detalles (productos)
        $('.dynamic-detalleguia_set').each(function() {
            const fila = $(this);
            
            // Si la fila está marcada para borrar, no la sumamos
            if (fila.find('input[name$="-DELETE"]').is(':checked')) {
                return; 
            }

            const inputCantidad = fila.find('input[name$="-cantidad"]');
            const selectProducto = fila.find('select[name$="-producto"]');
            
            // Obtenemos los valores. El precio viene del atributo 'data-precio' que inyectamos vía AJAX
            let cantidad = parseFloat(inputCantidad.val()) || 0;
            let precio = parseFloat(selectProducto.attr('data-precio')) || 0;

            // Sumamos al total
            totalAcumulado += (cantidad * precio);
        });

        // Actualizamos el campo Total General arriba
        if (inputTotalVenta.length > 0) {
            inputTotalVenta.val(totalAcumulado.toFixed(2));
        }
    }

    // --- C. ASIGNAR LOGICA A CADA FILA (PRECIO + LISTENERS) ---
    function conectarEventosFila(fila) {
        let selectProducto = fila.find('select[name$="-producto"]');
        let inputCantidad = fila.find('input[name$="-cantidad"]');
        let deleteBox = fila.find('input[name$="-DELETE"]');
        
        // 1. Cuando cambia el producto -> Traer Precio de la API
        selectProducto.on('change', function() {
            let productoId = $(this).val();
            if (productoId) {
                $.ajax({
                    url: `/api/producto/${productoId}/`,
                    success: function(data) {
                        let precio = data.precio || 0;
                        
                        // Guardamos el precio en el elemento select para cálculos rápidos
                        selectProducto.attr('data-precio', precio);
                        
                        // Recalculamos el total general
                        calcularTotalGeneral();
                    }
                });
            } else {
                selectProducto.attr('data-precio', 0);
                calcularTotalGeneral();
            }
        });

        // 2. Cuando cambia la cantidad -> Recalcular Total
        inputCantidad.on('input keyup change', function() {
            calcularTotalGeneral();
        });
        
        // 3. Si borran la fila -> Recalcular Total
        deleteBox.on('change', function() {
            calcularTotalGeneral();
        });

        // 4. Inicialización para filas existentes (Edición)
        // Si ya hay un producto seleccionado, forzamos la carga del precio
        if (selectProducto.val() && !selectProducto.attr('data-precio')) {
            selectProducto.trigger('change');
        }
    }

    // --- D. INICIALIZACIÓN ---
    
    // 1. Conectar eventos a filas existentes al cargar la página
    $('.dynamic-detalleguia_set').each(function() {
        conectarEventosFila($(this));
    });

    // 2. Conectar eventos a nuevas filas cuando se presiona "Agregar otro"
    $(document).on('formset:added', function(event, $row, formsetName) {
        conectarEventosFila($row);
    });


    // =======================================================
    // 3. VENTANA FLOTANTE (MODAL) PARA VER PDF
    // =======================================================
    const modalHTML = `
    <div id="modalPDF" style="display:none; position:fixed; z-index:9999; left:0; top:0; width:100%; height:100%; overflow:hidden; background-color:rgba(0,0,0,0.6); backdrop-filter: blur(2px);">
        <div style="background-color:#fff; margin: 2% auto; padding:0; border:1px solid #888; width:90%; height:90%; border-radius:15px; display:flex; flex-direction:column; box-shadow: 0 4px 15px 0 rgba(0,0,0,0.3);">
            <div style="padding: 10px 20px; background-color: #1e293b; color:white; border-bottom: 1px solid #444; display:flex; justify-content:space-between; align-items:center;">
                <h4 style="margin:0; font-family: sans-serif; font-size: 16px;"><i class="fas fa-file-pdf"></i> Vista Previa</h4>
                <span id="cerrarModal" style="color:#fff; font-size:30px; font-weight:bold; cursor:pointer; line-height: 20px;">&times;</span>
            </div>
            <div style="flex-grow:1; background-color:#e9ecef; padding:0; position:relative;">
                <iframe id="iframePDF" src="" style="width:100%; height:100%; border:none;"></iframe>
            </div>
        </div>
    </div>`;
    
    document.body.insertAdjacentHTML('beforeend', modalHTML);

    const modal = document.getElementById("modalPDF");
    const iframe = document.getElementById("iframePDF");
    const spanCerrar = document.getElementById("cerrarModal");

    // Delegación de eventos para botones dinámicos
    $('body').on('click', '.ver-pdf-modal', function(e) {
        e.preventDefault();
        let urlPDF = $(this).attr('href');
        iframe.src = urlPDF;
        modal.style.display = "block";
    });

    spanCerrar.onclick = function() {
        modal.style.display = "none";
        iframe.src = "";
    }

    window.onclick = function(event) {
        if (event.target == modal) {
            modal.style.display = "none";
            iframe.src = "";
        }
    }
});