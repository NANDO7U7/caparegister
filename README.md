# SIGECAP — Sistema de Gestión de Capacitaciones
## Docentes y Administrativas

Bienvenido a la documentación y archivos base de planificación del proyecto **SIGECAP**. Este paquete contiene las definiciones técnicas, arquitectura, modelo de datos relacional, **sistema de diseño visual (Design System)** y plan de trabajo para el desarrollo del sistema web centralizado de capacitaciones universitarias, desarrollado con **Python, Django y PostgreSQL**, con un enfoque riguroso de mitigación de vulnerabilidades, seguridad institucional y **diseño de interfaz basado en prototipos de Google Stitch (Material Design 3)**.

---

## 📑 Índice de Archivos del Proyecto

| Archivo | Descripción |
|---|---|
| 📘 [`01_PLAN_DE_DESARROLLO.md`](./01_PLAN_DE_DESARROLLO.md) | Cronograma detallado de 10 semanas (5 fases), metodología de trabajo, pruebas de seguridad estática (`bandit`), hitos, riesgos y entregables de continuidad. |
| 🏗️ [`02_ARQUITECTURA_Y_STACK.md`](./02_ARQUITECTURA_Y_STACK.md) | Justificación técnica del stack (**Python + Django + PostgreSQL**), arquitectura MTV, **matriz de mitigación de vulnerabilidades OWASP Top 10**, seguridad de carga de archivos, sesiones y Docker seguro. |
| 📋 [`03_ESPECIFICACION_REQUERIMIENTOS.md`](./03_ESPECIFICACION_REQUERIMIENTOS.md) | Requerimientos funcionales y requerimientos no funcionales de seguridad (Magic Bytes, anti-inyección CSV, inmutabilidad de auditoría, control IDOR y RBAC). |
| 🗄️ [`04_MODELO_DE_DATOS_POSTGRESQL.sql`](./04_MODELO_DE_DATOS_POSTGRESQL.sql) | Script SQL DDL listo para ejecución en PostgreSQL con tablas relacionales, llaves foráneas, **trigger de inmutabilidad estricta (Append-Only) en auditoría**, campos de seguridad anti-fuerza bruta e índices de rendimiento. |
| 📊 [`05_PLANTILLA_MIGRACION_EXCEL.md`](./05_PLANTILLA_MIGRACION_EXCEL.md) | Guía técnica y diccionario de datos para la migración de archivos históricos de Excel con **normas de desinfección contra inyección de fórmulas CSV**. |
| 📄 [`plantilla_migracion_ejemplo.csv`](./plantilla_migracion_ejemplo.csv) | Archivo de datos de ejemplo estructurado con registros reales y cursos académicos para pruebas de importación. |
| 🎨 [`06_GUIA_DISENO_VISUAL_STITCH.md`](./06_GUIA_DISENO_VISUAL_STITCH.md) | **Sistema de diseño visual completo** extraído de los prototipos de Google Stitch: paleta de colores institucional (Material Design 3), tipografía Inter, componentes UI (sidebar, KPIs, tablas, botones, badges, filtros), tokens de espaciado y 9 pantallas documentadas. |
| 📖 [`07_DOCUMENTACION_COMPLETA_DEL_SISTEMA.md`](./07_DOCUMENTACION_COMPLETA_DEL_SISTEMA.md) | **Documentación Integral del Sistema SIGECAP**: resumen ejecutivo, arquitectura técnica, manual de módulos (Dashboard, Capacitaciones, Matriz Docente, Padrón, Costos), modelo ERD, comandos de importación Excel, guía de despliegue y directrices OWASP. |
| 💻 [`sigecap/`](./sigecap/) | **Código fuente ejecutable del proyecto Django 5**: aplicaciones modulares (`core`, `capacitaciones`, `personas`, `catalogos`, `costos`), plantillas HTML, hoja de estilos CSS Material Design 3 y base de datos inicializada. |
| 📁 [`stitch_sistema_de_gesti_n_de_capacitaciones/`](./stitch_sistema_de_gesti_n_de_capacitaciones/) | Carpeta con los **9 prototipos HTML originales de Google Stitch** y sus capturas de pantalla (`code.html` + `screen.png` por vista). |

---

## 🚀 Resumen del Stack Tecnológico: Python + Django + PostgreSQL

* **Lenguaje y Framework Principal:** **Python 3.11+ con Django 5.x**
  * **Django Admin Integrado:** Proporciona de inmediato un panel administrativo completo, seguro y configurable para gestionar todos los catálogos (áreas, tipos, facultades, proveedores y proyectos) sin necesidad de programar pantallas administrativas desde cero.
  * **Django ORM y Migraciones:** Mapeo objeto-relacional robusto que garantiza la integridad de los datos y control estricto de versiones de la base de datos.
  * **Manejo Seguro de Excel:** Integración nativa con `pandas` y `openpyxl` con protección de analizadores XML (`defusedxml`) y desinfección contra inyección de fórmulas CSV.
  * **Seguridad Nativa OWASP:** Protección automática contra inyecciones SQL, ataques CSRF, XSS, secuestro de clics y gestión integrada de contraseñas con sal única (PBKDF2/Argon2).
* **Base de Datos:** **PostgreSQL 15+** (Relacional, transaccional, estándar en el sector educativo, con triggers de base de datos para garantizar auditorías inmutables que impiden borrado o alteración de registros).
* **Frontend y Vistas:** Plantillas Django (DTL) con **Tailwind CSS** configurado con los tokens de color y tipografía de Material Design 3 extraídos de Google Stitch. Componentes interactivos para dashboards con **Chart.js** y gráficas SVG.
* **Diseño Visual:** Sistema de diseño **SIGECAP** basado en 9 prototipos de Google Stitch con paleta institucional azul (`primary: #00236f`, `secondary: #0051d5`), tipografía **Inter** y componentes Material You.
* **Despliegue Seguro:** Empaquetado completo con `Docker Compose` (PostgreSQL en red interna aislada sin exponer puertos públicos, contenedor web sin privilegios root y Nginx con cabeceras de seguridad HSTS y CSP).

---

## 🛡️ Principales Vulnerabilidades Mitigadas en el Diseño

1. **Carga Maliciosa de Archivos:** Renombrado forzoso a UUIDv4 aleatorio, validación binaria de tipo MIME real por Magic Bytes (`python-magic`) y prohibición de ejecución de scripts en `/media/`.
2. **Inyección de Fórmulas CSV:** Sanitización automática anteponiendo comilla simple (`'`) a cualquier celda que inicie con `=`, `+`, `-`, `@`, `|`, `%`.
3. **Control de Acceso Roto (IDOR / BOLA):** Autorización estricta a nivel de objeto en Django ORM para que ningún docente o gestor pueda ver ni descargar evidencias ajenas.
4. **Ataques de Fuerza Bruta:** Bloqueo temporal de cuentas e IPs tras 5 intentos fallidos consecutivos de login (`django-axes`).
5. **Auditoría Inalterable:** Trigger en PostgreSQL que rechaza operaciones de `UPDATE` o `DELETE` sobre la tabla `auditoria_log`.

---

## 🎨 Pantallas Diseñadas en Google Stitch (9 Vistas Prototipadas)

| # | Pantalla | Descripción Funcional |
|---|---|---|
| 1 | **Dashboard Principal** | Tablero de control con 5 KPIs (inversión, programas, personas, horas, satisfacción), gráfica de tendencia anual y ranking de mayor demanda. |
| 2 | **Listado de Capacitaciones** | Tabla maestra con filtros por estado, área, facultad y modalidad. Badges de código, barra de progreso, paginación. |
| 3 | **Detalle de Capacitación** | Ficha completa de un evento: datos generales, proveedor, participantes, costos y evidencias. |
| 4 | **Formulario de Nueva Capacitación** | Formulario multi-sección con validaciones, selección de catálogos y asignación de facultades. |
| 5 | **Ficha de Participante** | Historial acumulativo: horas por área, cronograma de cursos, diplomas y gráfica radar de perfil. |
| 6 | **Costos y Presupuesto** | Vista financiera: planificado vs. ejecutado, desglose por rubro y proyección de cierre. |
| 7 | **Portal Docente** | Vista personal del docente: sus capacitaciones, progreso y diplomas propios. |
| 8 | **Administración de Catálogos** | Gestión CRUD de facultades, áreas, proveedores y proyectos con KPIs de salud. |
| 9 | **Reportes y Analíticas** | Dashboards avanzados con filtros cruzados, exportación PDF/Excel y comparativas interanuales. |

---

## 👥 Roles del Sistema
1. **Administrador del Sistema:** Gestión total de catálogos vía Django Admin, capacitaciones, usuarios, costos y consulta de bitácora inmutable de auditoría.
2. **Gestor de Capacitación:** Coordinación de eventos de sus áreas formativas, registro de asistencias y subida de evidencias.
3. **Directivo / Consulta:** Visualización de dashboards de inversión, cobertura docente y reportes ejecutivos consolidados.
4. **Docente / Administrativo:** Consulta de historial formativo acumulado y descarga de constancias y diplomas propios.
