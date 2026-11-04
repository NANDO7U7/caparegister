# Especificación Formal de Requerimientos del Sistema
## Sistema de Gestión de Capacitaciones Docentes y Administrativas

---

## 1. Introducción y Propósito

El presente documento formaliza los requerimientos funcionales y no funcionales para el **Sistema de Gestión de Capacitaciones Docentes y Administrativas (SGCDA)**, desarrollado bajo la plataforma **Python, Django y PostgreSQL**. El sistema tiene como objetivo principal sustituir el registro fragmentado en hojas de cálculo por una plataforma web centralizada, transaccional, analítica y **altamente segura**, conservando el histórico acumulado año con año y protegiendo los datos institucionales frente a vulnerabilidades informáticas.

---

## 2. Requerimientos Funcionales (RF)

### 2.1 Gestión de Catálogos y Flexibilidad (RF-01)
* **RF-01.1:** El sistema debe permitir la creación, modificación y desactivación de **Áreas de Formación** (ej. Institucional, Formación Pedagógica, Formación de Especialidad, Formación Integral) mediante el panel administrativo seguro de Django.
* **RF-01.2:** El sistema debe permitir la gestión de **Tipos y Modalidades** (Taller, Curso, Diplomado, Congreso, Conferencia; Presencial, Virtual, Híbrida).
* **RF-01.3:** El sistema debe permitir la gestión de **Facultades y Unidades Organizacionales** de la universidad.
* **RF-01.4:** El sistema debe permitir la gestión de **Proyectos / Fuentes de Financiamiento** (fondos propios, cooperación externa, convenios institucionales).
* **RF-01.5:** El sistema debe permitir la configuración y alta de nuevos catálogos sin requerir modificaciones en el código fuente.

### 2.2 Gestión de Capacitaciones (RF-02)
* **RF-02.1:** Registro de capacitaciones con los siguientes campos obligatorios:
  * Nombre de la capacitación.
  * Descripción y objetivos.
  * Área de formación (seleccionable del catálogo).
  * Tipo y modalidad.
  * Duración total en **horas académicas**.
  * Fecha de inicio y fecha de finalización.
  * Facultad(es) o unidades beneficiadas (soporte para una o múltiples facultades).
  * Proyecto o fuente de financiamiento asociada.
  * Proveedor o facilitador (interno o externo).
* **RF-02.2:** Control de Estados del Ciclo de Vida:
  * `Planificada` -> `En Curso` -> `Finalizada` -> `Cancelada`.
* **RF-02.3:** Búsqueda avanzada y filtrado por año, periodo, facultad, área y estado con sanitización estricta de parámetros de consulta.

### 2.3 Proveedores e Instructores (RF-03)
* **RF-03.1:** Registro de proveedores con: Nombre de la institución o facilitador, tipo (interno/externo), país de origen, contacto, correo, teléfono y observaciones.
* **RF-03.2:** Vista de historial acumulado de todas las capacitaciones impartidas por cada proveedor con evaluación o métricas de participación.

### 2.4 Gestión de Personas y Participantes (RF-04)
* **RF-04.1:** Ficha única por persona con:
  * Identificador institucional unívoco (Código de empleado o documento de identidad).
  * Nombre completo y apellidos.
  * Tipo de personal: `Docente` o `Administrativo`.
  * Facultad o unidad a la que pertenece.
  * Cargo o puesto actual.
  * Correo electrónico y teléfono de contacto.
* **RF-04.2:** Inscripción a capacitaciones (individual o masiva mediante plantilla).
* **RF-04.3:** Registro de estado de participación:
  * `Inscrito` -> `Asistió` -> `Aprobó` -> `No Completó`.

### 2.5 Historial Acumulativo Interanual (RF-05)
* **RF-05.1:** El sistema debe conservar todo el historial de capacitaciones de una persona a lo largo de los años sin sobrescritura de datos.
* **RF-05.2:** La ficha del participante debe mostrar:
  * Total de horas cursadas históricas y horas acumuladas por año.
  * Desglose de horas por área de formación (ej. 80 hrs pedagógicas, 120 hrs de especialidad).
  * Listado cronológico de cursos con sus fechas y estados de aprobación.

### 2.6 Presupuesto, Costos y Fuentes de Financiamiento (RF-06)
* **RF-06.1:** Registro de costos asociados a cada capacitación:
  * Costo de inscripción (por persona o grupal).
  * Transporte y pasajes.
  * Materiales y logística.
  * Viáticos y alimentación.
  * Otros conceptos libres definibles por el gestor.
* **RF-06.2:** Asociación de cada rubro de costo a un proyecto o fuente de financiamiento.
* **RF-06.3:** Reporte comparativo de **Presupuesto Planificado vs. Presupuesto Ejecutado (Gasto Real)** con control de acceso exclusivo a directivos y administradores.

### 2.7 Gestión Segura de Evidencias Digitales (RF-07)
* **RF-07.1:** Subida de archivos en formatos PDF, PNG y JPG asociados a:
  * La capacitación general (listas de asistencia firmadas, programa de curso, informe final).
  * El participante individual (diploma, constancia de aprobación).
* **RF-07.2:** Renombrado automático a UUIDv4 y validación binaria de tipo MIME (Magic Bytes) para impedir subida de código malicioso.
* **RF-07.3:** Descarga protegida: El sistema debe verificar que el usuario autenticado tiene autorización antes de permitir descargar cualquier evidencia.

### 2.8 Importación Masiva Segura desde Excel (RF-08)
* **RF-08.1:** Módulo de carga masiva mediante archivo `.xlsx` o `.csv` estandarizado procesado con Python (`pandas`).
* **RF-08.2:** Validador y sanitizador previo a la inserción:
  * Desinfección contra inyección de fórmulas CSV (`=`, `+`, `-`, `@`).
  * Identificación de filas con errores (código de empleado inexistente, fechas inválidas).
  * Pre-visualización de registros válidos para confirmación del usuario antes de guardar.
* **RF-08.3:** Generación de reporte de incidencias descargable para corrección rápida.

### 2.9 Dashboards y Reportes Analíticos (RF-09)
* **RF-09.1:** Tablero de mando interactivo con indicadores clave (KPIs):
  * **Inversión Total:** Filtros por año, facultad, área de formación y proveedor.
  * **Cobertura Docente:** Porcentaje de personal capacitado frente al total de la plantilla por facultad.
  * **Horas Promedio:** Horas de formación por docente y por unidad.
  * **Top de Capacitaciones:** Eventos con mayor demanda y tasa de finalización.
* **RF-09.2:** Comparativa interanual (crecimiento o variación porcentual respecto al año anterior).

### 2.10 Exportaciones Formales (RF-10)
* **RF-10.1:** Exportación de tablas filtradas a formato Excel (`.xlsx`) con sanitización de celdas.
* **RF-10.2:** Generación de reportes ejecutivos en PDF con membrete institucional universitario.

---

## 3. Requerimientos No Funcionales de Seguridad y Rendimiento (RNF)

* **RNF-01 (Principio Acumulativo e Integridad Histórica):** Los datos históricos nunca deben sobrescribirse ni eliminarse físicamente en los cierres anuales. El sistema opera mediante consultas temporales por año fiscal preservando la integridad histórica en PostgreSQL.
* **RNF-02 (Control de Acceso Basado en Roles - RBAC):** Autenticación de sesiones y control de permisos nativo de Django. Separación estricta de privilegios para Administradores, Gestores, Directivos y Docentes.
* **RNF-03 (Auditoría Inmutable - Append-Only):** Registro automático de bitácora para todas las acciones de modificación (`auditoria_log`). La base de datos prohíbe mediante triggers cualquier actualización o eliminación de registros de auditoría.
* **RNF-04 (Usabilidad y Adopción):** Interfaz limpia, intuitiva y rápida, optimizada para usuarios habituados a tablas de Excel, con tiempos de respuesta menores a 1 segundo.
* **RNF-05 (Seguridad en la Carga de Archivos):**
  * Validación de tipo MIME real leyendo los *Magic Bytes* del archivo (`python-magic`), rechazando archivos donde la extensión no coincida con el contenido.
  * Límite de tamaño estricto de 10 MB por archivo de evidencia.
  * Almacenamiento con nombres UUIDv4 aleatorios en directorios sin permisos de ejecución (`noexec`).
* **RNF-06 (Protección contra Inyección CSV / Fórmulas):** Toda exportación e importación tabular debe neutralizar celdas que inicien con caracteres de fórmulas ejecutables (`=`, `+`, `-`, `@`, `|`, `%`), anteponiendo una comilla simple `'`.
* **RNF-07 (Protección contra Fuerza Bruta y Control de Sesiones):** Bloqueo automático de IP y cuenta tras 5 intentos fallidos consecutivos de inicio de sesión (`django-axes`). Cookies con banderas obligatorias `Secure`, `HttpOnly` y `SameSite=Lax`.
* **RNF-08 (Prevención de IDOR / BOLA):** Validación estricta a nivel de objeto en todas las vistas de Django. Un usuario solo puede acceder a registros que correspondan a su propia facultad o a su propio perfil.
* **RNF-09 (Protección de Datos Personales):** Enmascaramiento de documentos de identidad sensibles en interfaces públicas y prohibición de registrar contraseñas o datos bancarios en los logs del sistema.
* **RNF-10 (Portabilidad y Aislamiento en Docker):** La base de datos PostgreSQL debe correr en una red interna privada de Docker sin exponer puertos públicos al exterior. El contenedor web de Django debe ejecutarse bajo un usuario sin privilegios root (`UID 1000`).
* **RNF-11 (Respaldos Cifrados):** Tareas programadas automáticas de copias de seguridad de PostgreSQL (`pg_dump`) almacenadas en volúmenes dedicados.

---

## 4. Matriz de Trazabilidad de Roles y Permisos

| Módulo / Acción | Administrador | Gestor de Área | Directivo / Consulta | Docente / Participante |
|---|:---:|:---:|:---:|:---:|
| Gestionar Catálogos en Django Admin | ✅ | ❌ | ❌ | ❌ |
| Crear / Editar Capacitaciones | ✅ | ✅ (Solo su área) | ❌ | ❌ |
| Registrar Participantes | ✅ | ✅ (Su facultad) | ❌ | ❌ |
| Registrar Costos y Presupuestos | ✅ | ✅ (Su área) | ❌ | ❌ |
| Subir Diplomas / Evidencias | ✅ | ✅ | ❌ | ✅ (Solo sus propios diplomas) |
| Descargar Diplomas de Otros | ✅ | ✅ (Su facultad) | ❌ | ❌ (Bloqueado) |
| Importación Masiva Excel | ✅ | ❌ | ❌ | ❌ |
| Ver Dashboards y KPIs Globales | ✅ | ✅ (Su área) | ✅ (Global o Fac.) | ❌ |
| Consultar Historial Personal | ✅ | ✅ | ✅ | ✅ (Solo su ficha) |
| Exportar Reportes Oficiales | ✅ | ✅ | ✅ | ❌ |
| Ver Bitácora de Auditoría | ✅ | ❌ | ❌ | ❌ |
