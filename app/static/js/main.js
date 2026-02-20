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
});
