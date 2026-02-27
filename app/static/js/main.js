/**
 * SCRIPT PRINCIPAL - Sistema de Gestion de Residentes
 * Confirmacion de eliminacion via formularios HTML
 */

document.addEventListener('DOMContentLoaded', function() {
    const deleteForms = document.querySelectorAll('.delete-form');

    deleteForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const residenteNombre = this.dataset.nombre;

            if (!confirm(`¿Está seguro de eliminar al residente ${residenteNombre}?`)) {
                e.preventDefault();
            }
        });
    });

    const backgrounds = ['bg-1', 'bg-2', 'bg-3', 'bg-4'];
    let currentIndex = 0;

    const applyBackground = () => {
        document.body.classList.remove(...backgrounds);
        document.body.classList.add(backgrounds[currentIndex]);
        currentIndex = (currentIndex + 1) % backgrounds.length;
    };

    applyBackground();
    setInterval(applyBackground, 60 * 1000);
});
