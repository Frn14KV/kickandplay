// Función para cargar los datos del evento en el modal
function cargarDatosEvento(eventoId) {
    fetch(`/api/eventos/${eventoId}/`)
        .then(response => {
            if (!response.ok) {
                throw new Error("No se pudo cargar el evento.");
            }
            return response.json();
        })
        .then(data => {
            // Llenar los campos del formulario del modal
            document.querySelector('#formEditarEvento').setAttribute('action', `/evento/editar/${eventoId}/`);
            document.querySelector('#titulo').value = data.titulo;
            document.querySelector('#descripcion').value = data.descripcion;
            document.querySelector('#fecha').value = data.fecha;
            document.querySelector('#hora_inicio').value = data.hora_inicio;
            document.querySelector('#hora_fin').value = data.hora_fin;
            // Selecciona la cancha asociada al evento
            const canchaSelect = document.querySelector('#cancha');
            canchaSelect.value = data.cancha;  // Selecciona la cancha correcta
        })
        .catch(error => console.error('Error al cargar los datos del evento:', error));
}


// Manejar el envío del formulario de edición
document.querySelector('#formEditarEvento').addEventListener('submit', function(event) {
    event.preventDefault(); // Evita que el formulario recargue la página

    const formData = new FormData(this); // Obtiene los datos del formulario
    const eventoId = this.getAttribute('data-evento-id'); // Obtiene el ID del evento

    // Realiza la solicitud AJAX al backend
    fetch(`/evento/editar/${eventoId}/`, {
        method: 'POST',
        body: formData,
    })
    .then(response => {
        if (response.ok) {
            // Cierra el modal y actualiza la página o el calendario
            const modal = bootstrap.Modal.getInstance(document.getElementById('modalEditarEvento'));
            modal.hide(); // Cierra el modal usando Bootstrap
            location.reload(); // Recarga la página (o actualiza dinámicamente el calendario)
        } else {
            return response.json();
        }
    })
    .then(data => {
        if (data.errors) {
            // Manejar los errores y mostrarlos al usuario
            console.error('Errores al guardar:', data.errors);
            alert("No se pudo actualizar el evento. Verifica los datos ingresados.");
        }
    })
    .catch(error => console.error('Error al guardar el evento:', error));
});
