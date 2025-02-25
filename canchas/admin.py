# Decompiled with PyLingual (https://pylingual.io)
# Internal filename: C:\Users\villa\Django\kicknplay\canchas\admin.py
# Bytecode version: 3.12.0rc2 (3531)
# Source timestamp: 2025-02-25 21:22:20 UTC (1740518540)

from django.contrib import admin
from .models import Canchas, Equipos, Comentarios, Partidos
admin.site.register(Canchas)
admin.site.register(Equipos)
admin.site.register(Comentarios)
admin.site.register(Partidos)