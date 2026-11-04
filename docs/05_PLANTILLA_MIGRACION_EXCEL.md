# Guía y Diccionario de la Plantilla de Migración Excel
## Sistema de Gestión de Capacitaciones Docentes y Administrativas

---

## 1. Objetivo de la Plantilla

Esta plantilla tiene como finalidad **estandarizar la información histórica** dispersa en las diferentes hojas de Excel de la universidad para permitir su carga masiva automatizada hacia la base de datos PostgreSQL del sistema Django, garantizando la consistencia, limpieza, integridad y **seguridad estricta contra inyecciones de código o fórmulas maliciosas**.

---

## 2. Estructura de Columnas y Validaciones

Cada fila del archivo Excel representa una **participación de un empleado en una capacitación específica**:

| Columna en Excel | Tipo de Dato | Obligatorio | Valores Permitidos / Formato | Ejemplo |
|---|---|:---:|---|---|
| `Anio_Periodo` | Número (4 dígitos) | Sí | Entre 2010 y 2030 | `2024` |
| `Nombre_Capacitacion` | Texto (hasta 250) | Sí | Nombre oficial del curso/taller | `Diseño Curricular Basado en Competencias` |
| `Area_Formacion` | Texto (Catálogo) | Sí | `Área Institucional`, `Formación Pedagógica`, `Formación de Especialidad`, `Formación Integral` | `Formación Pedagógica` |
| `Tipo` | Texto (Catálogo) | Sí | `Taller`, `Curso`, `Diplomado`, `Congreso`, `Conferencia` | `Curso` |
| `Modalidad` | Texto (Catálogo) | Sí | `Presencial`, `Virtual`, `Híbrida` | `Virtual` |
| `Horas_Duracion` | Número entero | Sí | Entero mayor a 0 | `40` |
| `Fecha_Inicio` | Fecha | Sí | `AAAA-MM-DD` (ej. 2024-03-15) | `2024-03-15` |
| `Fecha_Fin` | Fecha | Sí | `AAAA-MM-DD` (igual o posterior a inicio) | `2024-03-29` |
| `Estado_Capacitacion` | Texto (Catálogo) | Sí | `Planificada`, `En Curso`, `Finalizada`, `Cancelada` | `Finalizada` |
| `Proveedor` | Texto | No | Nombre de la institución o facilitador | `Unidad de Formación Docente` |
| `Codigo_Empleado` | Texto (hasta 50) | Sí | Identificador único del docente/administrativo | `DOC-0042` |
| `Nombres_Participante`| Texto (hasta 100) | Sí | Nombres de pila | `María José` |
| `Apellidos_Participante`| Texto (hasta 100)| Sí | Apellidos | `Hernández Rivera` |
| `Tipo_Personal` | Texto (Catálogo) | Sí | `Docente` o `Administrativo` | `Docente` |
| `Facultad` | Texto (Catálogo) | Sí | Nombre o código de la facultad | `Facultad de Ingeniería y Arquitectura` |
| `Cargo_Puesto` | Texto | No | Cargo actual del empleado | `Catedrático Titular I` |
| `Email_Participante` | Correo | No | Correo institucional | `maria.hernandez@universidad.edu` |
| `Estado_Participacion`| Texto (Catálogo) | Sí | `Inscrito`, `Asistió`, `Aprobó`, `No Completó` | `Aprobó` |
| `Costo_Inscripcion` | Decimal | No | Mayor o igual a 0.00 | `150.00` |
| `Otros_Costos` | Decimal | No | Viáticos, transporte, etc. | `25.00` |
| `Fuente_Financiamiento`| Texto | No | `Fondos Propios`, `Cooperación Externa`, etc. | `Fondos Propios` |

---

## 3. Normas de Seguridad y Prevención de Vulnerabilidades en la Carga

Para evitar vulnerabilidades comunes en el procesamiento de archivos tabulares:

### 3.1 Prevención de Inyección de Fórmulas CSV (Formula / CSV Injection)
* **Vulnerabilidad:** Celdas maliciosas que inician con caracteres como `=`, `+`, `-`, `@`, `|`, o `%` pueden ejecutar comandos o macros arbitrarias al ser abiertas en hojas de cálculo por autoridades universitarias.
* **Regla de Validación:**
  * Si el valor de cualquier columna de texto inicia con `=`, `+`, `-`, `@`, `|`, `%`, el validador de Python antepondrá de forma automática una comilla simple (`'`) para neutralizar la ejecución y almacenar el valor estrictamente como texto plano.

### 3.2 Tipos de Archivos Permitidos y Control de Tamaño
* **Formatos Admitidos:** Únicamente `.xlsx` (OpenXML estándar) y `.csv` (UTF-8).
* **Formatos Prohibidos:** Se rechazan terminantemente archivos con macros habilitadas (`.xlsm`, `.xltm`, `.xlsb`), ejecutables o scripts.
* **Tamaño Máximo:** El archivo de importación no debe superar los **15 MB**.
* **Límite de Filas por Lote:** Máximo **5,000 filas por archivo**. Si el histórico universitario supera este volumen, debe dividirse por año o periodo para mitigar riesgos de denegación de servicio (DoS) por memoria.

### 3.3 Prevención de Ataques XML (XXE en archivos XLSX)
* El procesamiento interno en Python utiliza librerías con analizadores protegidos (`defusedxml`) que bloquean la resolución de entidades externas en los archivos comprimidos de Microsoft Excel.

---

## 4. Reglas de Negocio para la Ingesta de Datos

1. **Deduplicación Automática de Personas:** Si el `Codigo_Empleado` ya existe en la base de datos, el sistema no duplica la persona; asocia la nueva capacitación a su historial existente.
2. **Deduplicación de Capacitaciones:** Si coinciden `Nombre_Capacitacion`, `Fecha_Inicio` y `Horas_Duracion`, el módulo agrupa a todos los participantes dentro del mismo evento formativo.
3. **Manejo Seguro de Errores:** Si una fila contiene un error crítico (por ejemplo, `Fecha_Fin` anterior a `Fecha_Inicio` o campo obligatorio vacío), el sistema marcará esa fila en pantalla con la razón exacta del error antes de confirmar cualquier inserción a la base de datos.
