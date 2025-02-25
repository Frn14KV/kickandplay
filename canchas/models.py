from django.db import models
from django.contrib.auth.models import User

class Canchas(models.Model):
    nombre = models.CharField(max_length=100)
    direccion = models.CharField(max_length=255)
    disponible = models.BooleanField(default=True)
    reservado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_reserva = models.DateField(null=True, blank=True)
    latitud = models.FloatField(null=True, blank=True)
    longitud = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.nombre

class Equipos(models.Model):
    nombre = models.CharField(max_length=100)
    miembros = models.ManyToManyField(User, related_name='equipos')

    def __str__(seft):
        return seft.nombre

class Partidos(models.Model):
    equipo_local = models.ForeignKey(Equipos, related_name='partidos_local', on_delete=models.CASCADE)
    equipo_visitante = models.ForeignKey(Equipos, related_name='partidos_visitante', on_delete=models.CASCADE)
    fecha = models.DateField()
    cancha = models.ForeignKey(Canchas, on_delete=models.CASCADE)

    def __str__(seft):
        return f'{seft.equipo_local} vs {seft.equipo_visitante} en {seft.cancha}'

class Comentarios(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    cancha = models.ForeignKey(Canchas, related_name='comentarios', on_delete=models.CASCADE)
    texto = models.TextField()
    calificacion = models.IntegerField(default=1, choices=[(i, str(i)) for i in range(1, 6)])
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} - {self.cancha.nombre}'