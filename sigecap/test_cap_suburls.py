import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sigecap.settings')
django.setup()

import urllib.request
from apps.capacitaciones.models import Capacitacion

cap = Capacitacion.objects.first()
if cap:
    sub_urls = [
        f'http://127.0.0.1:8000/capacitaciones/{cap.id}/',
        f'http://127.0.0.1:8000/capacitaciones/{cap.id}/duplicar/',
        f'http://127.0.0.1:8000/capacitaciones/{cap.id}/qr-asistencia/',
        f'http://127.0.0.1:8000/capacitaciones/{cap.id}/asistencia-qr/',
        f'http://127.0.0.1:8000/capacitaciones/{cap.id}/encuesta/',
    ]
    for url in sub_urls:
        try:
            req = urllib.request.urlopen(url, timeout=5)
            print(f"[OK] {url} -> HTTP {req.status}")
        except Exception as e:
            print(f"[ERR] {url} -> {e}")
else:
    print("No capacitaciones found to test.")
