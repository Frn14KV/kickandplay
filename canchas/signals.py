from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile

# Crear automáticamente el perfil del usuario cuando se crea un nuevo usuario
@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    if created:  # Solo cuando el usuario es creado
        UserProfile.objects.create(user=instance)

# Guardar automáticamente el perfil del usuario cuando se guarda el usuario
@receiver(post_save, sender=User)
def guardar_perfil_usuario(sender, instance, **kwargs):
    instance.userprofile.save()
