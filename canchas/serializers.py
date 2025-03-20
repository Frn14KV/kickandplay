# Decompiled with PyLingual (https://pylingual.io)
# Internal filename: C:\Users\villa\Django\kicknplay\canchas\serializers.py
# Bytecode version: 3.12.0rc2 (3531)
# Source timestamp: 2025-02-25 21:22:20 UTC (1740518540)

from rest_framework import serializers
from .models import Canchas, Equipos, Partidos, Comentarios, Evento, Reserva
from django.contrib.auth.models import User


class ReservaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reserva
        fields = ['id', 'usuario', 'cancha', 'fecha_reserva', 'hora_inicio', 'hora_fin', 'estado']

class EventoSerializer(serializers.ModelSerializer):
    reserva = ReservaSerializer()  # Incluir detalles de la reserva asociada

    class Meta:
        model = Evento
        fields = ['id', 'titulo', 'descripcion', 'tipo_evento', 'fecha_creacion', 'reserva']


class EquipoSerializer(serializers.ModelSerializer):
    miembros = serializers.PrimaryKeyRelatedField(many=True, queryset=User.objects.all())

    class Meta:
        model = Equipos
        fields = ['id', 'nombre', 'miembros']

class PartidoSerializer(serializers.ModelSerializer):

    class Meta:
        model = Partidos
        fields = ['id', 'equipos_local', 'equipos_visitante', 'fecha_partido', 'cancha']

class ComentarioSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = Comentarios
        fields = '__all__'

class CanchaSerializer(serializers.ModelSerializer):
    comentarios = ComentarioSerializer(many=True, read_only=True)

    class Meta:
        model = Canchas
        fields = ['id', 'nombre', 'direccion', 'capacidad', 'disponible', 'latitud', 'longitud', 'fotos_url']
        read_only_fields = ['imagen_url']  # La URL de la foto se genera automáticamente