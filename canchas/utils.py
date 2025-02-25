# Decompiled with PyLingual (https://pylingual.io)
# Internal filename: C:\Users\villa\Django\kicknplay\canchas\utils.py
# Bytecode version: 3.12.0rc2 (3531)
# Source timestamp: 2025-02-25 21:22:20 UTC (1740518540)

from django.core.mail import send_mail
from django.conf import settings
import requests

def obtener_coordenadas(direccion):
    API_KEY = 'AIzaSyBhIssxZqO6LEianMabpvH0Fur5yVxpBxI'
    url = f'https://maps.googleapis.com/maps/api/geocode/json?address={direccion}&key={API_KEY}'
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if data['status'] == 'OK':
            coordenadas = data['results'][0]['geometry']['location']
            print('error')
            return (coordenadas['lat'], coordenadas['lng'])
        print('eeroro Api')
        return
    except requests.exceptions.RequestException as e:
        print(f'error de red {e}')
        return None
    except (KeyError, IndexError):
        print('error processo')
        return (None, None)
    else:
        pass

def enviar_correo(usuario, asunto, mensaje):
    send_mail(asunto, mensaje, settings.EMAIL_HOST_USER, [usuario.email], fail_silently=False)