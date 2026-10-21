import urllib.request
import urllib.error

urls = [
    'http://127.0.0.1:8000/',
    'http://127.0.0.1:8000/capacitaciones/',
    'http://127.0.0.1:8000/capacitaciones/calendario/',
    'http://127.0.0.1:8000/personas/portal/',
    'http://127.0.0.1:8000/personas/matriz/',
    'http://127.0.0.1:8000/costos/',
    'http://127.0.0.1:8000/catalogos/',
    'http://127.0.0.1:8000/administracion/',
]

for url in urls:
    try:
        req = urllib.request.urlopen(url, timeout=5)
        print(f"[OK] {url} -> HTTP {req.status}")
    except urllib.error.HTTPError as e:
        print(f"[HTTP ERR] {url} -> HTTP {e.code}")
    except Exception as e:
        print(f"[ERR] {url} -> {e}")
