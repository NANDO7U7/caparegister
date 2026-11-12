# Documentación Integral del Sistema SIGECAP
## Sistema de Gestión de Capacitaciones Docentes y Administrativas

> **Versión del Documento:** 1.2  
> **Fecha:** Octubre 2026  
> **Estado:** Implementado, Operativo y Funcional  
> **Stack Tecnológico:** Python 3.11+ / Django 5.x / PostgreSQL 16 / Material Design 3 (Google Stitch)  
> **Ubicación del Código:** `sigecap/`

---

## 1. Resumen Ejecutivo y Alcance del Proyecto

### 1.1 Problemática Universitaria Resuelta
Históricamente, la gestión de formaciones docentes y administrativas se realizaba mediante múltiples libros de Microsoft Excel dispersos por facultades y años fiscales. Esta práctica generaba:
* Pérdida de trazabilidad del historial formativo acumulado de cada profesor.
* Dificultad para medir el cumplimiento real del **Plan Integral de Formación Docente**.
* Desalineación entre los presupuestos aprobados y los gastos efectivamente ejecutados en viáticos, traslados y honorarios.
* Registro manual en listas de papel con alto riesgo de pérdida y lentitud operativa.
* Falta de un repositorio unificado para diplomas, constancias y evidencias digitales.

### 1.2 Objetivo del Sistema
**SIGECAP** centraliza, automatiza y asegura todo el ciclo de vida de la capacitación universitaria: desde la planificación y registro del evento formativo, el control de asistencia digital sin papel por código QR, el despacho de notificaciones y recordatorios, el control financiero por rubros, la acreditación de horas y emisión de certificados, hasta el seguimiento en tiempo real de la **Matriz Docente** institucional y el portal personal de trayectoria.

```
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│                                         SIGECAP                                           │
│   ┌───────────────────────┐   ┌────────────────────────┐   ┌──────────────────────────┐   │
│   │Calendario y Asistencia│   │ Experiencia Docente    │   │  Costos y Presupuesto    │   │
│   │ • Calendario Mensual  │   │ • Mi Trayectoria       │   │ • Plan vs. Ejecutado     │   │
│   │ • Código QR Asistencia│   │ • Metas Anuales (40h)  │   │ • Bitácora Comprobantes  │   │
│   │ • Duplicar Eventos    │   │ • Constancia PDF Firm. │   │ • Rubros de Gasto        │   │
│   │ • Control Evidencias  │   │ • Encuestas CSAT       │   │                          │   │
│   │                       │   │ • Matriz 18 Competenc. │   │                          │   │
│   └───────────┬───────────┘   └───────────┬────────────┘   └────────────┬─────────────┘   │
│               └───────────────────────────┼─────────────────────────────┘                 │
│                                           ▼                                               │
│                         ┌───────────────────────────────────┐                             │
│                         │   Padrón Central de Participantes │                             │
│                         │   (Historial Acumulativo de Horas)│                             │
│                         └───────────────────────────────────┘                             │
└───────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Arquitectura de Software y Stack Tecnológico

El sistema fue desarrollado bajo los más altos estándares de robustez, escalabilidad y seguridad:

| Componente | Tecnología Seleccionada | Justificación Técnica |
|---|---|---|
| **Lenguaje Backend** | **Python 3.11+ / 3.14** | Tipado fuerte, procesamiento analítico de datos y seguridad. |
| **Framework Web** | **Django 5.x** | Arquitectura MVT (Model-View-Template), ORM robusto anti-SQL Injection, autenticación integrada y panel administrativo nativo. |
| **Base de Datos** | **PostgreSQL 16** / SQLite (Dev) | Soporte de transacciones ACID, tipos UUID nativos, índices optimizados y compatibilidad dual. |
| **Diseño Visual (Frontend)** | **Material Design 3 (Google Stitch)** | Paleta de colores institucional (`#00236f`, `#0051d5`), tipografía **Inter**, iconos **Material Symbols Outlined** y contenedores limpios. |
| **Skill de Diseño UI/UX** | **Apple Design Skill (`apple-design`)** | Integración de 123 guías HIG de Apple (`references/hig/`), principios de diseño craft, materiales traslúcidos (*Liquid Glass / Frosted Glass*), accesibilidad WCAG y micro-interacciones fluidas. |
| **Calendario Interactivo** | **FullCalendar 6.x** | Visualización mensual, semanal y por lista con filtros reactivos por facultad. |
| **Generación QR & PDF** | **qrcode / ReportLab** | Generación dinámica de códigos QR para asistencia móvil y constancias PDF oficiales con firma digital y hash. |
| **Visualización Analítica** | **Chart.js v4** | Gráficas interactivas de tendencias de capacitación y distribución por áreas formativas. |
| **Procesamiento de Archivos** | **Pandas / Openpyxl / DefusedXML** | Lectura segura e ingesta automatizada de matrices y libros de Excel institucionales. |
| **Contenerización** | **Docker & Docker Compose** | Despliegue estandarizado en contenedores listos para producción. |

---

## 3. Módulos Funcionales del Sistema

### 3.1 Dashboard Principal y KPIs (`/`)
* **5 Indicadores Clave en Tiempo Real:**
  1. *Total de Capacitaciones Registradas.*
  2. *Docentes Formados con Aprobación.*
  3. *Inscripciones Totales y Evaluaciones Aprobadas.*
  4. *Horas Académicas Impartidas.*
  5. *Inversión Presupuestaria Ejecutada.*
* **Gráfica de Tendencia Mensual:** Muestra la evolución temporal de docentes capacitados a lo largo del año.
* **Gráfica Doughnut por Áreas Formativas:** Distribución porcentual entre ejes pedagógicos, tecnológicos, investigación, etc.
* **Tabla de Eventos Recientes:** Acceso directo con chips de estado (*Planificada*, *En Curso*, *Finalizada*, *Cancelada*).

---

### 3.2 Módulo de Calendario y Asistencia (`/capacitaciones/calendario/`)

Este módulo agiliza el trabajo diario de la coordinación de capacitación eliminando cuellos de botella y procesos manuales:

#### A. Calendario Institucional de Capacitaciones (`/capacitaciones/calendario/`)
* **Vistas Temporales Múltiples:** Vista mensual por cuadrícula (`Mes`), semanal detallada (`Semana`) y agenda cronológica (`Agenda / Lista`).
* **Filtros Reactivos:** Filtrado simultáneo por **Facultad / Unidad Destinataria**, **Área Formativa** y **Estado de la Capacitación**.
* **Modal Interactivo de Evento:** Al hacer clic sobre cualquier evento, se despliega una tarjeta flotante con información clave (Horas, Lugar, Facilitador, Inscritos) y accesos directos de 1 clic:
  * *Ver Ficha Completa.*
  * *Póster QR de Asistencia.*
  * *Duplicar Capacitación.*

#### B. Control de Asistencia por Código QR (`/capacitaciones/<uuid>/qr-asistencia/`, `/capacitaciones/<uuid>/asistencia-qr/`)
* **Póster de Aula / Proyección en Pantalla Completa:**
  * Genera un póster imprimible o proyectable con el Código QR de alta resolución, membrete oficial, nombre del curso, horas y pasos a seguir.
* **Auto-Registro Móvil del Participante:**
  * El docente o administrativo escanea el código con su teléfono celular o tablet.
  * Ingresa su Código de Empleado, DNI o Correo Institucional (con selector predictivo).
  * Validación instantánea en base de datos: actualiza la participación a estado **Asistió** y acredita las horas lectivas correspondientes en su expediente.
  * Despliega pantalla de confirmación visual y enlace directo a su portal personal.
* **Cero Listas en Papel:** Elimina el uso de planillas físicas, reduciendo tiempos de digitación y posibles extravíos.

#### D. Duplicación / Clonación de Capacitaciones (`/capacitaciones/<uuid>/duplicar/`)
* **Creación de Nuevas Ediciones en Segundos:** Permite tomar cualquier capacitación anterior y clonar en 1 clic toda su estructura:
  * Área formativa y modalidad (*Presencial, Virtual, Híbrida*).
  * Proveedor / Facilitador y objetivos pedagógicos.
  * Carga horaria y cupo estándar.
  * Facultades beneficiarias destinatarias.
* El coordinador únicamente ajusta las nuevas fechas del calendario y confirma.

#### E. Estado de Evidencias Digitales y Diplomas (`/capacitaciones/<uuid>/cargar-evidencia/`)
* **Semáforo Visual en Listados y Fichas:**
  * 🔴 *Pendientes (Crítico):* Curso finalizado sin actas ni constancias cargadas.
  * 🟢 *Completas (N Archivos):* Expediente con documentos oficiales verificados.
  * 🔵 *En Plazo:* Cursos planificados o en curso.
* **Repositorio Digital:** Carga clasificada de archivos (Listas firmadas, Fotografías del evento, Informes de resultados, Sílabos, Copias de Diplomas, Comprobantes de pago).

---

### 3.3 Módulo de Experiencia del Docente y Portal "Mi Trayectoria" (`/personas/portal/`)
* **Línea de Tiempo Visual ("Mi Trayectoria"):** Vista cronológica con nodos interactivos que exhiben el histórico de capacitaciones cursadas, fechas, modalidad, horas acreditadas y diplomas obtenidos.
* **Metas de Horas Anuales:** Barra de progreso dinámica que compara las horas acumuladas en el año fiscal respecto al mínimo institucional fijado por la universidad (**40 horas anuales**), indicando el porcentaje de cumplimiento y horas restantes.
* **Generación de Constancia Oficial en PDF (`/personas/<uuid>/constancia-pdf/`):** Generador de expediente en PDF formal con membrete institucional, tabla detallada de cursos aprobados, horas acreditadas, promedios, firmas de la Coordinación de Capacitación y Dirección de Talento Humano, y código de verificación digital.
* **Encuestas de Satisfacción y Calidad (`/capacitaciones/<uuid>/encuesta/`):**
  * Instrumento de evaluación post-evento con escala de 1 a 5 estrellas en 4 dimensiones: *Claridad del Facilitador*, *Dominio del Tema*, *Utilidad Práctica* y *Calidad de Recursos y Entorno*.
  * Registro de retroalimentación cualitativa (aspectos destacados y sugerencias de mejora).
  * Consolidación automática del índice CSAT y métricas de satisfacción en el Dashboard Principal y en la Ficha de cada Capacitación.

---

### 3.4 Módulo de la Matriz Docente (`/personas/matriz/`)
Basado en la hoja institucional `Formación x persona D-SM` del libro de Excel:
* **Cuadrícula Interactiva (Matrix Grid):** Fila por cada docente y columnas para las **18 competencias del Plan Integral de Formación**:
  1. *Formación Académica:* Maestría, Doctorado.
  2. *Formación Pedagógica:* Inducción Curricular, Construcción de Competencias (Enfoque Socioformativo), Estrategias Didácticas, Tertulias Pedagógicas, Aula Invertida.
  3. *Formación en Investigación:* Fundamentos de Investigación, Cómo elaborar artículo académico, Visibilización de la producción científica, Elaboración de Encuestas.
  4. *Formación Integral:* Género e Inclusión en Educación Superior, Lengua de Señas Salvadoreña (LESSA).
  5. *Formación en Virtualidad y Tecnología:* Certificación en Diseño y Desarrollo para Educación Virtual, Inducción Profesor Tutor, Experto en Tutoría Virtual, Inducción a Genially.
  6. *Formación en Especialidad:* Diplomados y cursos de especialidad profesional.
* **Cálculo de `% de Avance`:** Porcentaje de cumplimiento institucional en tiempo real por profesor.
* **Modal de Matrícula Directa:** Permite cambiar el estado (*Aprobado*, *En Curso*, *Pendiente*) y registrar la fecha exacta de diploma con un solo clic.

---

### 3.5 Padrón de Participantes y Ficha Individual (`/personas/`)
* **Directorio General:** Listado de docentes y personal administrativo con filtros por tipo de contrato (*Tiempo Completo, Hora Clase, Medio Tiempo*), grado académico (*Licenciatura, Maestría, Doctorado*) y facultad.
* **Registro de Nuevo Docente (`/personas/nuevo/`):** Alta con auto-generación de código y auto-matriculación en la matriz docente.
* **Ficha Individual de Trayectoria (`/personas/<uuid>/`):** Hoja de vida institucional que consolida:
  * Histórico acumulado de horas acreditadas año tras año.
  * Listado cronológico de todas las capacitaciones aprobadas y calificaciones.
  * Resumen del estado en la matriz de competencias.
* **Edición de Expediente (`/personas/<uuid>/editar/`):** Actualización de cargos, unidad de adscripción y datos de contacto.

---

### 3.6 Control Presupuestal y Financiero (`/costos/`)
* **KPIs Financieros:** Presupuesto Total Asignado, Gasto Planificado, Gasto Ejecutado (Pagado) y Saldo Disponible.
* **Desglose por Rubros:** Barras de avance por *Inscripción / Honorarios*, *Materiales Didácticos*, *Alimentación / Refrigerios*, *Transporte*, *Viáticos y Hospedaje*, *Plataformas Virtuales* y *Certificación*.
* **Bitácora de Comprobantes:** Registro de números de factura, recibos y órdenes de compra asociadas a cada evento.

---

### 3.7 Catálogos Institucionales Dinámicos (`/catalogos/`)
Administración ágil e independiente de las entidades maestras de la universidad:
* **Facultades y Centros Regionales** (Código y Nombre oficial).
* **Áreas / Ejes Formativos**.
* **Tipos y Modalidades** (*Cursos, Talleres, Diplomados, Congresos*).
* **Proveedores e Instituciones Capacitadoras** (*Internos y Externos*).
* **Proyectos y Fondos de Financiamiento**.

---

## 4. Estructura de Base de Datos Relacional

```
 ┌──────────────┐         ┌────────────────────────┐         ┌──────────────────────┐
 │  FACULTADES  │◄────────┤        PERSONAS        ├────────►│  MATRICULAS_MATRIZ   │
 └──────────────┘         └───────────┬────────────┘         └──────────┬───────────┘
                                      │                                 │
                                      ▼                                 ▼
                          ┌────────────────────────┐         ┌──────────────────────┐
                          │     PARTICIPACIONES    │         │ COMPETENCIAS_MATRIZ  │
                          └───────────┬────────────┘         └──────────────────────┘
                                      │
                                      ▼
                          ┌────────────────────────┐         ┌──────────────────────┐
                          │     CAPACITACIONES     ├────────►│ GASTOS_CAPACITACION  │
                          └─────┬──────────────┬───┘         └──────────────────────┘
                                │              │
                                ▼              ▼
                    ┌─────────────────┐  ┌─────────────────────────┐
                    │   EVIDENCIAS    │  │  ENCUESTAS_SATISFACCION │
                    └─────────────────┘  └─────────────────────────┘
```

### Tablas y Modelos Principales:
1. `personas`: Padrón unificado con campos de contrato, grado académico, sexo, facultad y horas acumuladas.
2. `competencias_matriz`: Catálogo de las 18 competencias del Plan Integral Docente.
3. `matriculas_matriz_docente`: Relación N:M entre Persona y Competencia con estado (*Aprobado*, *En Curso*, *Pendiente*) y fecha de finalización.
4. `capacitaciones`: Registro de eventos formativos con horas, fechas, modalidad, estado, QR y evidencias.
5. `participaciones`: Inscripciones de personas en capacitaciones con calificaciones y horas acreditadas.
6. `evidencias`: Archivos y expedientes digitales (listas de asistencia, fotos, constancias, reportes).
7. `encuestas_satisfaccion`: Evaluaciones de calidad post-capacitación con 4 dimensiones CSAT.
8. `gastos_capacitaciones`: Control financiero y comprobantes por rubro.
9. `auditoria_logs`: Bitácora inmutable de trazabilidad de cambios (OWASP).

---

## 5. Integración con el Libro de Excel

Se utilizan [plantillas sintéticas del Excel y CSV](plantillas/README.md).
Los originales institucionales se retiraron del seguimiento tras confirmar su
respaldo privado. Esto no elimina la información del historial de Git.

El importador usa por defecto el [Excel sintético](plantillas/plantilla_formaciones_sintetica.xlsx).
La opción `--file` permite seleccionar otro libro compatible; solo debe usarse
con autorización para importar sus datos. Ejecutar el comando crea registros.

### Comandos de Gestión por Consola:
```powershell
# 1. Cargar catálogos base, personas y cursos de demostración:
python manage.py seed_data

# 2. Importar la matriz del Excel sintetico (solo sobre una base autorizada):
python manage.py import_matriz_excel

# 3. Validar integridad del sistema:
python manage.py check
```

---

## 6. Guía de Instalación y Puesta en Marcha

### 6.1 Requisitos Previos
* **Python 3.11+** instalado.
* **Git** (opcional para control de versiones).
* **Docker Desktop** (opcional para despliegue con base de datos PostgreSQL).

### 6.2 Pasos para Ejecutar en Entorno Local
1. **Abrir terminal en la carpeta del proyecto:**
   ```powershell
   cd sigecap/
   ```

2. **Instalar dependencias necesarias:**
   ```powershell
   python -m pip install -r requirements.txt
   ```

3. **Ejecutar migraciones de base de datos:**
   ```powershell
   python manage.py migrate --settings=sigecap.local_settings
   ```

4. **Iniciar el servidor de desarrollo:**
   ```powershell
   $env:DEBUG = 'True'
   python manage.py runserver 127.0.0.1:8080 --settings=sigecap.local_settings
   ```

5. **Abrir el sistema en el navegador:**
   👉 **`http://127.0.0.1:8000/`**

---

### 6.3 Acceso y configuracion segura

El acceso requiere una cuenta autorizada. No existen credenciales predeterminadas.
Consulta [seguridad.md](seguridad.md) para configurar variables de entorno,
ejecutar el servidor local y conocer la politica de permisos. Las migraciones
solo deben ejecutarse deliberadamente en una base nueva o autorizada, nunca como
parte de una revision contra datos existentes.

---

## 7. Directrices de Seguridad y Protección de Datos

En cumplimiento de las directrices **OWASP Top 10** y normativas institucionales:
1. **Prevención de Inyección SQL (A03):** Todo acceso a la base de datos se realiza mediante el ORM de Django con consultas parametrizadas.
2. **Protección CSRF (A01):** Todos los formularios POST incluyen token criptográfico de validación `@csrf_protect`.
3. **Control de Sesiones Seguras (A07):** Cookies configuradas con `HttpOnly` y `SameSite=Lax`.
4. **Validación de Archivos y Prevención de Malware:** Almacenamiento de evidencias digitales con renombramiento seguro y tipado MIME verificado.
5. **Auditoría Inmutable:** Registro de IPs, marcas de tiempo y usuarios en `AuditLog`.

---

## 8. Directorio de Archivos del Proyecto

```text
caparegister/
|-- README.md
|-- docs/
|   |-- 01_PLAN_DE_DESARROLLO.md
|   |-- arquitectura/02_ARQUITECTURA_Y_STACK.md
|   |-- 03_ESPECIFICACION_REQUERIMIENTOS.md
|   |-- 05_PLANTILLA_MIGRACION_EXCEL.md
|   |-- 06_GUIA_DISENO_VISUAL_STITCH.md
|   |-- 07_DOCUMENTACION_COMPLETA_DEL_SISTEMA.md
|   |-- plantillas/                     # Excel y CSV sinteticos
|   |-- historico/04_MODELO_DE_DATOS_POSTGRESQL.sql
|   `-- prototipos/sistema_gestion_capacitaciones.html
|-- e2e/                       # Pruebas Playwright e instrucciones AGENTS.md
|-- package.json
|-- package-lock.json
|-- playwright.config.ts
`-- sigecap/
    |-- manage.py
    |-- requirements.txt
    |-- docker-compose.yml
    |-- sigecap/               # Configuracion Django
    |-- apps/                 # Incluye las migraciones vigentes
    |-- static/               # Recursos fuente
    `-- templates/            # Plantillas utilizadas por Django
```

El SQL de `historico/` es un diseno historico: no sustituye las migraciones
Django ni debe ejecutarse para inicializar la base de la aplicacion.
Las rutas de ejecucion se interpretan desde la raiz del repositorio,
excepto cuando se indique expresamente `cd sigecap`.
