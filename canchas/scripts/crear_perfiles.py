from django.contrib.auth.models import User
from canchas.models import UserProfile

usuarios = User.objects.all()
for usuario in usuarios:
    UserProfile.objects.get_or_create(user=usuario)