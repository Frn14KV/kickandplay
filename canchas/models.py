from django.db import models
from .utils import obtener_coordenadas  # Importa la función desde utils
from django.contrib.auth.models import User

class Canchas(models.Model):
    nombre = models.CharField(max_length=100)
    direccion = models.CharField(max_length=255)
    capacidad = models.PositiveIntegerField(default=50)
    imagen_url = models.URLField(blank=True, null=True)
    latitud = models.FloatField(null=True, blank=True)
    longitud = models.FloatField(null=True, blank=True)

    def save(self, *args, **kwargs):
        # Si no hay latitud y longitud, intenta obtenerlas automáticamente
        if self.direccion and (self.latitud is None or self.longitud is None):
            coordenadas = obtener_coordenadas(self.direccion)
            if coordenadas:
                self.latitud, self.longitud = coordenadas
        super().save(*args, **kwargs)

    def get_imagen_url(self):
        """Retorna la URL de la imagen o una predeterminada."""
        return self.imagen_url or "https://fluofgltdazuwfgpnctl.supabase.co/storage/v1/object/public/media//k&plogo.jpg"

    def __str__(self):
        return self.nombre
    
    def calificacion_promedio(self):
        comentarios = self.comentarios.all()  # Relación inversa desde Comentario
        if comentarios.exists():
            return comentarios.aggregate(models.Avg('calificacion'))['calificacion__avg']
        return 0

    def total_comentarios(self):
        return self.comentarios.count()

class Comentarios(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comentarios")
    cancha = models.ForeignKey(Canchas, on_delete=models.CASCADE, related_name="comentarios")
    texto = models.TextField()
    calificacion = models.IntegerField(default=1, choices=[(i, str(i)) for i in range(1, 6)])
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} - {self.cancha.nombre}'

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
    
class Evento(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)  # Relación con el usuario
    cancha = models.ForeignKey(Canchas, on_delete=models.CASCADE, blank=True, null=True)  # Relación con la cancha
    titulo = models.CharField(max_length=100)  # Título del evento
    descripcion = models.TextField(blank=True, null=True)  # Descripción opcional
    fecha = models.DateField()  # Fecha del evento
    hora_inicio = models.TimeField()  # Hora de inicio
    hora_fin = models.TimeField()  # Hora de fin

    def __str__(self):
        return f"{self.titulo} ({self.fecha})"

class Reserva(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)  # Usuario que hace la reserva
    cancha = models.ForeignKey(Canchas, on_delete=models.CASCADE)  # Cancha a reservar
    fecha_reserva = models.DateField()  # Fecha de la reserva
    hora_inicio = models.TimeField()  # Hora de inicio
    hora_fin = models.TimeField()  # Hora de fin

    def __str__(self):
        return f"Reserva de {self.usuario} para {self.cancha.nombre} en {self.fecha_reserva}"
