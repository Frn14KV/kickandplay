from django.db import models
from django.contrib.auth.models import User

class Canchas(models.Model):
    nombre = models.CharField(max_length=100)
    direccion = models.CharField(max_length=255)
    capacidad = models.PositiveIntegerField(default=50)
    #imagen = models.ImageField(upload_to='canchas/', blank=True, null=True)  # Imagen opcional
    imagen_url = models.URLField(blank=True, null=True)
    latitud = models.FloatField(null=True, blank=True)
    longitud = models.FloatField(null=True, blank=True)

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
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()
    cancha = models.ForeignKey(Canchas, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.titulo} - {self.cancha.nombre}"

class Reserva(models.Model):
    cancha = models.ForeignKey(Canchas, on_delete=models.CASCADE, related_name='reservas')
    fecha_reserva = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    reservado_por = models.ForeignKey(User, on_delete=models.CASCADE)  # Usuario que hizo la reserva

    def __str__(self):
        return