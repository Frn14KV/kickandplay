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

#metodos de web
#home
def home(request):
    # Filtrar eventos públicos y privados, priorizando los públicos
    eventos_destacados = Evento.objects.filter(
        Q(tipo_evento='publico') | Q(tipo_evento='privado')).order_by('-tipo_evento', '-fecha_creacion')[:6]
    
    return render(request, 'index.html', {'eventos_destacados': eventos_destacados,})

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

#mapa de las canchas
def mapa_canchas(request):
    canchas = Canchas.objects.values('id', 'nombre', 'direccion', 'latitud', 'longitud', 'imagen_url')
    return render(request, 'mapa.html', {'canchas': list(canchas)})

#lista de eventos
def lista_eventos(request):
    eventos = Evento.objects.all().order_by('-fecha_creacion')
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
    # Obtener las reservas futuras (fecha de reserva mayor o igual a hoy)
    reservas_futuras = Reserva.objects.filter(fecha_reserva__gte=date.today()).order_by('fecha_reserva')

    # Obtener las reservas pasadas (fecha de reserva menor a hoy)
    reservas_pasadas = Reserva.objects.filter(fecha_reserva__lt=date.today()).order_by('-fecha_reserva')

    # Paginación para reservas futuras
    paginator_futuras = Paginator(reservas_futuras, 6)  # 6 reservas por página
    page_futuras = request.GET.get('page_futuras')  # Clave para identificar la paginación de futuras
    reservas_futuras = paginator_futuras.get_page(page_futuras)

    # Paginación para reservas pasadas
    paginator_pasadas = Paginator(reservas_pasadas, 6)  # 6 reservas por página
    page_pasadas = request.GET.get('page_pasadas')  # Clave para identificar la paginación de pasadas
    reservas_pasadas = paginator_pasadas.get_page(page_pasadas)

    # Renderizar la plantilla con los datos paginados
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
    # Filtra los eventos relacionados con esta cancha a través de la reserva
    eventos = Evento.objects.filter(reserva__cancha=cancha).order_by('reserva__fecha_reserva', 'reserva__hora_inicio')
    #eventos = Evento.objects.filter(cancha=cancha).order_by('fecha_creacion')
    canchas = Canchas.objects.all()  # Aquí se envían todas las canchas

    if request.method == 'POST':
        form = EventoForm(request.POST)
        if form.is_valid():
            print("aqui")
            evento = form.save(commit=False)
            # Encuentra o valida la reserva asociada a la cancha
            # Aquí puedes ajustar la lógica según cómo gestionas las reservas
            try:
                print("aqui_1")
                reserva = Reserva.objects.get(cancha=cancha, fecha_reserva=request.POST.get('fecha_reserva'))
                print(reserva.fecha_reserva)
                evento.reserva = reserva  # Asocia la reserva al evento
                evento.save()  # Guarda el evento
                # Redirige al calendario después de guardar
                return redirect('calendario_cancha', cancha_id=cancha_id)
            except Reserva.DoesNotExist:
                # Si no hay una reserva asociada, maneja el error (podrías mostrar un mensaje)
                form.add_error(None, "No se encontró una reserva válida para la cancha seleccionada.")
    else:
        form = EventoForm()

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
def crear_evento(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id)
    print("aqui_2")
    # Verifica si ya existe un evento asociado a la reserva
    if hasattr(reserva, 'evento'):
        return redirect('detalle_evento', id=reserva.evento.id)
    print("aqui_2")
    if request.method == 'POST':
        # Para solicitudes AJAX del modal
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            print(request.POST)

            form = EventoForm(request.POST)
            if form.is_valid():
                evento = form.save(commit=False)
                evento.reserva = reserva  # Vincula el evento a la reserva
                evento.save()

                # Responde con JSON para notificar éxito
                return JsonResponse({'status': 'success', 'message': 'Evento creado correctamente!'})
            else:
                # Responde con los errores del formulario
                return JsonResponse({'status': 'error', 'errors': form.errors})

        # Alternativa para solicitudes normales POST
        else:
            form = EventoForm(request.POST)
            if form.is_valid():
                evento = form.save(commit=False)
                evento.reserva = reserva
                evento.save()
                return redirect('detalle_reserva', id=reserva.id)

    # Renderiza el formulario en caso de GET
    form = EventoForm()
    return render(request, 'crear_evento.html', {'form': form, 'reserva': reserva})

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

