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
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'), 
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'), 
    
    path('admin/', admin.site.urls), 
         # Ruta para la página principal
    path('', views.home, name='home'), 
        # Ruta para la lista de canchas
    path('canchas/', views.lista_canchas, name='canchas'),  
    #path('canchas/', include('canchas.urls')),
        # Ruta para la lista de Eventos
    #path('eventos/', include('canchas.urls')), 
    path('eventos/', views.lista_eventos, name='lista_eventos'),
    path('eventos/<int:id>/', views.detalle_evento, name='detalle_evento'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)