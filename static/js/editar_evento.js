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
            const canchaSelect = document.querySelector('#cancha');
            canchaSelect.value = data.cancha; // Selecciona la cancha asociada al evento
        })
        .catch(error => console.error('Error al cargar los datos del evento:', error));
}

console.log("Archivo editar_evento.js cargado correctamente.");
function cargarDetallesEvento(eventoId) {
    console.log(`Cargando detalles para el evento con ID: ${eventoId}`);
    fetch(`/api/eventos/${eventoId}/`)
        .then(response => {
            if (!response.ok) {
                throw new Error("No se pudo cargar el evento.");
            }
            return response.json();
        })
        .then(data => {
            // Actualiza los campos del modal con los datos del evento
            document.querySelector('#detalleTitulo').textContent = data.titulo || "Sin título";
            document.querySelector('#detalleDescripcion').textContent = data.descripcion || "Sin descripción";
            document.querySelector('#detalleFecha').textContent = data.fecha || "Sin fecha";
            document.querySelector('#detalleHoraInicio').textContent = data.hora_inicio || "Sin hora inicio";
            document.querySelector('#detalleHoraFin').textContent = data.hora_fin || "Sin hora fin";
            // Actualiza el botón de reserva con la URL correspondiente
            const reservarBoton = document.querySelector('#reservarBoton');
            if (reservarBoton) {
                reservarBoton.setAttribute('href', `/reservar_evento/${eventoId}/`);
            }
        })
        .catch(error => console.error("Error al cargar los detalles del evento:", error));
}


// Manejar el envío del formulario de edición con AJAX
document.addEventListener('DOMContentLoaded', function() {
    console.log("El DOM está completamente cargado y listo.");

    const form = document.querySelector('#formEditarEvento');
    if (form) {
        form.addEventListener('submit', function(event) {
            event.preventDefault(); // Evita el comportamiento predeterminado del formulario
            console.log("El formulario fue interceptado correctamente.");

            const formData = new FormData(this); // Obtiene los datos del formulario
            const actionUrl = this.getAttribute('action'); // Obtiene la URL del atributo action
            const eventoId = actionUrl.split('/').slice(-2, -1)[0]; // Extrae el ID del evento de la URL

            // Realiza la solicitud AJAX al backend
            fetch(actionUrl, {
                method: 'POST',
                body: formData,
            })
            .then(response => {
                if (response.ok) {
                    return response.json(); // Procesa la respuesta JSON
                } else {
                    throw new Error("Error al guardar el evento.");
                }
            })
            .then(data => {
                if (data.success) {
                    // Cierra el modal
                    const modal = bootstrap.Modal.getInstance(document.getElementById('editarEventoModal'));
                    modal.hide(); // Utiliza Bootstrap para cerrar el modal

                    // Actualiza dinámicamente la fila del evento en la tabla
                    console.log(`Actualizando la fila con ID: #evento-${eventoId}`);
                    const eventoRow = document.querySelector(`#evento-${eventoId}`);
                    console.log(eventoRow); // Asegúrate de que no sea null
                    if (eventoRow) {
                        const tituloCell = eventoRow.querySelector('.evento-titulo');
                        if (tituloCell) tituloCell.textContent = data.evento.titulo || "Sin título";
                    
                        const fechaCell = eventoRow.querySelector('.evento-fecha');
                        if (fechaCell) fechaCell.textContent = data.evento.fecha || "Sin fecha";
                    
                        const horaInicioCell = eventoRow.querySelector('.evento-hora-inicio');
                        if (horaInicioCell) horaInicioCell.textContent = data.evento.hora_inicio || "Sin hora inicio";
                    
                        const horaFinCell = eventoRow.querySelector('.evento-hora-fin');
                        if (horaFinCell) horaFinCell.textContent = data.evento.hora_fin || "Sin hora fin";
                    } else {
                        console.warn(`No se encontró la fila con ID evento-${eventoId}`);
                    }
                    
                } else {
                    console.error("Errores en el formulario:", data.errors);
                    alert("No se pudo guardar el evento. Verifica los datos ingresados.");
                }
            })
            .catch(error => console.error('Error en la solicitud AJAX:', error));
        });
    } else {
        console.error("No se encontró el formulario con ID #formEditarEvento.");
    }
});
