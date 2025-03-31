# Decompiled with PyLingual (https://pylingual.io)
# Internal filename: C:\Users\villa\Django\kicknplay\canchas\urls.py
# Bytecode version: 3.12.0rc2 (3531)
# Source timestamp: 2025-02-25 21:22:20 UTC (1740518540)

from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter
from .views import CanchaViewSet, EquipoViewSet, PartidoViewSet, ComentarioViewSet, ListaEventosView, obtener_informacion_usuario
router = DefaultRouter()
router.register(r'canchas', CanchaViewSet, basename='cancha')
router.register('equipos', EquipoViewSet)
router.register('partidos', PartidoViewSet)
router.register('comentarios', ComentarioViewSet)
#router.register('eventos',ListaEventosView)

urlpatterns = [
    path('', include(router.urls)),
    path('obtener_usuario/', obtener_informacion_usuario, name='obtener_usuario'),

    # Rutas de canchas
    #path('canchas/', views.lista_canchas, name='lista_canchas'),

    #path('canchas/', views.lista_canchas, name='lista_canchas'),  # Ruta para la lista de canchas
    # Rutas de eventos
   # path('eventos/', views.lista_eventos, name='lista_eventos'),
   # path('eventos/<int:id>/', views.detalle_evento, name='detalle_evento'),
    #ruta de calendario
   # path('calendario/', views.calendario_eventos, name='calendario_eventos'),
] 