# Instalar SIGECAP en Windows

## Primera instalación

1. Instala Python de 64 bits, versión 3.12 o posterior, con el lanzador `py` o
   con `python` disponible en PATH. La instalación de dependencias requiere
   conexión a Internet o un repositorio de paquetes configurado por soporte.
2. Guarda la carpeta completa de SIGECAP en una ubicación de tu usuario de
   Windows con permisos de escritura. Si estás trasladando una instalación,
   pide a soporte una copia del archivo SQLite, de `sigecap/.env` y de
   `sigecap/media`.
3. Abre la carpeta y haz doble clic en **instalar.bat**. El instalador prepara
   `.venv`, instala las dependencias y crea `sigecap/.env` si hace falta.
4. Si el instalador indica que va a crear una base nueva, revisa la ruta que
   muestra y escribe `s` para autorizar las migraciones iniciales. La ruta
   predeterminada es `sigecap/db.sqlite3`. Si esperabas reutilizar una base,
   cancela y pide a soporte que revise la ruta antes de continuar.
5. Si aparece el asistente de administrador, escribe `s`, ingresa el usuario y
   escribe la contraseña dos veces. La consola oculta los caracteres mientras
   escribes. Django valida la contraseña y guarda su hash. Guarda el usuario y
   la contraseña en un gestor de contraseñas.

Si ya existe un superusuario activo, el instalador conserva esa cuenta y omite
el asistente. Si cancelas el asistente o la contraseña no pasa la validación,
puedes retomarlo con **iniciar.bat** o **instalar.bat**. Una vez creada la cuenta
inicial, la base registra el alta y el asistente queda cerrado incluso si más
adelante se desactiva la cuenta. Si pierdes el acceso, contacta a soporte para
recuperar la cuenta.

## Iniciar y detener el sistema

- Haz doble clic en **iniciar.bat**. Deja abierta la ventana de la consola
  mientras usas SIGECAP. El navegador abrirá `http://127.0.0.1:8080/` y
  SIGECAP pedirá iniciar sesión.
- Si el navegador no se abre automáticamente, escribe esa dirección en la
  barra de direcciones del navegador de la misma computadora.
- Para apagar SIGECAP, vuelve a la consola y presiona **Ctrl+Break** o cierra
  esa ventana. Cerrar el navegador deja el sistema en ejecución.

## Si aparece un error

| Mensaje | Qué hacer |
| --- | --- |
| Falta Python o faltan dependencias | Instala Python o vuelve a ejecutar **instalar.bat** con conexión al repositorio de paquetes. |
| Falta la configuración o la base | Ejecuta **instalar.bat** para una instalación nueva. Si ya usabas SIGECAP, pide a soporte que localice la configuración y la base originales. |
| Migraciones pendientes en una base existente | Pide a soporte que respalde la base y revise la actualización. El instalador se detiene antes de aplicar migraciones a ese archivo. |
| La primera migración se interrumpió | Conserva el archivo generado y pide a soporte que determine si puede completar las migraciones. Una nueva ejecución tratará ese archivo como una base existente. |
| El puerto ya está en uso | Busca otra ventana de SIGECAP abierta. Si el puerto 8080 lo usa otro programa, contacta a soporte. |

Los dos archivos `.bat` operan con SQLite en un archivo local. El servidor de
desarrollo escucha solo en `127.0.0.1`. Mantén restringido el acceso de Windows
a la carpeta de SIGECAP y a sus respaldos. El asistente requiere una consola
interactiva y se ejecuta antes de iniciar el servidor. Las instalaciones con
PostgreSQL y el acceso desde otros equipos requieren un despliegue administrado.
Si soporte usa un archivo SQLite en otra ruta, debe configurar `DB_NAME` en
`sigecap/.env` antes de ejecutar los archivos `.bat`.
