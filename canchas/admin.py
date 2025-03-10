from django.contrib import admin
from django.contrib.admin import AdminSite
from .models import Canchas, Equipos, Comentarios, Partidos, Evento

class MiAdminSite(AdminSite):
    site_header = "Kick&Play Admin"
    site_title = "Panel Administrativo Kick&Play"
    index_title = "Bienvenido al Administrador de Kick&Play"

class CanchaAdmin(admin.ModelAdmin):
    readonly_fields = ('latitud', 'longitud')  # Campos de solo lectura
    list_display = ('nombre', 'direccion', 'latitud', 'longitud')  # Campos visibles en la lista
    search_fields = ('nombre', 'direccion')  # Habilitar la búsqueda por nombre o dirección

admin_site = MiAdminSite(name='miadmin')   
admin.site.register(Canchas, CanchaAdmin)
#admin.site.register(Canchas)
admin.site.register(Equipos)
admin.site.register(Comentarios)
admin.site.register(Partidos)
admin.site.register(Evento)