from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from .utils import obtener_coordenadas  # Importa función para obtener coordenadas

# -----------------------------------------------
# MODELOS RELACIONADOS CON USUARIOS
# -----------------------------------------------
class UserProfile(models.Model):
    """
    Extiende el modelo User para agregar información adicional del usuario.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='user_profile')
    bio = models.TextField(blank=True, null=True)
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return self.user.username


class CustomLoginForm(AuthenticationForm):
    """
    Personaliza el formulario de autenticación para que los campos sean más visuales.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = field.label

# -----------------------------------------------
# MODELOS RELACIONADOS CON CANCHAS Y COMENTARIOS
# -----------------------------------------------
class Canchas(models.Model):
    """
    Representa una cancha deportiva con datos básicos como nombre, dirección, y capacidad.
    También incluye coordenadas geográficas (latitud y longitud).
    """
    nombre = models.CharField(max_length=100)
    direccion = models.CharField(max_length=255)
    capacidad = models.PositiveIntegerField(default=50)
    imagen_url = models.URLField(blank=True, null=True)
    latitud = models.FloatField(null=True, blank=True)
    longitud = models.FloatField(null=True, blank=True)

    def save(self, *args, **kwargs):
        """
        Sobrescribe el método save para calcular las coordenadas
        geográficas automáticamente si no están definidas.
        """
        if self.direccion and (self.latitud is None or self.longitud is None):
            coordenadas = obtener_coordenadas(self.direccion)
            if coordenadas:
                self.latitud, self.longitud = coordenadas
        super().save(*args, **kwargs)

    def get_imagen_url(self):
        """
        Devuelve la URL de la imagen si existe; de lo contrario, una predeterminada.
        """
        return self.imagen_url or "https://fluofgltdazuwfgpnctl.supabase.co/storage/v1/object/public/media//k&plogo.jpg"

    def calificacion_promedio(self):
        """
        Calcula la calificación promedio de la cancha a partir de sus comentarios.
        """
        comentarios = self.comentarios.all()
        if comentarios.exists():
            return comentarios.aggregate(models.Avg('calificacion'))['calificacion__avg']
        return 0

    def total_comentarios(self):
        """
        Devuelve la cantidad total de comentarios asociados a la cancha.
        """
        return self.comentarios.count()

    def __str__(self):
        return self.nombre


class Comentarios(models.Model):
    """
    Representa un comentario realizado por un usuario sobre una cancha.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comentarios")
    cancha = models.ForeignKey(Canchas, on_delete=models.CASCADE, related_name="comentarios")
    texto = models.TextField()
    calificacion = models.IntegerField(
        default=1, choices=[(i, str(i)) for i in range(1, 6)]
    )  # Calificación de 1 a 5
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} - {self.cancha.nombre}'

# -----------------------------------------------
# MODELOS RELACIONADOS CON EQUIPOS Y PARTIDOS
# -----------------------------------------------
class Equipos(models.Model):
    """
    Representa un equipo que puede tener múltiples usuarios como miembros.
    """
    nombre = models.CharField(max_length=100)
    miembros = models.ManyToManyField(User, related_name='equipos')

    def __str__(self):
        return self.nombre


class Partidos(models.Model):
    """
    Representa un partido entre dos equipos que tiene lugar en una cancha en una fecha específica.
    """
    equipo_local = models.ForeignKey(Equipos, related_name='partidos_local', on_delete=models.CASCADE)
    equipo_visitante = models.ForeignKey(Equipos, related_name='partidos_visitante', on_delete=models.CASCADE)
    fecha = models.DateField()
    cancha = models.ForeignKey(Canchas, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.equipo_local} vs {self.equipo_visitante} en {self.cancha}'

# -----------------------------------------------
# MODELOS RELACIONADOS CON RESERVAS Y EVENTOS
# -----------------------------------------------
class Reserva(models.Model):
    """
    Representa una reserva realizada por un usuario para una cancha específica.
    """
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    cancha = models.ForeignKey(Canchas, on_delete=models.CASCADE)
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
        default='pendiente',
    )

    def __str__(self):
        return f"Reserva de {self.usuario.username} en {self.cancha.nombre} el {self.fecha_reserva}"


class Evento(models.Model):
    """
    Representa un evento asociado a una reserva, con tipo (público o privado).
    """
    TIPO_EVENTO_CHOICES = [
        ('publico', 'Público'),
        ('privado', 'Privado'),
    ]

    reserva = models.OneToOneField(
        Reserva, on_delete=models.CASCADE, related_name="evento"
    )
    titulo = models.CharField(max_length=255)
    descripcion = models.TextField()
    tipo_evento = models.CharField(
        max_length=10, choices=TIPO_EVENTO_CHOICES, default='publico'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.titulo} ({self.get_tipo_evento_display()})"
