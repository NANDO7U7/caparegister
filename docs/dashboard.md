# Indicadores reales del Dashboard

El Dashboard consulta los modelos en cada petición. No almacena estadísticas
precargadas ni usa números aleatorios. Se conserva el diseño de tarjetas, tabla
y gráficas; las gráficas se apilan en pantallas pequeñas.

## Fuentes, fórmulas y alcance

Salvo la tendencia mensual, los indicadores son históricos, sin filtro de año.
Se conservan los criterios históricos existentes para los indicadores que ya
consultaban la base. No se eliminan ni corrigen automáticamente registros que
puedan contener estados contradictorios.

| Indicador | Fuente y criterio |
| --- | --- |
| Capacitaciones | `Capacitacion.objects.count()`: todos los eventos registrados, incluidos planificados y cancelados. No equivale a eventos impartidos. |
| Docentes formados | Personas distintas con `tipo_personal` Docente o Ambos y al menos una participación en estado Aprobó. Una persona cuenta una sola vez, aunque apruebe varios cursos. No se excluyen personas actualmente inactivas del histórico. |
| Inscripciones | Cantidad de filas de `Participacion`, en todos sus estados. La relación persona/capacitación tiene restricción de unicidad; la misma persona inscrita en dos cursos representa dos inscripciones. |
| Inscripciones aprobadas | Filas de `Participacion` cuyo estado es Aprobó. No se deduce aprobación de una calificación, certificado ni asistencia. |
| Horas impartidas | Suma de `Capacitacion.horas_duracion` de eventos En Curso o Finalizada, una vez por evento. No se multiplica por participantes. Se mantiene el criterio previo y se aclara en la tarjeta que es duración registrada. |
| Gasto ejecutado | Suma decimal de `GastoCapacitacion.monto_ejecutado` exclusivamente para gastos en estado Ejecutado. No se mezclan montos planificados, comprometidos o cancelados. Se muestran dos decimales. |
| Satisfacción | Promedio de los cuatro criterios de cada encuesta, con igual peso para cada respuesta: `Σ(claridad + dominio + utilidad + materiales) / (4 × N)`. Incluye todas las encuestas almacenadas, incluso anónimas. Se muestra un decimal. |
| Porcentaje de satisfacción | `promedio sin redondear / 5 × 100`, presentado con un decimal. Es porcentaje del puntaje máximo, no proporción de respuestas satisfechas; se retiró la etiqueta CSAT para evitar esa confusión. |
| Tendencia: formaciones | Eventos En Curso o Finalizada con fecha de inicio en el año calendario actual, agrupados por mes de `fecha_inicio`. |
| Tendencia: participación | Participaciones en estado Asistió o Aprobó de esos eventos, agrupadas por mes de inicio del evento. Cada participación cuenta una vez, no cada encuesta, gasto ni persona única del año. |
| Distribución por áreas | Cantidad de eventos registrados por área, en todos los estados, igual que el total de capacitaciones. Se omiten áreas sin eventos; no se excluyen áreas inactivas que tengan registros históricos. |
| Recientes y en curso | Hasta seis eventos: primero En Curso; dentro de cada grupo, fecha de inicio descendente, fecha de creación descendente y clave primaria para resolver empates. Incluye todos los estados. Proveedor ausente se muestra como Sin proveedor registrado. |

Las consultas de participaciones, gastos y encuestas se agregan por separado:
no hay uniones múltiples que multipliquen sus filas. No se usa `SUM(DISTINCT ...)`,
que eliminaría erróneamente gastos diferentes con el mismo monto.

## Estados vacíos y seguridad

- Conteos y sumas sin registros: cero.
- Sin encuestas: satisfacción y porcentaje sin valor (`None`), con el texto
  **Sin datos disponibles**; no se muestran 4.8/5, 96% ni un porcentaje sin muestra.
- Tendencia: doce meses, con cero únicamente cuando no hay observaciones en ese
  mes. Si todo el año carece de datos elegibles, aparece un estado vacío sin canvas.
- Áreas: series vacías cuando no hay eventos, aunque existan catálogos.
- Datos para JavaScript serializados mediante `json_script`, sin interpolaciones
  con `safe`; nombres con comillas o etiquetas no pueden romper el script.
- Se mantienen el middleware de autenticación, CSRF y permisos existentes.

## Moneda: hallazgo y propuesta

No hay configuración central ni campo de moneda por gasto. `L.` estaba escrito
directamente en `templates/dashboard.html`; también aparece en el módulo de
costos y en `GastoCapacitacion.__str__`. Los presupuestos y proyectos mencionan
`L/USD` en etiquetas de modelos. Esto no permite confirmar la unidad real de los
montos almacenados.

Se conserva `L.` en este cambio. Si la institución lleva sus cuentas en dólares,
la propuesta es centralizar **USD** como moneda de presentación, después de que
el responsable financiero confirme la unidad de los datos históricos y la
uniformidad entre módulos. Cambiar un símbolo no convierte importes. Si existen
varias monedas, se necesitarían moneda por registro y reglas de conversión;
no se han añadido campos ni migraciones por asumir esa necesidad.

## Información que todavía no existe

- No hay sesiones de clase ni horas efectivamente impartidas por fecha. El
  indicador de horas usa la duración completa registrada, incluso En Curso;
  no puede medir avance parcial real.
- No existe fecha individual de asistencia o aprobación: la tendencia se
  atribuye al inicio del evento, no a la fecha real de asistencia ni inscripción.
  La fecha de inscripción disponible es la fecha de creación del registro y
  puede no representar el mes histórico de participación tras una importación.
- `MatriculaMatrizDocente` registra competencias aparte, sin relación con
  `Capacitacion` ni duración; no se suma a las inscripciones o docentes formados
  para evitar inventar equivalencias y duplicar logros.
- Las encuestas no tienen una restricción de una respuesta por persona/evento.
  Se cuentan respuestas guardadas; no se presume que sean personas únicas.
- El gasto no tiene fecha efectiva de pago ni moneda: no se presenta gasto
  mensual, conversión ni consolidación de varias divisas.

## Archivos y pruebas

Archivos de esta entrega:

- `sigecap/apps/core/views.py`
- `sigecap/templates/dashboard.html`
- `sigecap/static/js/dashboard.js` (nuevo)
- `sigecap/apps/core/test_dashboard.py` (nuevo)
- `docs/dashboard.md` (este documento)

Ejecutar desde `sigecap/`:

```powershell
$pythonExe = 'python'  # Entorno virtual activado
& $pythonExe manage.py test apps.core.test_dashboard apps.core.tests apps.personas.tests apps.personas.tests_plantillas --settings=sigecap.test_settings --noinput
& $pythonExe manage.py check --settings=sigecap.test_settings
```

Las pruebas usan SQLite exclusivamente en memoria. Cubren base vacía, catálogos
sin eventos, registros reales de prueba, recarga tras altas y cambios de estado,
ausencia de multiplicación de conteos y sumas, docentes únicos, gastos iguales,
promedios ponderados por respuesta, cuatro criterios, límites de año y estados,
series JSON reales, escape seguro, orden de recientes y autenticación obligatoria.
Los datos de prueba se crean únicamente en esa base aislada.

Resultado de la ejecución: **49 pruebas aprobadas** (8 específicas del Dashboard
y 41 de autenticación, personas y plantillas). `manage.py check` sin problemas;
`git diff --check` sin errores. WhiteNoise emite el aviso de directorio
`staticfiles/` todavía no recopilado, sin afectar los resultados.

No se ejecutan los scripts históricos de pruebas de la raíz: algunos acceden a
la base configurada de la aplicación. No se requieren migraciones ni cambios
en registros reales. La comprobación visual en navegador no forma parte de las
pruebas automatizadas ejecutadas.
