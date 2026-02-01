/* gestion/static/gestion/js/custom_admin.js */

document.addEventListener("DOMContentLoaded", function () {
    const $ = django.jQuery; // Usamos el jQuery de Django para asegurar compatibilidad

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
            if (window.location.pathname.includes("/home/")) {
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

    // --- A. AUTO-COMPLETAR DIRECCIÓN DEL CLIENTE ---
    if (selectCliente.length > 0) {
        selectCliente.on('change', function() {
            let clienteId = $(this).val();
            if (clienteId) {
                // Usamos la ruta relativa a tu admin
                $.ajax({
                    url: `/adminconfiguracion/gestion/api/cliente/${clienteId}/`, 
                    type: 'GET',
                    success: function(data) {
                        if (data.direccion) {
                            // Rellenamos el campo, pero el usuario puede editarlo después
                            inputDireccion.val(data.direccion);
                        }
                    },
                    error: function() {
                        console.log("No se pudo obtener la dirección (Verificar URL en urls.py)");
                    }
                });
            }
        });
    }

    // --- B. FUNCIÓN PARA CALCULAR EL TOTAL EN TIEMPO REAL ---
    function calcularTotalGeneral() {
        let totalAcumulado = 0;

        // Recorremos todas las filas visibles de detalles (productos)
        // Nota: Django usa clases dynamic-form o similares. Ajustamos el selector:
        $('.dynamic-detalleguia_set').each(function() {
            const fila = $(this);
            
            // Si la fila está marcada para borrar, no la sumamos
            if (fila.find('input[name$="-DELETE"]').is(':checked')) {
                return; 
            }

            // Buscamos los inputs de Cantidad y Precio dentro de la fila
            let inputCantidad = fila.find('input[name$="-cantidad"]');
            
            // Intentamos buscar el precio. Puede estar en un input visible o ser traído
            // Si tienes un campo 'precio_unitario' en el detalle:
            let inputPrecio = fila.find('input[name$="-precio_unitario"]'); 
            
            // Si no existe input de precio (porque es readonly), buscamos el select del producto
            // y usamos el atributo 'data-precio' que guardaremos ahí.
            let selectProducto = fila.find('select[name$="-producto"]');
            
            let cantidad = parseFloat(inputCantidad.val()) || 0;
            let precio = 0;

            if (inputPrecio.length > 0) {
                precio = parseFloat(inputPrecio.val()) || 0;
            } else {
                precio = parseFloat(selectProducto.attr('data-precio')) || 0;
            }

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
        
        // 1. Cuando cambia el producto -> Traer Precio
        selectProducto.on('change', function() {
            let productoId = $(this).val();
            if (productoId) {
                $.ajax({
                    url: `/adminconfiguracion/gestion/api/producto/${productoId}/`,
                    success: function(data) {
                        let precio = data.precio || 0;
                        
                        // Guardamos el precio en el elemento select para cálculos rápidos
                        selectProducto.attr('data-precio', precio);
                        
                        // Si tienes un campo visible de precio unitario, lo llenamos también
                        let inputPrecioVisible = fila.find('input[name$="-precio_unitario"]');
                        if (inputPrecioVisible.length) {
                            inputPrecioVisible.val(precio);
                        }

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
        fila.find('input[name$="-DELETE"]').on('change', function() {
            calcularTotalGeneral();
        });
    }

    // --- D. INICIALIZACIÓN ---
    
    // 1. Conectar eventos a filas existentes al cargar
    $('.dynamic-detalleguia_set').each(function() {
        const fila = $(this);
        conectarEventosFila(fila);
        
        // Disparar change si ya hay producto seleccionado (para cargar precio inicial)
        let select = fila.find('select[name$="-producto"]');
        if (select.val()) {
            select.trigger('change');
        }
    });

    // 2. Conectar eventos a nuevas filas (Django Admin dynamic forms)
    $(document).on('formset:added', function(event, $row, formsetName) {
        conectarEventosFila($row);
    });


    // =======================================================
    // 3. VENTANA FLOTANTE (MODAL) PARA VER PDF (Mantenido)
    // =======================================================
    const modalHTML = `
    <div id="modalPDF" style="display:none; position:fixed; z-index:9999; left:0; top:0; width:100%; height:100%; overflow:hidden; background-color:rgba(0,0,0,0.6); backdrop-filter: blur(2px);">
        <div style="background-color:#fff; margin: 2% auto; padding:0; border:1px solid #888; width:85%; height:90%; border-radius:8px; display:flex; flex-direction:column; box-shadow: 0 4px 15px 0 rgba(0,0,0,0.3);">
            <div style="padding: 10px 20px; background-color: #343a40; color:white; border-bottom: 1px solid #444; display:flex; justify-content:space-between; align-items:center; border-radius: 8px 8px 0 0;">
                <h4 style="margin:0; font-family: sans-serif; font-size: 16px;"><i class="fas fa-file-pdf"></i> Vista Previa de Guía</h4>
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