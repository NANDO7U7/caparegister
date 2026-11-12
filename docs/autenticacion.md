# Inicio de sesión obligatorio en SIGECAP

## Implementación

Se reutilizan `django.contrib.auth`, sus usuarios, sesiones, backend, validadores
y hashing de contraseñas. `LoginView` procesa el formulario institucional en
`/login/`, valida credenciales y valida el host y esquema del destino `next`.
Sin destino válido, vuelve al Dashboard (`/`). Los errores de acceso muestran
el mismo mensaje para cuentas inexistentes, inactivas y contraseñas incorrectas.
No hay registro público de cuentas.

`LoginRequiredMiddleware`, después de `AuthenticationMiddleware`, exige sesión
en las vistas de todos los módulos, APIs, portales, exportaciones, QR y archivos
media servidos por Django en desarrollo. Los recursos estáticos siguen disponibles
para presentar el login. El login de Django Admin conduce al formulario común;
Admin conserva su control de acceso para personal autorizado. Las vistas privadas
nuevas quedan protegidas por defecto: no deben marcarse `login_not_required`.

`LogoutView` acepta POST con CSRF, invalida la sesión y vuelve siempre al login.
Está disponible también en `/admin/logout/`. El botón aparece en la plantilla
base y en la consola PIF, que tiene su propia plantilla. Las respuestas de vistas
usan `Cache-Control: no-store` para evitar conservar información privada.
Las cookies de sesión y CSRF se envían exclusivamente por HTTPS cuando DEBUG=False.

El endpoint JSON de autenticación existente se conserva para cambiar de cuenta
desde la consola PIF, con contraseña y CSRF; ahora también requiere una sesión
previa para abrirlo. Se conserva literalmente la contraseña, incluidos espacios,
y no se convierte el nombre de usuario a minúsculas.

La gestión de cuentas existente en `/administracion/usuarios/<accion>/` exige
un superusuario activo. No se modifican los permisos de los usuarios existentes
ni se rediseñan los permisos de los demás módulos.

## Origen del mensaje sobre ugb_pif

El selector de roles de la plantilla base enviaba un nombre de usuario a
`conmutar_rol_web_view`, que llamaba a `login()` sin verificar una contraseña.
Si faltaba la cuenta seleccionada, mostraba el mensaje de usuario inexistente.
`ugb_pif` identifica un gestor de la consola PIF en la lógica existente.

Se retiró el selector inseguro. Su URL antigua conduce al login sin cambiar la
identidad de la sesión. No se creó `ugb_pif` ni se le asignaron permisos.
El comando heredado `seed_users` contiene contraseñas fijas y modifica cuentas
y permisos: no se ejecutó y **no debe usarse para configurar el acceso**.

## Crear un administrador local (operación manual)

Los cambios no requieren migraciones de modelos. No se ejecutaron migraciones,
comandos de carga ni creación de usuarios contra la base real.
Para crear deliberadamente un administrador en tu base local, abre PowerShell:

```powershell
cd sigecap
$pythonExe = 'python'  # Entorno virtual activado
$env:DEBUG = 'True'
& $pythonExe manage.py createsuperuser --settings=sigecap.local_settings
```

Escribe el usuario y una contraseña única cuando Django los solicite. No hay
contraseña predeterminada. Este comando sí agrega el usuario a la base configurada;
ejecútalo únicamente sobre la base local donde quieras administrarlo.
Si ya existe un administrador, utiliza sus credenciales. Los usuarios adicionales
se administran por personal autorizado desde Django Admin o el panel existente.

## Iniciar el servidor y comprobar el flujo

Desde esa misma carpeta y consola:

```powershell
& $pythonExe manage.py runserver 127.0.0.1:8080 --settings=sigecap.local_settings
```

1. Abre una ventana privada del navegador en http://127.0.0.1:8080/.
2. Comprueba que aparece el login y que las credenciales incorrectas muestran un error genérico.
3. Abre `/personas/`, `/capacitaciones/`, `/costos/` o `/administracion/` sin sesión: deben llevar al login.
4. Inicia sesión: se abre la página solicitada o el Dashboard.
5. Pulsa **Cerrar sesión**: vuelve al login y las URLs privadas vuelven a bloquearse.
6. Un `next` externo, por ejemplo `https://example.org/`, debe terminar en el Dashboard.

Si `python` apunta al alias de Microsoft Store, utiliza la ruta explícita anterior.
En producción, los archivos media también deben servirse mediante un mecanismo
que verifique la sesión; un servidor web que publique directamente esa carpeta
no pasa por el middleware de Django. Usa HTTPS y DEBUG=False.

## Verificación automatizada

```powershell
& $pythonExe manage.py test apps.core.tests apps.personas.tests apps.personas.tests_plantillas --settings=sigecap.test_settings --noinput
& $pythonExe manage.py check --settings=sigecap.test_settings
```

Resultado: **41 pruebas aprobadas**, revisión de Django sin problemas.
Las pruebas usan exclusivamente una base SQLite en memoria, incluso si el entorno
de la aplicación está configurado para PostgreSQL. Los usuarios y contraseñas de
prueba se generan únicamente allí. Se comprobaron acceso anónimo a rutas de todos
los módulos por GET y POST, credenciales válidas e inválidas, cuenta inactiva,
destinos seguros, CSRF, cierre de sesión, reutilización de sesión invalidada,
protección de media, caché, gestión restringida de cuentas y bloqueo de suplantación.
También pasaron las pruebas existentes de personas y plantillas.

WhiteNoise advierte que falta `staticfiles/`, el directorio de estáticos recopilados;
no afecta las pruebas. El servidor de desarrollo sirve los recursos desde `static/`.
Los scripts heredados `test_*.py` de la raíz no se ejecutaron porque algunos trabajan
contra la base configurada de la aplicación. No se ejecutaron commits, push ni merges.

La configuracion actual y la politica de permisos se describen en [seguridad.md](seguridad.md). seed_users esta retirado y no modifica cuentas.
