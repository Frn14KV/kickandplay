# Decompiled with PyLingual (https://pylingual.io)
# Internal filename: C:\Users\villa\Django\kicknplay\canchas\views.py
# Bytecode version: 3.12.0rc2 (3531)
# Source timestamp: 2025-02-25 21:23:26 UTC (1740518606)

from django.shortcuts import render, get_object_or_404
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

#metodos de web
#home
def home(request):
    return render(request, 'index.html')

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
    print(canchas)
    return render(request, 'canchas/lista_canchas.html', {'canchas': canchas})

#lista de eventos
def lista_eventos(request):
    eventos = Evento.objects.select_related('cancha').all().order_by('fecha_inicio')
    return render(request, 'eventos/lista_eventos.html', {'eventos': eventos})

#detalle de un evento
def detalle_evento(request, id):
    evento = get_object_or_404(Evento, id=id)
    return render(request, 'eventos/detalle_evento.html', {'evento': evento})

#mapa de las canchas
def mapa_canchas(request):
    canchas = Canchas.objects.values('id', 'nombre', 'direccion', 'latitud', 'longitud', 'imagen_url')
    return render(request, 'mapa.html', {'canchas': list(canchas)})

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

