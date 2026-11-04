# Arquitectura y Stack Tecnológico
## Sistema de Gestión de Capacitaciones Docentes y Administrativas

---

## 1. Justificación del Stack Seleccionado: Python, Django y PostgreSQL

Para garantizar un sistema robusto, de fácil mantenimiento institucional, con alta capacidad de procesamiento de datos y un perfil de seguridad estricto, se ha seleccionado el stack **Python 3.11+ con Django 5.x y PostgreSQL 15+**:

### 1.1 Backend y Aplicación Web: Python con Django 5.x
* **¿Por qué Django para la Universidad?**
  * **Panel de Administración Listo para Usar (`django-admin`):** Resuelve de inmediato el requerimiento 5.7 (*"administración de catálogos para poder crecer sin tocar código"*). Con solo registrar los modelos, el personal administrativo dispone de un panel seguro y potente para dar de alta nuevas facultades, áreas de formación, modalidades y proveedores.
  * **Manejo Seguro de Hojas de Excel:** Al estar basado en Python, Django se conecta de forma directa con librerías de alto rendimiento como `pandas` y `openpyxl`, procesando importaciones masivas de miles de registros en segundos con validación estricta de tipos de datos y sanitización previa.
  * **Seguridad Nativa Probada en Producción:** Django incluye protección automática contra vulnerabilidades críticas del **OWASP Top 10** (inyecciones SQL, Cross-Site Scripting XSS, Cross-Site Request Forgery CSRF y clickjacking), además de un sistema criptográfico probado para contraseñas de usuarios.
  * **Django ORM y Migraciones Automáticas:** Control estricto de versiones de la base de datos a través de `python manage.py makemigrations` y `migrate`, garantizando consistencia y cero desajustes entre el código y la base de datos.
  * **Arquitectura Unificada (Baterías Incluidas):** Al ser un framework completo, no requiere mantener repositorios ni servidores separados para frontend y backend, reduciendo los costos de mantenimiento y la superficie de ataque para el departamento de TI de la universidad.

### 1.2 Base de Datos: PostgreSQL 15+
* **¿Por qué PostgreSQL?**
  * **Estándar Empresarial y Académico:** Es el motor relacional de código abierto más utilizado en entornos universitarios por su fiabilidad y cero costo de licenciamiento.
  * **Integridad Transaccional Estricta (ACID):** Vital para registrar presupuestos (presupuestado vs. ejecutado) e historiales formativos interanuales que nunca deben corromperse ni sobrescribirse.
  * **Seguridad en la Base de Datos:** Soporte para usuarios con privilegios mínimos (Principle of Least Privilege), conexiones encriptadas con SSL/TLS y triggers para bitácoras de auditoría inmutables (*Append-Only*).
  * **Campos JSONB:** Permite almacenar metadatos y configuraciones personalizadas de auditoría y catálogos sin necesidad de modificar la estructura de las tablas.

### 1.3 Frontend e Interfaz de Usuario
* **Plantillas Django (DTL) con Tailwind CSS / Bootstrap:**
  * Interfaz limpia, ágil y profesional, diseñada pensando en usuarios habituados a tablas de datos.
  * Tableros de control y gráficas de indicadores mediante **Chart.js** (interactivo, ligero y responsivo).
  * Filtros dinámicos y búsquedas rápidas en tiempo real.

---

## 2. Diagrama de Arquitectura de la Solución

```
+──────────────────────────────────────────────────────────────────────────+
|                              CAPA CLIENTE                                |
|  [Navegador Web / Docentes]     [Coordinadores / Gestores]   [Directivos]|
+─────────────────────────────────────┬────────────────────────────────────+
                                      │ HTTPS (TLS 1.3 Obligatorio)
                                      ▼
+──────────────────────────────────────────────────────────────────────────+
|                       SERVIDOR WEB Y REVERSE PROXY                       |
|                                                                          |
|                            [ Nginx Reverse Proxy ]                       |
|           ├──> Cabeceras de Seguridad (HSTS, CSP, X-Frame-Options)       |
|           ├──> Servir Archivos Estáticos / Evidencias (Sin ejecución)    |
|           ├──> Limitación de Tasa de Peticiones (Rate Limiting Anti-DoS) |
|           └──> Redirección WSGI a Gunicorn / Django Application          |
+─────────────────────────────────────┬────────────────────────────────────+
                                      │
                                      ▼
+──────────────────────────────────────────────────────────────────────────+
|                         APLICACIÓN WEB (DJANGO 5.x)                      |
|                                                                          |
|  [ Middleware de Autenticación, Sesiones y Seguridad CSRF ]              |
|  [ Filtro Anti-Fuerza Bruta (django-axes) ]                              |
|         │                                                                |
|         ├───> [ Panel Django Admin (Gestión de Catálogos Dinámicos) ]    |
|         ├───> [ Módulo de Capacitaciones y Eventos Formativos ]          |
|         ├───> [ Módulo de Participantes e Historial Acumulativo ]        |
|         ├───> [ Módulo Presupuestal (Planificado vs. Ejecutado) ]         |
|         ├───> [ Motor Seguro de Importación Excel (Pandas / DefusedXML) ]|
|         └───> [ Motor de Dashboards y Reportes (Chart.js / ReportLab) ]  |
+──────────────────┬─────────────────────────────┬─────────────────────────+
                   │                             │
                   ▼                             ▼
+──────────────────────────────────────+  +────────────────────────────────+
|        BASE DE DATOS RELACIONAL      |  |   ALMACENAMIENTO DE ARCHIVOS   |
|                                      |  |                                |
|          [ PostgreSQL 15+ ]          |  |  [ Almacenamiento Local Seguro |
|  - Tablas Normalizadas (Django ORM)  |  |    o Volumen Persistente Docker]|
|  - Índices de Búsqueda Rápida        |  |  - Nombres UUID4 Aleatorios    |
|  - Histórico Acumulativo             |  |  - Permisos de solo lectura    |
|  - Auditoría Inmutable (Append-Only) |  |  - Sin permisos de ejecución   |
+──────────────────────────────────────+  +────────────────────────────────+
```

---

## 3. Matriz de Mitigación de Vulnerabilidades (OWASP Top 10)

Para blindar la plataforma contra incidentes de seguridad que afecten la confidencialidad, integridad o disponibilidad de los datos universitarios, se implementan las siguientes salvaguardas:

### 3.1 Vulnerabilidades en la Carga de Archivos (Diplomas y Evidencias)
* **Riesgo:** Subida de scripts ejecutables disfrazados de documentos (`.php`, `.py`, `.exe`, `.html`, `.svg` con XSS malicioso) o nombres con *Path Traversal* (`../../etc/passwd`).
* **Medidas de Seguridad Implementadas:**
  1. **Renombrado Forzoso con UUIDv4:** Ningún archivo conserva su nombre original en el disco. Se almacena como `550e8400-e29b-41d4-a716-446655440000.pdf`.
  2. **Validación de Magic Bytes (Tipo MIME Real):** No se confía en la extensión del archivo ni en la cabecera enviada por el navegador. Se analiza el contenido binario con `python-magic` para verificar que el archivo es auténticamente un PDF, PNG o JPEG.
  3. **Lista Blanca Estricta de Extensiones:** Solo se permiten extensiones explícitas: `.pdf`, `.png`, `.jpg`, `.jpeg`. Archivos ejecutables o SVG están estrictamente prohibidos.
  4. **Límite de Tamaño por Archivo:** Máximo 10 MB por documento para mitigar ataques de denegación de servicio (DoS) por llenado de disco.
  5. **Directorio sin Permisos de Ejecución (`noexec`):** En Nginx, la carpeta `/media/` está configurada para servir únicamente archivos estáticos binarios, deshabilitando cualquier ejecución de scripts en el servidor.
  6. **Descarga Protegida con Verificación de Permisos:** Los diplomas individuales de un docente no son públicos; la vista de Django valida que el usuario autenticado sea el dueño del diploma o un administrador antes de servir el archivo.

### 3.2 Vulnerabilidades en la Importación y Exportación de Excel / CSV
* **Riesgo 1: Inyección de Fórmulas CSV (Formula / CSV Injection):** Filas maliciosas que inician con caracteres de fórmulas (`=`, `+`, `-`, `@`, `|`, `%`) que pueden ejecutar macros o extraer datos al ser abiertas en Microsoft Excel por directivos de la universidad.
* **Medidas Implementadas:**
  * Al procesar o exportar, cualquier celda que comience con `=,+,-,@,|,tab` se neutraliza anteponiendo un carácter de escape (comilla simple `'`).
* **Riesgo 2: Bombas de Descompresión y Ataques XML (XXE en archivos `.xlsx`):**
  * Los archivos `.xlsx` son contenedores ZIP con XML. Se utiliza la librería `defusedxml` para deshabilitar la resolución de entidades externas en los analizadores XML.
  * Límite de tamaño máximo del archivo de Excel a 15 MB y límite de filas por importación a 5,000 registros por lote.

### 3.3 Control de Acceso Roto (Broken Access Control - BOLA / IDOR)
* **Riesgo:** Que un docente o gestor manipule parámetros en la URL (ej. cambiar `/participante/10/` por `/participante/11/`) para acceder a historiales o presupuestos de otra persona o facultad.
* **Medidas Implementadas:**
  * **Autorización a Nivel de Objeto:** En cada vista de Django, las consultas filtran obligatoriamente por el contexto del usuario autenticado:
    ```python
    # Ejemplo de filtro seguro en vista de Django
    if not request.user.is_staff:
        # Los docentes solo ven sus propios registros
        queryset = Participacion.objects.filter(persona__usuario=request.user)
    elif request.user.groups.filter(name='Gestor').exists():
        # Los gestores solo ven su facultad asignada
        queryset = Participacion.objects.filter(capacitacion__facultad=request.user.persona.facultad)
    ```
  * Uso de identificadores UUIDv4 en lugar de IDs numéricos secuenciales en URLs públicas, eliminando la predictibilidad de registros.

### 3.4 Protección Contra Ataques de Fuerza Bruta y Gestión de Sesiones
* **Fuerza Bruta:** Integración del paquete `django-axes` para bloquear temporalmente direcciones IP y cuentas tras 5 intentos fallidos consecutivos de inicio de sesión durante 15 minutos.
* **Política de Contraseñas:** Validadores integrados de Django configurados:
  * Mínimo 10 caracteres.
  * No permitir contraseñas comunes ni similares a los datos del usuario.
  * Combinación de números, letras y símbolos.
* **Cifrado de Credenciales:** Algoritmo de hashing **PBKDF2 con SHA-256** (o Argon2) con sal única por usuario.

### 3.5 Endurecimiento de Parámetros de Django para Producción (`settings.py`)
```python
# Configuración de Seguridad para Servidor Universitario
DEBUG = False
ALLOWED_HOSTS = ['capacitaciones.universidad.edu.sv', 'localhost']

# Protección HTTPS y Cookies
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_HTTPONLY = True

# Cabeceras de Seguridad del Navegador
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000 # 1 año HSTS
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

### 3.6 Inmutabilidad de la Bitácora de Auditoría
* La tabla `auditoria_log` en PostgreSQL cuenta con reglas/triggers a nivel de base de datos que **impiden operaciones de `UPDATE` o `DELETE`**, garantizando que ningún usuario (ni siquiera administradores del sistema) pueda borrar evidencias o alterar el historial de cambios.

---

## 4. Despliegue Seguro con Docker Compose

```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    restart: always
    environment:
      POSTGRES_DB: capacitaciones_db
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./backups:/backups
    networks:
      - internal_network

  web:
    build: .
    restart: always
    user: "1000:1000" # Ejecución como usuario sin privilegios root
    command: gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 60
    environment:
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@db:5432/capacitaciones_db
      SECRET_KEY: ${DJANGO_SECRET_KEY}
      DEBUG: "False"
    volumes:
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    depends_on:
      - db
    networks:
      - internal_network

  nginx:
    image: nginx:alpine
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/conf.d/default.conf:ro
      - ./certs:/etc/nginx/ssl:ro
      - static_volume:/app/staticfiles:ro
      - media_volume:/app/media:ro
    depends_on:
      - web
    networks:
      - internal_network

volumes:
  pgdata:
  static_volume:
  media_volume:

networks:
  internal_network:
    driver: bridge
```

* **Red Aislada (`internal_network`):** La base de datos PostgreSQL **no expone puertos al exterior** (no hay `5432:5432` en el host), siendo accesible únicamente por la aplicación Django dentro de la red interna de Docker.
* **Ejecución No-Root:** El contenedor web corre bajo un usuario sin privilegios `UID 1000`, mitigando fugas de contenedor al sistema operativo anfitrión.
