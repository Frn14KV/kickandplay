from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from datetime import date
from rest_framework import viewsets
from .utils import enviar_correo, obtener_coordenadas, upload_to_supabase, calcular_distancia
from .models import Canchas, Equipos, Partidos, Comentarios, Evento, Reserva
from .serializers import CanchaSerializer, EquipoSerializer, PartidoSerializer, ComentarioSerializer
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Count, Avg
from .forms import ReservaForm, EventoForm, ComentarioForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages

#metodos de web
#home
def home(request):
    eventos_destacados = Evento.objects.order_by('-fecha')[:6]
    return render(request, 'index.html', {
        'eventos_destacados': eventos_destacados,
    })

#lista de canchas
def lista_canchas(request):
    hoy = date.today()
    # Obtén los parámetros de búsqueda desde el formulario o la URL
    nombre = request.GET.get('nombre', '')
    lat_usuario = float(request.GET.get('lat', 0))
    lon_usuario = float(request.GET.get('lon', 0))
    distancia_max = request.GET.get('distancia', None)  # Obtén el valor del parámetro
    calificacion_min = request.GET.get('calificacion_min', None)
    filtrar_comentarios = request.GET.get('filtrar_comentarios', None)  # Si se selecciona por comentarios
    
    # Filtrar las canchas
    canchas = Canchas.objects.all()

 # Filtro por nombre 
    if nombre:
        canchas = canchas.filter(nombre__icontains=nombre)

    # Filtro por calificación mínima (si está presente)
    if calificacion_min:
        canchas = canchas.filter(comentarios__calificacion__gte=calificacion_min).distinct()

    # Agregar lógica de filtro separado por cantidad de comentarios o calificación promedio
    if filtrar_comentarios:
        # Ordenar por cantidad de comentarios
        canchas = canchas.annotate(total_comentarios=Count('comentarios')).order_by('-total_comentarios')

    # Filtrar por distancia
    if lat_usuario and lon_usuario and distancia_max:
        lat_usuario = float(lat_usuario)
        lon_usuario = float(lon_usuario)
        distancia_max = float(distancia_max)

        canchas = [
            cancha for cancha in canchas
            if calcular_distancia(lat_usuario, lon_usuario, cancha.latitud, cancha.longitud) <= distancia_max
        ]

    # Agregar la calificación promedio y ordenarlas por este criterio (por defecto)
    canchas = canchas.annotate(
        calificacion_avg=Avg('comentarios__calificacion')  # Calcula el promedio
    ).order_by('-calificacion_avg')  # Ordena de mayor a menor promedio
    #reservas = Reserva.objects.filter(fecha_reserva__gte=hoy)
    return render(request, 'canchas/lista_canchas.html', {'canchas': canchas})

#detalle de canchas
def detalle_cancha(request, cancha_id):
    cancha = get_object_or_404(Canchas, id=cancha_id)
    eventos = Evento.objects.filter(cancha=cancha, fecha__gte=date.today()).order_by('fecha', 'hora_inicio')
    comentarios = Comentarios.objects.filter(cancha=cancha).order_by('-fecha_creacion')
    return render(request, 'detalle_cancha.html', {
        'cancha': cancha,
        'eventos': eventos,
        'comentarios': comentarios,
    })

#mapa de las canchas
def mapa_canchas(request):
    canchas = Canchas.objects.values('id', 'nombre', 'direccion', 'latitud', 'longitud', 'imagen_url')
    return render(request, 'mapa.html', {'canchas': list(canchas)})

#lista de eventos
def lista_eventos(request):
    eventos = Evento.objects.all().order_by('-fecha')
    return render(request, 'eventos.html', {'eventos': eventos})

#detalle evento
def detalle_evento(request, evento_id):
    evento = get_object_or_404(Evento, id=evento_id)
    return render(request, 'detalle_evento.html', {'evento': evento})

#sobre nosotros
def sobre_nosotros(request):
    return render(request, 'sobre_nosotros.html')

#crear reserva
@login_required
def reservar_cancha(request, cancha_id):
    # Obtener la cancha especificada o mostrar un error 404
    cancha = get_object_or_404(Canchas, id=cancha_id)

    if request.method == 'POST':
        # Recuperar datos del formulario
        fecha_reserva = request.POST.get('fecha_reserva')
        hora_inicio = request.POST.get('hora_inicio')
        hora_fin = request.POST.get('hora_fin')

        # Verificar si todos los datos están presentes
        if not (fecha_reserva and hora_inicio and hora_fin):
            messages.error(request, "Por favor, completa todos los campos.")
            return render(request, 'crear_reserva.html', {'cancha': cancha, 'form': request.POST})

        # Validar conflictos de horarios
        conflictos = Reserva.objects.filter(
            cancha=cancha,
            fecha_reserva=fecha_reserva,
            hora_inicio__lt=hora_fin,  # Cuando termina después de que otra comienza
            hora_fin__gt=hora_inicio   # Cuando comienza antes de que otra termina
        )
        if conflictos.exists():
            messages.error(request, "El horario seleccionado ya está reservado.")
            return render(request, 'crear_reserva.html', {'cancha': cancha, 'form': request.POST})

        # Crear la nueva reserva si no hay conflictos
        nueva_reserva = Reserva.objects.create(
            usuario=request.user,  # Usuario autenticado
            cancha=cancha,
            fecha_reserva=fecha_reserva,
            hora_inicio=hora_inicio,
            hora_fin=hora_fin
        )

        # Mostrar mensaje de éxito y redirigir a la confirmación
        messages.success(request, "¡Reserva creada exitosamente!")
        return redirect('confirmacion_reserva', reserva_id=nueva_reserva.id)

    # En caso de GET, renderizar el formulario vacío
    form = ReservaForm(initial={'cancha': cancha})
    return render(request, 'crear_reserva.html', {'cancha': cancha, 'form': form})

#confirmacion de reserva
def confirmacion_reserva(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id)
    return render(request, 'confirmacion_reserva.html', {'reserva': reserva})

#lista reservas
def lista_reservas(request):
     # Filtrar reservas por usuario
    reservas_futuras = Reserva.objects.filter(usuario=request.user, fecha_reserva__gte=date.today()).order_by('fecha_reserva', 'hora_inicio')
    reservas_pasadas = Reserva.objects.filter(usuario=request.user, fecha_reserva__lt=date.today()).order_by('-fecha_reserva', '-hora_inicio')

    return render(request, 'lista_reservas.html', {
        'reservas_futuras': reservas_futuras,
        'reservas_pasadas': reservas_pasadas,
    })
#eliminar reservas
@login_required
def cancelar_reserva(request, reserva_id):
    # Obtener la reserva correspondiente o mostrar un error 404 si no existe
    reserva = get_object_or_404(Reserva, id=reserva_id, usuario=request.user)

    if request.method == 'POST':
        # Eliminar la reserva y mostrar un mensaje de éxito
        reserva.delete()
        messages.success(request, "La reserva ha sido cancelada correctamente.")
        return redirect('lista_reservas')  # Redirigir a la lista de reservas

    # Renderizar la página de confirmación de cancelación
    return render(request, 'confirmar_cancelacion.html', {'reserva': reserva})

#dejar comentario
@login_required
def dejar_comentario(request, cancha_id):
    cancha = get_object_or_404(Canchas, id=cancha_id)

    if request.method == 'POST':
        texto = request.POST.get('texto')
        calificacion = request.POST.get('calificacion')

        # Validar que ambos campos estén completos
        if not texto or not calificacion:
            messages.error(request, "Por favor, completa todos los campos.")
            return redirect('detalle_cancha', cancha_id=cancha.id)

        # Crear el comentario
        Comentarios.objects.create(
            user=request.user,
            cancha=cancha,
            texto=texto,
            calificacion=int(calificacion)
        )
        messages.success(request, "¡Comentario agregado con éxito!")
        return redirect('detalle_cancha', cancha_id=cancha.id)

    return redirect('detalle_cancha', cancha_id=cancha.id)

#detalle reserva
def detalle_reserva(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id, usuario=request.user)
    return render(request, 'detalle_reserva.html', {'reserva': reserva})

#calendario
def calendario_cp(request, cancha_id):
    cancha = get_object_or_404(Canchas, id=cancha_id)
    eventos = Evento.objects.filter(cancha=cancha).order_by('fecha', 'hora_inicio')
    canchas = Canchas.objects.all()  # Aquí se envían todas las canchas

    if request.method == 'POST':
        form = EventoForm(request.POST)
        if form.is_valid():
            evento = form.save(commit=False)
            evento.cancha = cancha  # Asocia el evento a la cancha específica
            evento.save()
            # Redirige al calendario de la misma cancha
            return redirect('calendario_cancha', cancha_id=cancha_id)
    else:
        form = EventoForm(cancha=cancha)

    return render(request, 'calendario_eventos.html', {
        'form': form,
        'eventos': eventos,
        'cancha': cancha,
        'canchas': canchas,  # Asegúrate de incluir todas las canchas aquí
    })

#obtener evento
def obtener_evento(request, evento_id):
    evento = get_object_or_404(Evento, id=evento_id)
    data = {
        "titulo": evento.titulo,
        "descripcion": evento.descripcion,
        "fecha": evento.fecha,
        "hora_inicio": evento.hora_inicio,
        "hora_fin": evento.hora_fin,
        "cancha": evento.cancha.id,  
    }
    return JsonResponse(data)

#editar evento desde el calendario
def editar_evento(request, evento_id):
    evento = get_object_or_404(Evento, id=evento_id)
    if request.method == 'POST':
        form = EventoForm(request.POST, instance=evento, cancha=evento.cancha)
        if form.is_valid():
            evento = form.save(commit=False)
            evento.usuario = request.user  # Asegura que el usuario esté asignado
            evento.save()
            return JsonResponse({
                "success": True,
                "evento": {
                    "titulo": evento.titulo,
                    "fecha": str(evento.fecha),
                    "hora_inicio": str(evento.hora_inicio),
                    "hora_fin": str(evento.hora_fin),
                    "descripcion": evento.descripcion
                }
            }) # Respuesta para AJAX
        else:
            form = EventoForm(instance=evento, cancha=evento.cancha)
            return JsonResponse({"success": False, "errors": form.errors}, status=400)
    return JsonResponse({"success": False, "message": "Método no permitido"}, status=405)

#eliminar evento desde la cancha
def eliminar_evento(request, evento_id):
    evento = get_object_or_404(Evento, id=evento_id)
    cancha_id = evento.cancha.id
    evento.delete()
    # Redirige al calendario de la cancha correspondiente
    return redirect('calendario_cancha', cancha_id=cancha_id)

class CanchaViewSet(viewsets.ModelViewSet):
    queryset = Canchas.objects.all()
    serializer_class = CanchaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['nombre', 'direccion']
    search_fields = ['nombre', 'direccion']
    ordering_fields = ['nombre', 'direccion']

    def perform_create(self, serializer):
        canchas = serializer.save(reservado_por=self.request.user)
        lat, lng = obtener_coordenadas(canchas.direccion)
        if lat is not None and lng is not None:
            canchas.latitud = lat
            canchas.longitud = lng
        # Subir archivo a Supabase si se incluye en la solicitud
        if 'fotos' in self.request.FILES:
            file = self.request.FILES['fotos']
            file_name = f"canchas/{file.name}"
            canchas.imagen_url = upload_to_supabase(file, file_name)
        
        canchas.save()

    def perform_update(self, serializer):
        canchas = serializer.save(reservado_por=self.request.user)
        lat, lng = obtener_coordenadas(canchas.direccion)
        if lat is not None and lng is not None:
            canchas.latitud = lat
            canchas.longitud = lng
        # Subir archivo a Supabase si se incluye en la solicitud
        if 'fotos' in self.request.FILES:
            file = self.request.FILES['fotos']
            file_name = f"canchas/{file.name}"
            canchas.imagen_url = upload_to_supabase(file, file_name)
        
        canchas.save()

class EquipoViewSet(viewsets.ModelViewSet):
    queryset = Equipos.objects.all()
    serializer_class = EquipoSerializer
    permission_classes = [IsAuthenticated]

class PartidoViewSet(viewsets.ModelViewSet):
    queryset = Partidos.objects.all()
    serializer_class = PartidoSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        partido = serializer.save()
        usuarios = list(partido.equipo_local.miembros.all()) + list(partido.equipo_visitante.miembros.all())

class ComentarioViewSet(viewsets.ModelViewSet):
    queryset = Comentarios.objects.all()
    serializer_class = ComentarioSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ListaEventosView(APIView):
    #permission_classes = [IsAuthenticated]
    permission_classes = [AllowAny]

    def get(self, request, format=None):
        eventos = Evento.objects.all()  # Obtener los datos de los eventos
        data = {"eventos": [evento.titulo for evento in eventos]}  # Serializar datos básicos
        return Response(data)  # Responder con los datos en formato JSON

