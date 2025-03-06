# Decompiled with PyLingual (https://pylingual.io)
# Internal filename: C:\Users\villa\Django\kicknplay\canchas\admin.py
# Bytecode version: 3.12.0rc2 (3531)
# Source timestamp: 2025-02-25 21:22:20 UTC (1740518540)

from django.contrib import admin
from django.contrib.admin import AdminSite
from .models import Canchas, Equipos, Comentarios, Partidos, Evento

class MiAdminSite(AdminSite):
    site_header = "Kick&Play Admin"
    site_title = "Panel Administrativo Kick&Play"
    index_title = "Bienvenido al Administrador de Kick&Play"

admin_site = MiAdminSite(name='miadmin')   
admin.site.register(Canchas)
admin.site.register(Equipos)
admin.site.register(Comentarios)
admin.site.register(Partidos)
admin.site.register(Evento)