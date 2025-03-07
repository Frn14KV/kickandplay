# Decompiled with PyLingual (https://pylingual.io)
# Internal filename: C:\Users\villa\Django\kicknplay\canchas\utils.py
# Bytecode version: 3.12.0rc2 (3531)
# Source timestamp: 2025-02-25 21:22:20 UTC (1740518540)

from django.core.mail import send_mail
from django.conf import settings
import requests
from math import radians, sin, cos, sqrt, atan2
from supabase import create_client

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
    send_mail(
        asunto, mensaje, 
        settings.EMAIL_HOST_USER, 
        [usuario.email], 
        fail_silently=False)

def upload_to_supabase(file, file_name):
    supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    bucket = settings.SUPABASE_BUCKET

    response = supabase.storage.from_(bucket).upload(file_name, file.read(), {"upsert": True})

    if response.get("error"):
        raise Exception(f"Error al subir el archivo: {response['error']['message']}")

    public_url = f"{settings.SUPABASE_URL}/storage/v1/object/public/{bucket}/{file_name}"
    return public_url

def calcular_distancia(lat1, lon1, lat2, lon2):
    R = 6371  # Radio de la Tierra en km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c
