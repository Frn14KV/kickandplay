#!/usr/bin/env bash
# 🚀 Script de arranque para Render: Django con Gunicorn

# 🧮 Ejecutar migraciones de base de datos
python manage.py migrate --noinput

# 🎨 Recolectar archivos estáticos (para Whitenoise)
python manage.py collectstatic --noinput

# 🔥 Iniciar Gunicorn en el puerto asignado por Render
gunicorn kickandplay.wsgi:application --bind 0.0.0.0:$PORT
