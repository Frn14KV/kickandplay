from django.db import models
from .utils import obtener_coordenadas  # Importa la función desde utils
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm

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

class Reserva(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)  # Usuario que hace la reserva
    cancha = models.ForeignKey(Canchas, on_delete=models.CASCADE)  # Cancha reservada
    fecha_reserva = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    estado = models.CharField(
        max_length=50,
        choices=[
            ('pendiente', 'Pendiente'),
            ('confirmada', 'Confirmada'),
            ('cancelada', 'Cancelada'),
        ],
        default='pendiente',  # Valor predeterminado para evitar nulos
    )

    def __str__(self):
        return f"Reserva de {self.usuario.username} en {self.cancha.nombre} el {self.fecha}"
    
class Evento(models.Model):
    TIPO_EVENTO_CHOICES = [
        ('publico', 'Público'),
        ('privado', 'Privado'),
    ]

    reserva = models.OneToOneField(
        Reserva,
        on_delete=models.CASCADE,
        related_name="evento",
    )  # Relación uno-a-uno con Reserva
    titulo = models.CharField(max_length=255)
    descripcion = models.TextField()
    tipo_evento = models.CharField(
        max_length=10, choices=TIPO_EVENTO_CHOICES, default='publico'
    )  # Público o privado
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.titulo} ({self.get_tipo_evento_display()})"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True, null=True)
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)  # Nueva información editable
    phone_number = models.CharField(max_length=15, blank=True, null=True)  # Nuevo campo para teléfono

    def __str__(self):
        return self.user.username
    
class CustomLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = field.label
