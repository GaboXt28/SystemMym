document.addEventListener("DOMContentLoaded", function () {
    const $ = django.jQuery; // Usamos el jQuery de Django

    // =======================================================
    // 1. ARREGLAR ENLACE DEL DASHBOARD
    // =======================================================
    const links = document.querySelectorAll('.nav-sidebar .nav-link');
    for (let link of links) {
        if (link.textContent.trim() === "Dashboard") {
            link.href = "/dashboard/";
            link.innerHTML = `<i class="nav-icon fas fa-chart-pie text-warning"></i><p>Dashboard Gerencial</p>`;
            if (window.location.pathname === "/dashboard/") { link.classList.add("active"); }
            break;
        }
    }

    // =======================================================
    // 2. AUTO-COMPLETAR DIRECCIÓN (CORREGIDO Y MEJORADO)
    // =======================================================
    // Usamos 'body' y 'select2:select' para detectar cambios aunque sea un buscador
    $('body').on('change select2:select', '#id_cliente', function() {
        let clienteId = $(this).val();
        const inputDireccion = $('#id_direccion_entrega');
        
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

    // =======================================================
    // 3. CALCULADORA EN VIVO (TOTAL ESTIMADO) 💰
    // =======================================================
    
    // Inyectamos un texto grande VERDE debajo del campo Total Venta
    $('.field-total_venta').after(
        '<div class="form-row field-total_estimado" style="background:#f1f8e9; padding:15px; border-left: 5px solid #28a745; margin-bottom: 20px;">' +
        '<label style="font-size:16px; color:#333; font-weight:bold;">TOTAL A PAGAR (Estimado):</label>' +
        '<div style="font-size: 28px; font-weight: bold; color: #28a745;" id="texto-gran-total">S/. 0.00</div>' +
        '</div>'
    );

    // Función que recorre todas las filas, multiplica y suma
    function calcularGranTotal() {
        let total = 0;
        $('.dynamic-detalles').each(function() {
            let row = $(this);
            // Buscamos los inputs de esa fila
            let cantidadInput = row.find('input[name$="-cantidad"]');
            let precioInput = row.find('input[name$="-precio_aplicado"]');
            let deleteInput = row.find('input[name$="-DELETE"]');

            // Solo sumamos si no está marcada para eliminar
            if (!deleteInput.is(':checked')) {
                let cant = parseFloat(cantidadInput.val()) || 0;
                let prec = parseFloat(precioInput.val()) || 0;
                total += (cant * prec);
            }
        });
        // Actualizamos el texto grande
        $('#texto-gran-total').text('S/. ' + total.toFixed(2));
    }

    // =======================================================
    // 4. CONFIGURAR FILAS (PRECIOS Y EVENTOS)
    // =======================================================
    function configurarFila(fila) {
        let selectProducto = fila.find('select[name$="-producto"]');
        let inputPrecio = fila.find('input[name$="-precio_aplicado"]');
        let inputCantidad = fila.find('input[name$="-cantidad"]');

        // A. Traer precio al cambiar producto
        selectProducto.on('change', function() {
            let productoId = $(this).val();
            if (productoId) {
                $.ajax({
                    url: '/api/producto/' + productoId + '/',
                    success: function(data) {
                        inputPrecio.val(data.precio);
                        calcularGranTotal(); // Recalcular al obtener precio
                    }
                });
            } else {
                inputPrecio.val('');
                calcularGranTotal();
            }
        });

        // B. Recalcular total si cambian precio o cantidad manualmente
        inputPrecio.on('input change keyup', calcularGranTotal);
        inputCantidad.on('input change keyup', calcularGranTotal);
    }

    // Inicializar filas existentes y nuevas
    $(document).on('formset:added', function(event, $row) { 
        configurarFila($row);
        calcularGranTotal();
    });
    
    $(document).on('formset:removed', function(event, $row) {
        calcularGranTotal();
    });

    $('.dynamic-detalles').each(function() {
        configurarFila($(this));
    });
    
    // Calculo inicial (por si estamos editando)
    setTimeout(calcularGranTotal, 1000);

    // =======================================================
    // 5. VENTANA FLOTANTE (MODAL) PARA VER PDF
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

    spanCerrar.onclick = function() { modal.style.display = "none"; iframe.src = ""; }
    window.onclick = function(event) { if (event.target == modal) { modal.style.display = "none"; iframe.src = ""; } }
});