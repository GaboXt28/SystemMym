document.addEventListener("DOMContentLoaded", function () {
    // Buscamos TODOS los enlaces del menú lateral
    const links = document.querySelectorAll('.nav-sidebar .nav-link');

    for (let link of links) {
        // Buscamos SOLO el enlace que se llama "Dashboard" original
        // Jazzmin le suele poner la ruta /adminconfiguracion/ o /admin/
        if (link.textContent.trim() === "Dashboard") {

            // 1. Cambiamos a dónde va
            link.href = "/dashboard/";

            // 2. Cambiamos cómo se ve
            link.innerHTML = `
                <i class="nav-icon fas fa-chart-pie text-warning"></i>
                <p>Dashboard Gerencial</p>
            `;

            // 3. Si estamos en el dashboard, lo marcamos activo
            if (window.location.pathname === "/dashboard/") {
                link.classList.add("active");
            }

            // 4. ¡IMPORTANTE! Rompemos el ciclo para que solo cambie UNO
            break;
        }
    }
});