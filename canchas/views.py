# Decompiled with PyLingual (https://pylingual.io)
# Internal filename: C:\Users\villa\Django\kicknplay\canchas\views.py
# Bytecode version: 3.12.0rc2 (3531)
# Source timestamp: 2025-02-25 21:23:26 UTC (1740518606)

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
from .forms import ReservaForm, EventoForm
from django.contrib.auth.decorators import login_required

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
    eventos = Evento.objects.filter(cancha=cancha, fecha__gte=date.today())
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
def crear_reserva(request):
    if request.method == 'POST':
        form = ReservaForm(request.POST)
        if form.is_valid():
            reserva = form.save(commit=False)
            reserva.usuario = request.user  # Asocia al usuario autenticado
            reserva.save()
            return redirect('lista_reservas')  # Redirige a una página que muestre las reservas
    else:
        form = ReservaForm()
    return render(request, 'crear_reserva.html', {'form': form})

#lista reservas
def lista_reservas(request):
    # Recuperar todas las reservas del usuario autenticado
    reservas = Reserva.objects.filter(usuario=request.user).order_by('-fecha_reserva', '-hora_inicio')
    return render(request, 'lista_reservas.html', {'reservas': reservas})

#eliminar reservas
@login_required
def eliminar_reserva(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id, usuario=request.user)
    reserva.delete()
    return redirect('lista_reservas')

#buscar reserva
def lista_reservas(request):
    query = request.GET.get('q')  # Obtener el término de búsqueda
    if query:
        reservas = Reserva.objects.filter(
            usuario=request.user,
            cancha__nombre__icontains=query  # Buscar por nombre de la cancha
        ).order_by('-fecha_reserva', '-hora_inicio')
    else:
        reservas = Reserva.objects.filter(usuario=request.user).order_by('-fecha_reserva', '-hora_inicio')

    return render(request, 'lista_reservas.html', {'reservas': reservas, 'query': query})

#detalle reserva
def detalle_reserva(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id, usuario=request.user)
    return render(request, 'detalle_reserva.html', {'reserva': reserva})

#calendario
def calendario_cp(request, cancha_id):
    cancha = get_object_or_404(Canchas, id=cancha_id)
    eventos = Evento.objects.filter(cancha=cancha).order_by('fecha', 'hora_inicio')

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

    return render(request, 'calendario_eventos.html', {'form': form, 'eventos': eventos, 'cancha': cancha})

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
            return JsonResponse({"success": True})  # Respuesta para AJAX
    else:
        form = EventoForm(instance=evento, cancha=evento.cancha)
        
    return JsonResponse({"success": False, "errors": form.errors}, status=400)

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

