# Corrección responsive de Fichas de Cursos

## Causa

La plantilla `capacitaciones/lista.html` hereda un encabezado con altura fija de
68 px. El título comparte una fila flex sin wrapping con un buscador de 320 px
y tres botones de texto sin salto de línea. La barra lateral ocupa otros 260 px.
Cuando no cabe todo, el título se comprime, aumenta su altura y supera la altura
del encabezado. Los filtros también tenían contenedores de anchura fija.

## Cambio

- `templates/base.html`: punto de extensión `body_class`, vacío por defecto.
- `templates/capacitaciones/lista.html`: activa `courses-page`, carga el CSS local
  y sustituye anchos inline de filtros por clases adaptables.
- `static/css/course-list.css`: todas las reglas están bajo `.courses-page`.
  Encabezado con altura automática, wrapping, espacio reservado al título,
  buscador flexible y botones que pueden pasar a otras filas. Los filtros llenan
  sus contenedores y se apilan en móvil. La alerta y las acciones de la tabla
  también permiten wrapping. Los iconos tienen espacio limitado para que la
  falta de su fuente no desplace los textos de los controles.
- Hasta 640 px, la navegación permanece abierta sobre el contenido, con enlaces
  distribuidos en dos columnas. Así no resta 260 px al contenido móvil.
- El desplazamiento horizontal necesario de la tabla queda dentro de
  `.table-responsive`, sin desbordar la página.

Dashboard, Gestión de Matrículas y Padrón no cargan esta hoja ni activan su clase.
No se cambian URLs, formularios, consultas, autenticación, permisos o modelos.

## CSS y caché

Django localiza el archivo con sus buscadores de estáticos. La hoja se carga
después del tema global y usa la URL `course-list.css?v=20261111-1`, para que
una versión anterior de la página no reutilice el mismo recurso CSS. En la
comprobación HTTP local respondió 200 y sus reglas se reflejaron en los estilos
calculados en ambos motores. No fue necesario borrar la caché global.

En una instalación que sirva estáticos recopilados, debe publicarse también
este archivo mediante el procedimiento habitual de estáticos. No se ejecutó
`collectstatic` contra la instalación existente.

## Verificación

Se generaron las páginas con el cliente de pruebas de Django, sesión autenticada
y SQLite en memoria. Los registros para probar la tabla y la alerta se crearon
exclusivamente en esa base aislada. Luego se sirvieron las páginas renderizadas
y los CSS reales en un servidor HTTP local temporal para comprobar el layout.

| Ancho | Chromium | WebKit |
| --- | --- | --- |
| 1440 px | Correcto | Correcto |
| 1366 px | Correcto | Correcto |
| 1024 px | Correcto | Correcto |
| 768 px | Correcto | Correcto |
| 390 px | Correcto | Correcto |
| 360 px | Correcto | Correcto |

Se comprobaron título, controles contenidos dentro del encabezado, ausencia de
superposición entre controles, buscador de al menos 220 px, filtros sin desbordar,
ausencia de overflow horizontal del documento, enlace activo y carga HTTP del
CSS versionado. Se generaron capturas de las doce combinaciones y se revisaron
visualmente escritorio y móvil. Los archivos de revisión y capturas quedan en
`sigecap/test-results/course-layout/`, ignorado por Git.

Se verificó además que los otros tres módulos mantienen sus estilos compartidos.

Pruebas de Django:

```powershell
cd sigecap
$pythonExe = 'python'  # Entorno virtual activado
& $pythonExe manage.py test apps.core.test_dashboard apps.core.tests apps.personas.tests apps.personas.tests_plantillas --settings=sigecap.test_settings --noinput
& $pythonExe manage.py check --settings=sigecap.test_settings
```

Resultado: **49 pruebas aprobadas**, revisión Django sin problemas y
`git diff --check` sin errores. WhiteNoise conserva el aviso previo de que no
existe el directorio de estáticos recopilados `staticfiles/`.

## Límites de la comprobación

La revisión de navegador usa páginas renderizadas en la base aislada, no la base
real ni el servidor habitual del usuario. Las peticiones a fuentes y scripts de
CDN se bloquearon para hacer la revisión local; no se comprobó su disponibilidad
externa, y los iconos de las capturas aparecen sin su fuente. El layout se probó
incluso en esa condición. No se alteraron registros reales ni se ejecutaron
migraciones contra la base existente, commits o push.
