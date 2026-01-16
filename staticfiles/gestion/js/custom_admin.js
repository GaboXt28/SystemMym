document.addEventListener("DOMContentLoaded", function () {
    const $ = django.jQuery; // Usamos el jQuery de Django para asegurar compatibilidad

    // =======================================================
    // 1. ARREGLAR ENLACE DEL DASHBOARD (Menú Lateral)
    // =======================================================
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

    // =======================================================
    // 2. AUTO-COMPLETAR DIRECCIÓN DEL CLIENTE (Restaurado)
    // =======================================================
    const selectCliente = $('#id_cliente');
    const inputDireccion = $('#id_direccion_entrega');

    // Solo activamos esto si existen los campos en pantalla
    if (selectCliente.length > 0) {
        selectCliente.on('change', function() {
            let clienteId = $(this).val();
            if (clienteId) {
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
    }

    // =======================================================
    // 3. ACTUALIZAR PRECIOS AUTOMÁTICAMENTE
    // =======================================================
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

    // A. Detectar cuando se añaden filas nuevas
    $(document).on('formset:added', function(event, $row, formsetName) {
        actualizarFila($row);
    });

    // B. Aplicar a las filas que ya existen
    $('.dynamic-detalles').each(function() {
        actualizarFila($(this));
    });

    // =======================================================
    // 4. VENTANA FLOTANTE (MODAL) PARA VER PDF
    // =======================================================
    
    // A. Inyectamos el HTML del Modal en la página (oculto al inicio)
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
    </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHTML);

    // B. Referencias a los elementos
    const modal = document.getElementById("modalPDF");
    const iframe = document.getElementById("iframePDF");
    const spanCerrar = document.getElementById("cerrarModal");

    // C. Detectar clic en el botón "Ver" (Delegación de eventos para listas dinámicas)
    $('body').on('click', '.ver-pdf-modal', function(e) {
        e.preventDefault(); // Detiene la apertura normal
        
        let urlPDF = $(this).attr('href'); // Obtiene el enlace
        
        iframe.src = urlPDF; // Carga el PDF
        modal.style.display = "block"; // Muestra la ventana
    });

    // D. Cerrar al tocar la X
    spanCerrar.onclick = function() {
        modal.style.display = "none";
        iframe.src = ""; // Limpia el iframe
    }

    // E. Cerrar al tocar fuera del cuadro blanco
    window.onclick = function(event) {
        if (event.target == modal) {
            modal.style.display = "none";
            iframe.src = "";
        }
    }

});