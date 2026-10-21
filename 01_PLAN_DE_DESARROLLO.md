# Plan de Desarrollo del Proyecto
## SIGECAP — Sistema de Gestión de Capacitaciones Docentes y Administrativas

---

## 1. Información General del Proyecto
* **Nombre del Producto:** SIGECAP (Sistema de Gestión de Capacitaciones).
* **Cliente / Entorno:** Institución Universitaria (Dirección de Talento Humano / Unidad de Capacitación).
* **Stack Tecnológico:** **Python 3.11+, Django 5.x y PostgreSQL 15+**.
* **Diseño Visual:** Basado en **9 prototipos de Google Stitch** con sistema de diseño **Material Design 3 (Material You)**, tipografía **Inter** y paleta institucional azul (`primary: #00236f`, `secondary: #0051d5`). Referencia completa en `06_GUIA_DISENO_VISUAL_STITCH.md`.
* **Enfoque de Seguridad:** Arquitectura alineada con las directrices de seguridad de **OWASP Top 10** y protección de datos institucionales.
* **Objetivo:** Centralizar el registro, control presupuestal, evidencias y análisis de las capacitaciones del personal universitario, reemplazando el uso de múltiples hojas de Excel y preservando el histórico acumulado año tras año de forma segura.
* **Duración estimada:** 10 semanas (5 fases de 2 semanas cada una).
* **Modalidad:** Desarrollo iterativo e incremental con entregas quincenales funcionales.

### Pantallas Diseñadas (Prototipos de Referencia)
El frontend se construirá siguiendo fielmente los 9 prototipos de alta fidelidad generados en Google Stitch:

| # | Vista Prototipada | Fase de Implementación |
|---|---|---|
| 1 | Dashboard Principal (5 KPIs, gráficas de tendencia) | Fase 5 |
| 2 | Listado de Capacitaciones (tabla maestra con filtros) | Fase 2 |
| 3 | Detalle de Capacitación (ficha completa) | Fase 2 |
| 4 | Formulario de Nueva Capacitación | Fase 2 |
| 5 | Ficha de Participante (historial acumulativo) | Fase 3 |
| 6 | Costos y Presupuesto (planificado vs. ejecutado) | Fase 3 |
| 7 | Portal Docente (vista personal) | Fase 3 |
| 8 | Administración de Catálogos | Fase 2 |
| 9 | Reportes y Analíticas | Fase 5 |

---

## 2. Metodología de Trabajo
Se adoptará un marco ágil basado en **Sprints de 2 semanas**:
* **Planificación del Sprint:** Definición de objetivos e historias de usuario al inicio de cada fase.
* **Demostraciones Quincenales:** Presentación del avance funcional a los coordinadores de capacitación.
* **Seguridad desde el Diseño (Security by Design):** Cada avance incluye modelos de Django tipados, pruebas unitarias, análisis estático de vulnerabilidades (`bandit`) y scripts de migración.

---

## 3. Cronograma Detallado por Fases

```
[Semana 1-2] Fase 1: Fundamentos, Modelo de Datos Relacional y Plantilla de Carga
     │
[Semana 3-4] Fase 2: Configuración de Django, Autenticación, Catálogos y Capacitaciones
     │
[Semana 5-6] Fase 3: Participantes, Historial Acumulativo y Control Financiero
     │
[Semana 7-8] Fase 4: Repositorio de Evidencias Digitales e Importador Masivo de Excel
     │
[Semana 9-10] Fase 5: Dashboards Analíticos, Auditoría de Seguridad, Docker y Entrega
```

### Fase 1: Fundamentos, Modelo de Datos Relacional y Plantilla de Carga (Semanas 1 y 2)
* **Objetivo:** Establecer la base de datos relacional en PostgreSQL y definir el estándar para sanear y migrar los Excels históricos.
* **Actividades:**
  1. Levantamiento técnico y revisión de la estructura de las hojas de Excel actuales de la universidad.
  2. Diseño formal del Diagrama Entidad-Relación (ERD) en PostgreSQL.
  3. Creación del script DDL (`04_MODELO_DE_DATOS_POSTGRESQL.sql`) con llaves primarias, foráneas, restricciones, índices y **triggers de inmutabilidad en la bitácora de auditoría**.
  4. Diseño de la plantilla estandarizada de migración Excel con validaciones de datos y reglas contra inyección de fórmulas CSV.
  5. Configuración del entorno de desarrollo base (repositorio Git, Docker con PostgreSQL y entorno virtual de Python).
* **Entregables de la fase:**
  * Diagrama ERD y diccionario de datos.
  * Script SQL de creación de base de datos con triggers de seguridad y catálogos base.
  * Plantilla Excel de importación con instructivo de llenado.

---

### Fase 2: Configuración de Django, Autenticación, Catálogos y Capacitaciones (Semanas 3 y 4)
* **Objetivo:** Desarrollar el núcleo administrativo de la plataforma, el panel de control y el catálogo de eventos.
* **Actividades:**
  1. Configuración del proyecto Django con PostgreSQL y estructura modular de aplicaciones (`apps.core`, `apps.capacitaciones`, `apps.personas`, `apps.costos`).
  2. Implementación de autenticación segura con protección contra fuerza bruta (`django-axes`) y control de acceso basado en grupos y permisos nativos de Django (RBAC):
     * *Administrador del sistema*
     * *Gestor de capacitación*
     * *Directivo / Consulta*
     * *Docente / Personal administrativo*
  3. Configuración y personalización de **Django Admin** para la gestión ágil e inmediata de Catálogos Dinámicos (Áreas de formación, Tipos/Modalidades, Facultades, Proveedores, Proyectos).
  4. Módulo de Gestión de Capacitaciones: alta, edición, estados (planificada, en curso, finalizada, cancelada), asignación de facultades beneficiadas y horas totales con control de acceso por facultad.
* **Entregables de la fase:**
  * Módulo funcional de inicio de sesión y gestión de usuarios blindado contra fuerza bruta.
  * Panel de Django Admin configurado para administración de catálogos.
  * Interfaz web para registro y consulta de capacitaciones.

---

### Fase 3: Participantes, Historial Acumulado y Costos (Semanas 5 y 6)
* **Objetivo:** Conectar al personal docente/administrativo con las capacitaciones y registrar el control financiero.
* **Actividades:**
  1. Ficha digital de personas (identificación única institucional, cargo, facultad/unidad, tipo de personal) con protección contra referencias directas inseguras (IDOR).
  2. Asignación masiva o individual de participantes a capacitaciones con control de estado (inscrito, asistió, aprobó, no completó).
  3. Vista de **Historial Acumulativo Personal**: consulta de todas las capacitaciones cursadas por una persona a lo largo de los años sin pérdida de datos.
  4. Módulo de Costos y Presupuestos:
     * Registro de costos de inscripción, transporte, materiales y viáticos.
     * Asociación a fuentes de financiamiento o proyectos.
     * Vista de comparativa: **Presupuestado vs. Ejecutado** con acceso restringido a directores.
* **Entregables de la fase:**
  * Gestión de participantes y registro de asistencias/aprobaciones.
  * Módulo financiero y presupuestal por capacitación.

---

### Fase 4: Repositorio Seguro de Evidencias e Importador de Excel (Semanas 7 y 8)
* **Objetivo:** Organizar los archivos digitales de respaldo y automatizar la ingesta masiva de registros históricos.
* **Actividades:**
  1. Módulo de Carga de Evidencias Digitales:
     * Validación de tipo MIME real por *Magic Bytes* (`python-magic`).
     * Renombrado obligatorio a UUIDv4 aleatorio en disco.
     * Descargas protegidas mediante verificación de propiedad de documentos.
  2. Desarrollo del **Motor Seguro de Importación Masiva de Excel**:
     * Procesamiento con Python (`pandas`, `openpyxl` y analizador seguro `defusedxml`).
     * Filtro automático contra inyección de fórmulas CSV (`=`, `+`, `-`, `@`).
     * Validador en tiempo real: detecta filas con errores o datos faltantes antes de insertar en PostgreSQL.
     * Reporte visual de pre-visualización de registros válidos y errores detectados.
  3. Normalización y deduplicación automática de personas y cursos existentes.
* **Entregables de la fase:**
  * Repositorio digital de evidencias blindado contra subida de archivos maliciosos.
  * Importador de Excel en la interfaz web con visor de pre-validación y logs de error.

---

### Fase 5: Dashboards, Auditoría de Seguridad, Docker y Entrega (Semanas 9 y 10)
* **Objetivo:** Construir los paneles de toma de decisiones, ejecutar auditorías de seguridad y entregar el paquete final.
* **Actividades:**
  1. Dashboard Directivo interactivo con KPIs (inversión por facultad, cobertura docente y horas acumuladas).
  2. Exportación de reportes consolidados a Excel y PDF con sanitización de celdas y membrete institucional.
  3. **Auditoría y Pruebas de Seguridad:**
     * Ejecución de `python manage.py check --deploy` para verificar banderas de producción (HSTS, SSL, cookies).
     * Análisis estático de vulnerabilidades con `bandit` y verificación de dependencias con `pip-audit`.
     * Pruebas de penetración internas: verificación de aislamiento IDOR entre facultades y prueba de subida de archivos no permitidos.
  4. Empaquetado final con `docker-compose.yml` (PostgreSQL en red aislada privada + Django sin privilegios root + Nginx con cabeceras de seguridad).
  5. Manuales finales (Manual de Usuario y Manual Técnico de Despliegue y Seguridad).
* **Entregables de la fase:**
  * Sistema web 100% operativo, probado y blindado para producción en la universidad.
  * Código fuente documentado en repositorio Git.
  * Paquete de despliegue Docker y reporte de verificación de seguridad.

---

## 4. Matriz de Riesgos y Mitigación

| Riesgo Identificado | Impacto | Probabilidad | Estrategia de Mitigación |
|---|---|---|---|
| **Subida de archivos maliciosos en diplomas** | Crítico | Media | Renombrado obligatorio con UUIDv4, validación de tipo MIME por Magic Bytes y carpeta `/media/` sin permisos de ejecución. |
| **Inyección de fórmulas al exportar a Excel** | Alto | Media | Sanitización automática anteponiendo comilla simple a celdas que inicien con caracteres de fórmula. |
| **Ataques de fuerza bruta en cuentas de usuario** | Alto | Alta | Integración de `django-axes` para bloquear cuentas e IPs tras 5 intentos fallidos consecutivos. |
| **Acceso no autorizado a datos de otros docentes (IDOR)** | Alto | Media | Autorización estricta a nivel de objeto en cada consulta del ORM de Django. |
| **Excels históricos con formatos inconsistentes** | Medio | Alta | Etapa de pre-validación con advertencias visuales antes de la inserción y deduplicación en Django. |

---

## 5. Entregables de Continuidad para el Cliente
1. **Código Fuente en Python y Django:** Estructurado bajo buenas prácticas, tipado y documentado en español.
2. **Infraestructura Contenedorizada (`docker-compose.yml`):** Red interna aislada para PostgreSQL y contenedor Django con usuario no-root.
3. **Diccionario de Datos y DDL SQL:** Documentación completa de tablas, campos, relaciones y triggers de seguridad.
4. **Manual de Usuario:** Guía ilustrada paso a paso para administradores y coordinadores.
5. **Manual Técnico de Seguridad y Mantenimiento:** Instrucciones para ejecutar copias de seguridad automáticas de PostgreSQL (`pg_dump`), renovación de certificados TLS y comandos de gestión de Django.
