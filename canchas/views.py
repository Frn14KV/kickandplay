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
from django.contrib import messages
from django.contrib.auth import login
from .forms import RegistroForm 
from django.contrib.auth.views import LoginView, LogoutView
from .models import UserProfile
from .forms import UserProfileForm, EditUserForm
from django.urls import reverse_lazy
from .forms import CustomLoginForm
from django.core.paginator import Paginator
from django.contrib.auth.forms import UserChangeForm, PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.db.models import Q
from django.utils.timezone import now  # Usamos `now` para manejar fechas dinámicas
from rest_framework import generics
from .serializers import ReservaSerializer, EventoSerializer
from rest_framework.decorators import api_view
from django.contrib.auth.models import User
from .serializers import UserSerializer
from rest_framework.response import Response
from rest_framework.permissions import AllowAny


#----------------------------------------#
#--------------------metodos de web
#--------Publico
#----home
def home(request):
    caracteristicas = [
        {"icono": "bi bi-calendar3", "color": "success", "titulo": "Calendario de Eventos", "descripcion": "Consulta y participa en los eventos más destacados de tu comunidad."},
        {"icono": "bi bi-map", "color": "primary", "titulo": "Encuentra Canchas", "descripcion": "Descubre canchas cercanas y reserva fácilmente desde la plataforma."},
        {"icono": "bi bi-star-fill", "color": "warning", "titulo": "Comentarios y Reseñas", "descripcion": "Consulta calificaciones y opiniones de otros usuarios para elegir mejor."}
    ]
    # Filtrar eventos públicos y privados, priorizando los públicos
    eventos_destacados = Evento.objects.filter(
        Q(tipo_evento='publico') | Q(tipo_evento='privado')).order_by('-tipo_evento', '-fecha_creacion')[:6]
    
    paginator = Paginator(eventos_destacados, 6)  # Muestra 6 eventos por página
    page_number = request.GET.get('page')  # Obtén el número de página actual de la URL
    page_obj = paginator.get_page(page_number)  # Obtén los eventos de la página actual

    return render(request, 'index.html', {
        'caracteristicas': caracteristicas,
        'page_obj': page_obj
    })

#----lista de eventos
def lista_eventos(request):
    eventos = Evento.objects.all().order_by('-fecha_creacion')
    # Filtrar por nombre de evento (si se proporciona)
    query_nombre = request.GET.get('nombre', '')  # "nombre" será el nombre del input en el formulario
    if query_nombre:
        eventos = eventos.filter(titulo__icontains=query_nombre)

    # Filtrar por tipo de evento (si se proporciona)
    query_tipo = request.GET.get('tipo', '')  # "tipo" será el nombre del selector en el formulario
    if query_tipo:
        eventos = eventos.filter(tipo_evento=query_tipo)
        
     # Configura el paginador: 6 eventos por página
    paginator = Paginator(eventos, 6)  # Cambia "6" al número de eventos que quieres por página
    page_number = request.GET.get('page')  # Obtén el número de página desde la URL (parámetro GET)
    page_obj = paginator.get_page(page_number)  # Obtén los eventos para la página actual

    # Envía la página actual al template
    return render(request, 'eventos.html', {'page_obj': page_obj})

#detalle evento
def detalle_evento(request, evento_id):
    evento = get_object_or_404(Evento, id=evento_id)
    return render(request, 'detalle_evento.html', {'evento': evento})

#-----lista de canchas
def lista_canchas(request):
    hoy = date.today()
    # Obtén los parámetros de búsqueda desde el formulario o la URL
    nombre = request.GET.get('nombre', '')
    lat_usuario = float(request.GET.get('lat', 0))
    lon_usuario = float(request.GET.get('lon', 0))
    distancia_max = request.GET.get('distancia', None)  # Obtén el valor del parámetro
    calificacion_min = request.GET.get('calificacion_min', None)
    # Filtrar las canchas
    canchas = Canchas.objects.all()

 # Filtro por nombre 
    if nombre:
        canchas = canchas.filter(nombre__icontains=nombre)

    # Filtro por calificación mínima (si está presente)
    if calificacion_min:
        canchas = canchas.filter(comentarios__calificacion__gte=calificacion_min).distinct()

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
    ).order_by('calificacion_avg')  # Ordena de mayor a menor promedio
    
    # Configura el paginador: muestra 6 canchas por página
    paginator = Paginator(canchas, 6)  # Cambia el número a lo que prefieras
    page_number = request.GET.get('page')  # Obtén el número de página de la URL
    page_obj = paginator.get_page(page_number)  # Obtén los objetos de la página actual

    # Pasamos la página actual (page_obj) al template
    #reservas = Reserva.objects.filter(fecha_reserva__gte=hoy)
    return render(request, 'lista_canchas.html', {'page_obj': page_obj})

#detalle de canchas
def detalle_cancha(request, cancha_id):
    cancha = get_object_or_404(Canchas, id=cancha_id)
    comentarios = Comentarios.objects.filter(cancha=cancha).order_by('-fecha_creacion')
    eventos = Evento.objects.filter(reserva__cancha=cancha)
    return render(request, 'detalle_cancha.html', {
        'cancha': cancha,
        'eventos': eventos,
        'comentarios': comentarios,
    })

#sobre nosotros
def sobre_nosotros(request):
    return render(request, 'sobre_nosotros.html')

#mapa de las canchas
def mapa_canchas(request):
    canchas = Canchas.objects.values('id', 'nombre', 'direccion', 'latitud', 'longitud', 'imagen_url')
    return render(request, 'mapa.html', {'canchas': list(canchas)})

#calendario
def calendario_cp(request, cancha_id):
    cancha = get_object_or_404(Canchas, id=cancha_id)
    reservas = Reserva.objects.filter(cancha=cancha).order_by('fecha_reserva', 'hora_inicio')

    # Validar formato
    for reserva in reservas:
        print(f"Validando reserva {reserva.id}: {reserva.fecha_reserva}T{reserva.hora_inicio} - {reserva.hora_fin}")

    return render(request, 'calendario_eventos.html', {
        'cancha': cancha,
        'reservas': reservas
    })

#----------------------------------------#
#--------Restringido


@api_view(['GET', 'POST'])  # Permitir GET y POST
def obtener_informacion_usuario(request):
    try:
        # Manejo de solicitud GET
        if request.method == 'GET':
            username = request.query_params.get('username')  # Obtener el username desde la URL
            if not username:
                return Response({"error": "El parámetro 'username' es requerido"}, status=400)

        # Manejo de solicitud POST
        elif request.method == 'POST':
            username = request.data.get('username')  # Obtener el username desde el body
            if not username:
                return Response({"error": "El campo 'username' es requerido"}, status=400)

        # Buscar al usuario por username
        usuario = User.objects.filter(username=username).first()
        if not usuario:
            return Response({"error": "Usuario no encontrado"}, status=404)

        # Serializar y devolver los datos del usuario junto con el perfil
        serializer = UserSerializer(usuario)
        return Response(serializer.data, status=200)

    except Exception as e:
        # Manejo de cualquier excepción inesperada
        return Response({"error": str(e)}, status=500)

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
@login_required
def confirmacion_reserva(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id)
    return render(request, 'confirmacion_reserva.html', {'reserva': reserva})

#lista reservas
@login_required
def lista_reservas(request):
    # Fechas actuales para comparar
    hoy = now().date()

    # Filtrar reservas
    reservas_futuras = Reserva.objects.filter(fecha_reserva__gte=hoy).order_by('fecha_reserva')
    reservas_pasadas = Reserva.objects.filter(fecha_reserva__lt=hoy).order_by('-fecha_reserva')

    # Paginación para futuras y pasadas
    reservas_futuras = paginar(request, reservas_futuras, 'page_futuras', 6)
    reservas_pasadas = paginar(request, reservas_pasadas, 'page_pasadas', 6)

    # Renderizar la plantilla con los datos paginados
    return render(request, 'lista_reservas.html', {
        'reservas_futuras': reservas_futuras,
        'reservas_pasadas': reservas_pasadas,
    })

#paginacion para lista de reservas
def paginar(request, queryset, page_param, por_pagina):
    """Función genérica para manejar la paginación"""
    paginator = Paginator(queryset, por_pagina)
    page = request.GET.get(page_param)
    return paginator.get_page(page)

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
@login_required
def detalle_reserva(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id, usuario=request.user)
    return render(request, 'detalle_reserva.html', {'reserva': reserva})

#obtener evento
def obtener_evento(request, evento_id):
    evento = get_object_or_404(Evento, id=evento_id)
    data = {
        "titulo": evento.titulo,
        "descripcion": evento.descripcion,
        "fecha_creacion": evento.fecha_creacion,
        "reserva": evento.reserva.id,  
        "tipo_evento":evento.tipo_evento,
    }
    return JsonResponse(data)

#editar evento
@login_required
def editar_evento(request, evento_id):
    evento = get_object_or_404(Evento, id=evento_id)

    if request.method == 'POST':
        form = EventoForm(request.POST, instance=evento)
        if form.is_valid():
            form.save()
            return JsonResponse({'status': 'success', 'message': 'Evento actualizado correctamente!'})

        # Si hay errores en el formulario
        return JsonResponse({'status': 'error', 'errors': form.errors})

    # Renderiza el formulario si es necesario (en caso de no ser AJAX)
    form = EventoForm(instance=evento)
    return render(request, 'editar_evento.html', {'form': form, 'evento': evento})

#eliminar evento desde la cancha
@login_required
def eliminar_evento(request, evento_id):
    evento = get_object_or_404(Evento, id=evento_id)
    cancha_id = evento.cancha.id
    evento.delete()
    # Redirige al calendario de la cancha correspondiente
    return redirect('calendario_cancha', cancha_id=cancha_id)

#vista registro de usuarios
def registro(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Autenticación automática tras el registro
            messages.success(request, '¡Registro exitoso! Bienvenido/a al sistema.')
            return redirect('home')
        else:
            messages.error(request, 'Corrige los errores en el formulario.')
    else:
        form = RegistroForm()
    return render(request, 'registro.html', {'form': form})

#ver perfil
@login_required
def ver_perfil(request):
    user = request.user
    perfil = user.userprofile  # Obtenemos el perfil del usuario

    # Formulario para editar usuario y perfil
    user_form = EditUserForm(request.POST or None, instance=user)
    profile_form = UserProfileForm(request.POST or None, request.FILES or None, instance=perfil)

    # Formulario para cambiar contraseña
    password_form = PasswordChangeForm(user=user, data=request.POST or None)

    if request.method == 'POST':
        if 'guardar_datos' in request.POST:  # Botón para guardar datos de perfil
            if user_form.is_valid() and profile_form.is_valid():
                user_form.save()
                profile_form.save()
                return redirect('perfil')
        elif 'cambiar_clave' in request.POST:  # Botón para cambiar contraseña
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)  # Mantener la sesión activa
                return redirect('perfil')

    return render(request, 'perfil.html', {
        'perfil': perfil,
        'user_form': user_form,
        'profile_form': profile_form,
        'password_form': password_form,
    })

#crear evento
@login_required
def crear_evento(request, reserva_id):
    print("aquil......")
    reserva = get_object_or_404(Reserva, id=reserva_id)
    # Verifica si ya existe un evento asociado a la reserva
    if hasattr(reserva, 'evento'):
        return redirect('listar_reservas')  # Ajusta la URL según tu configuración
    
    if request.method == 'POST':
        # Para solicitudes AJAX del modal
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            form = EventoForm(request.POST)
            print("aquil")
            if form.is_valid():
               
                evento = form.save(commit=False)
                evento.reserva = reserva  # Vincula el evento a la reserva
                evento.save()

                # Responde con JSON para notificar éxito
                return JsonResponse({'status': 'success', 'message': 'Evento creado correctamente!'})
            else:
                print("no")
                # Responde con los errores del formulario
                return JsonResponse({'status': 'error', 'errors': form.errors})

        # Alternativa para solicitudes normales POST
        else:
            form = EventoForm(request.POST)
            if form.is_valid():
                evento = form.save(commit=False)
                evento.reserva = reserva
                evento.save()
                return redirect('listar_reservas')

    # Renderiza el formulario en caso de GET
    form = EventoForm()
    return render(request, 'crear_evento.html', {'form': form, 'reserva': reserva})

#--------Funciones Generales 
#vista de inicio sesion
class CustomLoginView(LoginView):
    template_name = 'login.html'
    form_class = CustomLoginForm
    redirect_authenticated_user = True
    success_url = reverse_lazy('home')  # Redirige a 'home' tras iniciar sesión

#vista de cierre de sesion
class CustomLogoutView(LogoutView):
    next_page = 'home'  # Redireccionar al login tras salir

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


# Listar y crear reservas
class ReservaListCreateAPIView(generics.ListCreateAPIView):
    queryset = Reserva.objects.all()
    serializer_class = ReservaSerializer

# Recuperar, actualizar y eliminar reservas
class ReservaDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Reserva.objects.all()
    serializer_class = ReservaSerializer

# Listar y crear eventos
class EventoListCreateAPIView(generics.ListCreateAPIView):
    queryset = Evento.objects.all()
    serializer_class = EventoSerializer

# Recuperar, actualizar y eliminar eventos
class EventoDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Evento.objects.all()
    serializer_class = EventoSerializer