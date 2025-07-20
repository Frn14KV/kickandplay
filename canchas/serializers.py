from rest_framework import serializers
from .models import Canchas, Equipos, Partidos, Comentarios, Evento, Reserva
from django.contrib.auth.models import User
from .models import UserProfile

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['bio', 'profile_image', 'location', 'phone_number']

class UserSerializer(serializers.ModelSerializer):
    user_profile = UserProfileSerializer()  # Cambiado de "perfil" a "user_profile"

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'user_profile']
        
# -----------------------------------------------
# SERIALIZADOR PARA RESERVAS
# -----------------------------------------------
class ReservaSerializer(serializers.ModelSerializer):
    """
    Serializador para el modelo Reserva.
    Convierte las instancias de reservas a JSON y viceversa.
    """
    class Meta:
        model = Reserva
        fields = ['id', 'usuario', 'cancha', 'fecha_reserva', 'hora_inicio', 'hora_fin', 'estado']


# -----------------------------------------------
# SERIALIZADOR PARA EVENTOS
# -----------------------------------------------
class EventoSerializer(serializers.ModelSerializer):
    """
    Serializador para el modelo Evento.
    Incluye una relación con la reserva asociada.
    """
    reserva = ReservaSerializer()  # Relación anidada: incluye los detalles de la reserva

    class Meta:
        model = Evento
        fields = ['id', 'titulo', 'descripcion', 'tipo_evento', 'fecha_creacion', 'reserva']


# -----------------------------------------------
# SERIALIZADOR PARA EQUIPOS
# -----------------------------------------------
class EquipoSerializer(serializers.ModelSerializer):
    """
    Serializador para el modelo Equipos.
    Convierte las instancias de equipos a JSON, incluyendo la relación con sus miembros.
    """
    miembros = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=User.objects.all()  # Permite elegir miembros existentes
    )

    class Meta:
        model = Equipos
        fields = ['id', 'nombre', 'miembros']


# -----------------------------------------------
# SERIALIZADOR PARA PARTIDOS
# -----------------------------------------------
class PartidoSerializer(serializers.ModelSerializer):
    """
    Serializador para el modelo Partidos.
    Convierte las instancias de partidos a JSON.
    """
    class Meta:
        model = Partidos
        fields = ['id', 'equipo_local', 'equipo_visitante', 'fecha', 'cancha']


# -----------------------------------------------
# SERIALIZADOR PARA COMENTARIOS
# -----------------------------------------------
class ComentarioSerializer(serializers.ModelSerializer):
    """
    Serializador para el modelo Comentarios.
    Incluye el nombre del usuario que realizó el comentario.
    """
    user = serializers.ReadOnlyField(source='user.username')  # Muestra solo el nombre de usuario

    class Meta:
        model = Comentarios
        fields = '__all__'  # Incluye todos los campos del modelo


# -----------------------------------------------
# SERIALIZADOR PARA CANCHAS
# -----------------------------------------------
class CanchaSerializer(serializers.ModelSerializer):
    """
    Serializador para el modelo Canchas.
    Incluye los comentarios relacionados y detalles de la cancha.
    """
    comentarios = ComentarioSerializer(many=True, read_only=True)  # Relación inversa: muestra los comentarios

    class Meta:
        model = Canchas
        fields = ['id', 'nombre', 'direccion', 'capacidad', 'latitud', 'longitud', 'comentarios', 'imagen_url']
        read_only_fields = ['imagen_url']  # Solo lectura: la URL de la imagen se genera automáticamente
