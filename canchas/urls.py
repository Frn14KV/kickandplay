# Decompiled with PyLingual (https://pylingual.io)
# Internal filename: C:\Users\villa\Django\kicknplay\canchas\urls.py
# Bytecode version: 3.12.0rc2 (3531)
# Source timestamp: 2025-02-25 21:22:20 UTC (1740518540)

from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter
from .views import CanchaViewSet, EquipoViewSet, PartidoViewSet, ComentarioViewSet, ListaEventosView
router = DefaultRouter()
router.register('canchas', CanchaViewSet)
router.register('equipos', EquipoViewSet)
router.register('partidos', PartidoViewSet)
router.register('comentarios', ComentarioViewSet)
#router.register('eventos',ListaEventosView)

urlpatterns = [
    path('', include(router.urls)),
    # Rutas de canchas
    path('canchas/', views.lista_canchas, name='lista_canchas'),

    # Rutas de eventos
    path('eventos/', views.lista_eventos, name='lista_eventos'),
    path('eventos/<int:id>/', views.detalle_evento, name='detalle_evento'),
]