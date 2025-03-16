# Decompiled with PyLingual (https://pylingual.io)
# Internal filename: C:\Users\villa\Django\kicknplay\kicknplay\urls.py
# Bytecode version: 3.12.0rc2 (3531)
# Source timestamp: 2025-02-25 21:22:20 UTC (1740518540)

"""
URL configuration for kicknplay project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from canchas import views
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
urlpatterns = [
    #api
    path('api/token/',                                  TokenObtainPairView.as_view(), name='token_obtain_pair'), 
    path('api/token/refresh/',                          TokenRefreshView.as_view(), name='token_refresh'), 
    # Ajusta según el nombre de tu aplicación
    path('api/', include('canchas.urls')), 
    #api
    path('admin/',                                      admin.site.urls), 
    # Ruta para la página principal
    path('',                                            views.home, name='home'), 
    # Ruta para la lista de canchas
    path('canchas/',                                    views.lista_canchas, name='canchas'),  
    path('canchas/<int:cancha_id>/',                    views.detalle_cancha, name='detalle_cancha'),
    path('canchas/<int:cancha_id>/dejar_comentario/',   views.dejar_comentario, name='dejar_comentario'),
    # Ruta para la lista de Eventos
    path('eventos/',                                    views.lista_eventos, name='lista_eventos'),
    path('eventos/<int:evento_id>/',                    views.detalle_evento, name='detalle_evento'),
     # Otras rutas
    path('evento/editar/<int:evento_id>/',              views.editar_evento, name='editar_evento'),
    #path('calendario/',                                    views.calendario_eventos, name='calendario_eventos'),
    path('calendario/cancha/<int:cancha_id>/',          views.calendario_cp, name='calendario_cancha'),
    path('api/eventos/<int:evento_id>/',                views.obtener_evento, name='obtener_evento'),
    path('calendario/eliminar/<int:evento_id>/',        views.eliminar_evento, name='eliminar_evento'),
    #mapa
    path('mapa/',                                       views.mapa_canchas, name='mapa_canchas'),
    #lista reservas
    path('reservas/nueva/',                             views.reservar_cancha, name='crear_reserva'),
    path('reservar_cancha/<int:cancha_id>/',            views.reservar_cancha, name='reservar_cancha'),
    path('confirmacion_reserva/<int:reserva_id>/',      views.confirmacion_reserva, name='confirmacion_reserva'),
    path('reservas/',                                   views.lista_reservas, name='lista_reservas'),
    path('reservas/eliminar/<int:reserva_id>/',         views.cancelar_reserva, name='eliminar_reserva'),
    path('reservas/<int:reserva_id>/',                  views.detalle_reserva, name='detalle_reserva'),
    # Otras rutas
    path('sobre-nosotros/',                             views.sobre_nosotros, name='sobre_nosotros'),
    #path('eventos/', include('canchas.urls')), 
    #path('canchas/', include('canchas.urls')),
    # registro en inicio de session
    path('registro/',                                   views.registro, name='registro'),
    path('login/',                                      views.CustomLoginView.as_view(), name='login'),
    path('logout/',                                     views.CustomLogoutView.as_view(), name='logout'),


] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
