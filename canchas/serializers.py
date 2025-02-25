# Decompiled with PyLingual (https://pylingual.io)
# Internal filename: C:\Users\villa\Django\kicknplay\canchas\serializers.py
# Bytecode version: 3.12.0rc2 (3531)
# Source timestamp: 2025-02-25 21:22:20 UTC (1740518540)

from rest_framework import serializers
from .models import Canchas, Equipos, Partidos, Comentarios
from django.contrib.auth.models import User

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
        fields = '__all__'