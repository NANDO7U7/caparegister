# Configuración y autorización de SIGECAP

## Inicio local seguro

Desde la raíz del repositorio, con el entorno virtual activado:

```powershell
cd sigecap
$env:DEBUG = 'True'
python manage.py check --settings=sigecap.local_settings
python manage.py runserver 127.0.0.1:8080 --settings=sigecap.local_settings
```

El perfil local es explícito y solo admite hosts de loopback. Conserva SQLite
local si no se configura otra base. No ejecuta migraciones ni crea usuarios.
Genera una clave secreta aleatoria en memoria si no hay una configurada; para
mantener sesiones entre arranques independientes, configura una clave privada
persistente mediante el entorno o un archivo `.env` ignorado por Git.

No uses el perfil local ni el servidor de desarrollo para publicar el sistema.

La variable `DEBUG` del entorno de algunas herramientas puede contener valores
como `release`. La configuración ahora rechaza valores no booleanos: establece
`True` explícitamente para local y `False` para producción. `ALLOWED_HOSTS` local
solo admite `localhost`, `127.0.0.1` y `[::1]`.

## Variables privadas y producción

El perfil por defecto es `production`. Sin configuración válida falla al arrancar,
antes de abrir la base. Una clave de al menos 50 caracteres debe generarse con un
generador criptográfico y guardarse fuera del repositorio. Por ejemplo, para
usarla solo en la consola actual sin imprimirla:

```powershell
$env:SECRET_KEY = python -c "import secrets; print(secrets.token_urlsafe(64))"
$env:SIGECAP_ENV = 'production'
$env:DEBUG = 'False'
$env:ALLOWED_HOSTS = 'sigecap.example.org'
```

Sustituye el host de ejemplo por el de tu instalación. El código no tiene clave
secreta ni contraseña PostgreSQL predeterminadas. Para PostgreSQL establece
`DB_ENGINE=django.db.backends.postgresql`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`,
`DB_HOST` y opcionalmente `DB_PORT` (5432). La contraseña debe proceder de tu
gestor de secretos o configuración privada; no la copies a documentación.
SQLite no local también requiere `DB_ENGINE` y `DB_NAME` explícitos.

`sigecap/.env.example` no contiene secretos. Puede copiarse a `sigecap/.env`
solo si no existe ya un archivo privado. El `.env` está ignorado por Git y las
variables del proceso tienen prioridad. Nunca publiques ese archivo.

Producción fuerza cookies seguras, redirección HTTPS y HSTS de una hora. No
habilita HSTS para subdominios ni preload sin conocer la infraestructura. Si hay
un proxy TLS, debe configurarse y comprobarse deliberadamente el tratamiento de
cabeceras de proxy; no se confía automáticamente en cabeceras enviadas por clientes.
El perfil local no fuerza HTTPS. `test_settings` siempre usa memoria, aunque el
entorno contenga credenciales o nombres de bases externas.

Docker Compose ya no tiene contraseñas predeterminadas y solo expone PostgreSQL
en loopback. No se ejecutó Docker ni se modificaron sus volúmenes existentes.

## Política mínima de permisos

Se usan permisos nativos de Django (`view`, `add`, `change`, `delete`) asignados
directamente o mediante grupos. No se crean permisos ni migraciones nuevas.

| Operación | Requisito |
| --- | --- |
| Usuarios y grupos, tanto en el panel propio como en Django Admin | Superusuario activo. Los permisos `auth.*` de un staff no bastan. |
| Consultar Catálogos | Superusuario o staff activo con `catalogos.view_<modelo>`. Solo se entregan los modelos que puede consultar. |
| Crear, editar o eliminar Catálogos | Superusuario o staff activo con `catalogos.add/change/delete_<modelo>`, según la acción. Se revisan ambas rutas web y las altas indirectas desde PIF. |
| Control de cursos en Administración | Staff activo con `capacitaciones.view_capacitacion`; cambiar estado exige `change_capacitacion`. |
| Auditoría administrativa | Staff activo con `core.view_auditlog`. No se permite editar la bitácora. |
| Altas/ediciones/bajas normales de cursos | Permiso funcional `capacitaciones.add/change/delete_capacitacion`; no requiere ser staff. |
| Alta/edición de personas y matrículas | `personas.add_persona`, `change_persona` o `change_matriculamatrizdocente`, respectivamente. |
| Inscripción y carga documental | `capacitaciones.add_participacion` y `add_evidencia`, respectivamente. |
| Bajas de participantes y evidencias dentro de un curso | Se mantiene el permiso funcional previo `capacitaciones.change_capacitacion`. |
| PIF: guardar e importar | Alta exige `add_capacitacion`, edición `change_capacitacion`, eliminación `delete_capacitacion`. Un ID de edición inexistente no se convierte en un alta. |

Los modelos de Catálogos son `facultad`, `areaformacion`, `tipomodalidad`,
`proveedor` y `proyecto`. Estar autenticado o tener `is_staff` por sí solo no
autoriza el mantenimiento. Un usuario sin sesión vuelve al login; las acciones
administrativas sin permiso devuelven 403 o redirigen al login en la gestión de
cuentas. `X-User-Role`, nombres especiales y campos enviados por el navegador no
otorgan permisos. La interfaz PIF recibe las capacidades del usuario desde Django.

Las operaciones PIF conservan su alcance agregado sobre participaciones y gastos
del evento. Reutilizar un catálogo existente no exige permiso para mantenerlo;
crear uno nuevo o cambiar datos de proveedor sí requiere permiso administrativo.
Si PIF crea o actualiza una persona global, también exige su permiso funcional.
Guardado e importación son transaccionales: una denegación revierte cambios
parciales. Los flujos autenticados de asistencia QR y encuestas siguen siendo
operaciones normales, sin exigir staff indiscriminadamente.

No se asignaron permisos ni se actualizaron cuentas existentes. El personal
autorizado deberá revisar sus grupos y permisos deliberadamente para dar acceso
a cada operación. La política no concede privilegios por nombres de usuario.

## seed_users retirado

El comando se conserva como un aviso compatible con scripts antiguos: termina
con `CommandError` sin crear usuarios ni cambiar permisos o contraseñas. Se
eliminaron todas sus contraseñas fijas. Para una base local nueva y autorizada:

```powershell
python manage.py createsuperuser --settings=sigecap.local_settings
```

Este comando es una operación manual que sí agrega una cuenta. No se ejecutó
durante estos cambios. El alta y cambio de contraseñas del panel propio también
aplican los validadores nativos de Django, sin recortar espacios de la contraseña.

## Pruebas reproducibles y E2E aislado

Desde `sigecap/`:

```powershell
python manage.py test apps.core.test_security apps.core.tests apps.core.test_dashboard apps.personas.tests apps.personas.tests_plantillas --settings=sigecap.test_settings --noinput
python manage.py check --settings=sigecap.test_settings
```

Las 76 pruebas de Django (27 nuevas y 49 existentes) usan SQLite en memoria.
Cubren anónimos, normales, staff sin permisos, staff delegado y superusuarios;
denegación por URL directa, aislamiento de cuentas/auditoría, Django Admin,
permisos PIF, reversión de cambios parciales, CSRF tras cambiar cuenta,
configuración sin secretos y comando retirado sin modificaciones.

Los E2E conservan los escenarios anteriores pero usan una fixture de login
real en cada prueba. Se retiraron las contraseñas literales de los tests: la
configuración genera valores aleatorios de prueba. `e2e_server.py` fija siempre
`e2e_settings`, verifica la base en memoria, crea únicamente fixtures efímeras y
escucha en `127.0.0.1:8091`. No reutiliza servidores ni sesiones existentes.
Las trazas están deshabilitadas para no registrar contraseñas introducidas.
No ejecutes el script E2E con otras configuraciones ni contra un servidor real.

Desde la raíz, con dependencias ya instaladas y `python` del entorno virtual:

```powershell
$env:SIGECAP_PYTHON = (Get-Command python).Source
npx playwright test e2e/06_security_access.spec.ts --project="Google Chrome"
```

Resultado: **4 pruebas E2E de seguridad aprobadas**. La suite heredada
`04_auth_and_roles.spec.ts` se ejecutó solo contra memoria: una prueba pasó y
tres fallaron en visibilidad de elementos con la clase `hidden`; la consola
depende del CSS Tailwind externo, cuya aplicación no estuvo disponible en esa
ejecución. No se modificó el diseño para ocultar ese fallo. Los demás escenarios
CRUD E2E no se ejecutaron en esta entrega.

`manage.py check` funciona en local y pruebas. La comprobación `--deploy`, con
configuración de producción y base efímera, solo conserva las advertencias
`security.W005` y `security.W021` sobre subdominios HSTS y preload, decisiones
que requieren conocer el dominio y su infraestructura. WhiteNoise advierte que
no existe aún el directorio local de estáticos recopilados.

## Riesgos y límites pendientes

- Los secretos y contraseñas antiguos pueden permanecer en el historial de Git.
  Si se usaron realmente, un responsable debe rotarlos y revisar las cuentas;
  no se cambiaron ni se comprobó su contenido en bases reales.
- Las fuentes y scripts de CDN siguen siendo dependencias de disponibilidad.
- La identidad docente no tiene una relación explícita con la cuenta Django:
  definir acceso por propietario en portales, QR y encuestas requiere una política
  adicional y no se inventó una asociación entre modelos.
- El proxy HTTPS y la protección de archivos media en el servidor de publicación
  requieren validación en ese entorno. No se ejecutó un despliegue.
- En Windows, la ejecución E2E necesitó detener el servidor temporal propio al
  finalizar para que terminara el runner; no quedó escuchando en el puerto 8091.

## Archivos de esta corrección

- Autorización: `sigecap/apps/core/permissions.py`, `admin.py`, `views.py`;
  `sigecap/apps/catalogos/views.py`, `sigecap/apps/personas/views.py`,
  `sigecap/apps/capacitaciones/views.py`.
- Configuración: `sigecap/sigecap/settings.py`, `environment.py`,
  `local_settings.py`, `test_settings.py`, `e2e_settings.py`;
  `sigecap/.env.example` y `sigecap/docker-compose.yml`.
- Cuentas: `sigecap/apps/capacitaciones/management/commands/seed_users.py`.
- Plantillas: `sigecap/templates/administracion/panel.html` y
  `sigecap/templates/capacitaciones/sistema_gestion.html`. El panel evita consultar
  usuarios o auditoría sin permiso; PIF utiliza capacidades reales y actualiza
  los tokens CSRF después de cambiar de cuenta. También se corrigió un alias de
  consulta del panel que colisionaba con la propiedad `total_inscritos` del modelo.
- Pruebas: `sigecap/apps/core/test_security.py`, `sigecap/e2e_server.py`,
  `e2e/fixtures.ts`, `e2e/06_security_access.spec.ts`, `playwright.config.ts` y los
  cinco `.spec.ts` anteriores, que ahora importan la fixture de autenticación.
- Documentación: `README.md`, `docs/autenticacion.md`, `docs/dashboard.md`,
  `docs/responsive-fichas.md`, `docs/07_DOCUMENTACION_COMPLETA_DEL_SISTEMA.md`
  y este documento. Los comandos locales se expresan de forma portable.

La política usa los [permisos nativos de Django](https://docs.djangoproject.com/en/6.0/topics/auth/default/)
y la configuración sigue su [guía de despliegue](https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/).
