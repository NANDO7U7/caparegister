# Guía de Diseño Visual y Sistema de Diseño (Design System)
## Sistema de Gestión de Capacitaciones Docentes y Administrativas (SIGECAP)

> Extraído y documentado a partir de los prototipos generados en **Google Stitch**.
> Basado en **Material Design 3 (Material You)** con variaciones personalizadas para identidad institucional universitaria.

---

## 1. Identidad del Producto

* **Nombre Comercial del Sistema:** SIGECAP (Sistema de Gestión de Capacitaciones)
* **Versión de Interfaz:** v2.4
* **Paradigma de Diseño:** Material Design 3 (Material You) — Google
* **Framework CSS:** Tailwind CSS (con configuración personalizada de tokens M3)
* **Tipografía Principal:** **Inter** (Google Fonts)
* **Iconografía:** Material Symbols Outlined (variable: peso, relleno, grado)

---

## 2. Paleta de Colores Institucional (Material Design 3 Tokens)

### 2.1 Colores Primarios y de Marca

| Token de Diseño | Código HEX | Uso Principal |
|---|---|---|
| `primary` | **`#00236f`** | Textos de títulos principales, encabezados de secciones, sidebar activo, badges de código de capacitación |
| `secondary` | **`#0051d5`** | Botones de acción secundarios, íconos activos, enlaces, etiquetas de estado "En Curso", gráficas de líneas |
| `primary-container` | **`#1e3a8a`** | Fondo del sidebar / barra lateral de navegación |
| `secondary-container` | **`#316bf3`** | Hover de botones secundarios, contenedores de acento |
| `on-primary` | **`#ffffff`** | Texto blanco sobre fondos primarios |
| `on-secondary` | **`#ffffff`** | Texto blanco sobre fondos secundarios |

### 2.2 Superficies y Fondos

| Token de Diseño | Código HEX | Uso Principal |
|---|---|---|
| `background` / `surface` | **`#f8f9ff`** | Fondo general de la aplicación (gris azulado ultra claro) |
| `surface-container-lowest` | **`#ffffff`** | Fondo de tarjetas KPI, tablas y paneles de contenido |
| `surface-container-low` | **`#eff4ff`** | Fondo de filas alternadas, hover suave en tablas, badges de íconos |
| `surface-container` | **`#e5eeff`** | Hover activo, separadores visuales |
| `surface-container-high` | **`#dce9ff`** | Fondos de filtros, barras de progreso inactivas |
| `surface-container-highest` | **`#d3e4fe`** | Encabezados de tabla, badges numéricos de ranking |

### 2.3 Texto y Contraste

| Token de Diseño | Código HEX | Uso Principal |
|---|---|---|
| `on-surface` | **`#0b1c30`** | Texto principal sobre superficies claras (títulos, nombres, datos numéricos) |
| `on-surface-variant` | **`#444651`** | Texto secundario descriptivo (subtítulos, metadatos, etiquetas de facultad) |
| `outline` | **`#757682`** | Texto terciario (fechas de actualización, placeholders, leyendas de gráficas) |
| `outline-variant` | **`#c5c5d3`** | Bordes de separación, líneas divisorias de tablas |

### 2.4 Estados de Éxito, Advertencia y Error

| Token de Diseño | Código HEX | Uso Principal |
|---|---|---|
| `tertiary` | **`#00312c`** | Texto oscuro sobre fondos de éxito/aprobación |
| `tertiary-fixed` | **`#89f5e7`** | Badges de estado "Aprobó" / "Finalizada" (verde menta brillante) |
| `tertiary-fixed-dim` | **`#6bd8cb`** | Indicadores de tendencia positiva (+12.4%, Meta superada) |
| `tertiary-container` | **`#004942`** | Fondo oscuro de indicadores verdes |
| `error` | **`#ba1a1a`** | Texto de error, badges de "Cancelada", alertas críticas |
| `error-container` | **`#ffdad6`** | Fondo de mensajes de error y notificaciones críticas |

### 2.5 Colores Complementarios (Fixed / Inverse)

| Token de Diseño | Código HEX | Uso |
|---|---|---|
| `secondary-fixed` | **`#dbe1ff`** | Fondo de badges de "Periodo Académico Activo" |
| `secondary-fixed-dim` | **`#b4c5ff`** | Fondo de estados seleccionados |
| `inverse-surface` | **`#213145`** | Fondos oscuros para tooltips e info contextual |
| `inverse-on-surface` | **`#eaf1ff`** | Texto sobre fondos oscuros invertidos |

---

## 3. Tipografía (Escala de Tipos Material Design 3)

| Nombre del Token | Familia | Tamaño | Line-Height | Peso | Uso en la Interfaz |
|---|---|---|---|---|---|
| `headline-xl` | Inter | 32px | 40px | 700 (Bold) | Títulos de página ("Tablero de Control", "Gestión y Catálogo") |
| `headline-lg` | Inter | 28px | 36px | 700 | Valores numéricos KPI grandes ($148,250 / 42 Programas / 1,240 Pax) |
| `headline-md` | Inter | 24px | 32px | 600 | Subtítulos de secciones dentro de paneles |
| `headline-sm` | Inter | 20px | 28px | 600 | Nombres de capacitación en tarjetas de detalle |
| `body-lg` | Inter | 16px | 24px | 400 | Párrafos descriptivos, instrucciones de formulario |
| `body-md` | Inter | 14px | 20px | 400 | Descripciones de contexto debajo de títulos |
| `body-sm` | Inter | 12px | 16px | 400 | Texto dentro de celdas de tabla, items de ranking |
| `label-md` | Inter | 14px | 20px | 500 | Textos de botones, etiquetas de filtros activos |
| `label-sm` | Inter | 11px | 16px | 500 | Badges de estado, etiquetas de íconos KPI, leyendas de gráficas |
| `data-tabular` | Inter | Variable | — | 600-700 | Cifras numéricas y monetarias con alineación tabular (`font-variant-numeric: tabular-nums`) |

---

## 4. Componentes de Interfaz Documentados (UI Kit)

### 4.1 Barra Lateral de Navegación (Sidebar)
* **Fondo:** `primary-container` (`#1e3a8a`) — azul oscuro institucional.
* **Texto de ítems:** `on-primary` (`#ffffff`) blanco.
* **Ítem activo:** Fondo `secondary` (`#0051d5`) con texto blanco y bordes redondeados (`rounded-lg`).
* **Logo:** "SIGECAP" en blanco con subtítulo "Gestión de...".
* **Secciones agrupadas:**
  * MÓDULOS PRINCIPALES: Dashboard, Capacitaciones, Participantes, Proveedores, Costos y Presupuesto, Evidencias, Reportes.
  * DOCENCIA Y GESTIÓN: Mi Portal Docente, Importación desde Excel, Administración de Catálogos.
  * SISTEMA: Administración.
* **Footer del sidebar:** Botón "Importador Masivo" y versión "v2.4".

### 4.2 Barra Superior (Top Bar)
* **Fondo:** `surface-container-lowest` (`#ffffff`).
* **Buscador global:** Input con placeholder "Buscar capacitación, docente o proveedor..." y atajo `⌘K`.
* **Selector de año:** Badge "Año Académico 2024" con ícono de calendario.
* **Notificaciones:** Ícono de campana con badge numérico rojo para alertas pendientes.
* **Rol activo:** Badge "Administrador General" con punto verde de estado.
* **Avatar de usuario:** Iniciales circulares o foto con nombre, cargo y área.

### 4.3 Tarjetas KPI (Key Performance Indicators)
* **Contenedor:** `surface-container-lowest` (`#ffffff`), bordes redondeados `xl` (0.75rem), sombra `shadow-sm`.
* **Etiqueta superior:** `label-sm`, `uppercase`, `tracking-wider`, color `outline`.
* **Valor principal:** `headline-lg`, `font-data-tabular`, color `on-surface`.
* **Subtexto:** `label-sm`, color `outline` o `on-surface-variant`.
* **Indicador de tendencia:** Color `tertiary-fixed-dim` (`#6bd8cb`) con ícono `trending_up`.
* **Barra de progreso:** Fondo `surface-container-high`, relleno con `tertiary-container`.

### 4.4 Tablas de Datos
* **Encabezados:** `label-sm`, `uppercase`, `tracking-wider`, color `outline`, con íconos de ordenamiento.
* **Filas:** Fondo alternado entre `surface-container-lowest` y `surface-container-low`.
* **Hover:** Transición suave hacia `surface-container`.
* **Badges de código:** Bordes redondeados `rounded-md`, fondo `surface-container-low`, texto `primary`, fuente monoespaciada (`data-tabular`).
* **Badges de modalidad:** Bordes redondeados `rounded-full`, colores contextuales.
* **Paginación:** Botones circulares, activo con fondo `secondary` y texto blanco.

### 4.5 Botones
* **Primario (CTA):** Fondo `secondary` (`#0051d5`), texto blanco, `rounded-lg`, hover hacia `primary` (`#00236f`).
* **Secundario:** Fondo `surface-container-lowest` (`#ffffff`), texto `on-surface`, borde `shadow-sm`, hover hacia `surface-container-low`.
* **De texto / enlace:** Color `secondary`, sin fondo, con flecha `arrow_forward`.

### 4.6 Filtros y Chips
* **Chip activo:** Fondo `primary-container` (`#1e3a8a`), texto blanco, badge numérico integrado.
* **Chip inactivo:** Fondo transparente, texto `on-surface-variant`, punto de color de estado (verde, amarillo, rojo).
* **Selectores dropdown:** Fondo blanco, ícono de chevron, sombra suave.

### 4.7 Badges de Estado de Capacitación
* **En Curso:** Punto `secondary` (`#0051d5`) + texto azul.
* **Planificada:** Punto `outline` (`#757682`) + texto gris.
* **Finalizada:** Punto `tertiary-fixed-dim` (`#6bd8cb`) + texto verde.
* **Cancelada:** Punto `error` (`#ba1a1a`) + texto rojo.

---

## 5. Layout y Estructura de Páginas

### 5.1 Grid Principal
* **Sidebar fijo:** Ancho ~220px, posición fija a la izquierda.
* **Área de contenido:** Margen izquierdo de 220px, padding interno `space-xl` (2rem).
* **Grid de contenido:** `grid-cols-12` de Tailwind para layouts responsive.
* **Espaciado entre bloques:** `gap-space-md` (1rem) o `gap-space-lg` (1.5rem).

### 5.2 Pantallas Documentadas desde Google Stitch

| # | Pantalla | Descripción Funcional |
|---|---|---|
| 1 | **Dashboard Principal** | Tablero de control con 5 KPIs (inversión, programas, personas, horas, satisfacción), gráfica de tendencia anual y ranking de mayor demanda. |
| 2 | **Listado de Capacitaciones** | Tabla maestra con filtros por estado, área, facultad y modalidad. Badges de código, barra de progreso de inscripción, paginación. |
| 3 | **Detalle de Capacitación** | Ficha completa de un evento: datos generales, proveedor, lista de participantes con estados, costos desglosados y evidencias adjuntas. |
| 4 | **Formulario de Nueva Capacitación** | Formulario multi-sección con validaciones, selección de catálogos, rango de fechas y asignación de facultades beneficiadas. |
| 5 | **Ficha de Participante** | Historial acumulativo del docente: horas por área formativa, cronograma de cursos, diplomas descargables y gráfica radar de perfil. |
| 6 | **Costos y Presupuesto** | Vista financiera: comparativa planificado vs. ejecutado, desglose por rubro, gráficas de barras y proyección de cierre. |
| 7 | **Portal Docente** | Vista personal del docente: sus capacitaciones, progreso de horas, diplomas propios y certificaciones pendientes. |
| 8 | **Administración de Catálogos** | Gestión CRUD de facultades, áreas, proveedores y proyectos con KPIs de salud de catálogo y auditoría. |
| 9 | **Reportes y Analíticas** | Dashboards avanzados con filtros cruzados, exportación PDF/Excel y comparativas interanuales. |

---

## 6. Principios de Interacción y Micro-Animaciones

* **Hover en filas de tabla:** `transition-colors` de 150ms hacia `surface-container`.
* **Hover en botones:** `transition-colors` de 150ms, botón primario cambia de `secondary` a `primary`.
* **Punto de "Periodo Activo":** Animación `animate-pulse` en el indicador verde de la barra superior.
* **Barras de progreso KPI:** Ancho animado con CSS `transition: width 0.6s ease`.
* **Badges numéricos:** Aparecen con opacidad suave al cargar.

---

## 7. Espaciado y Tokens de Layout

| Token | Valor | Uso |
|---|---|---|
| `space-xs` | 0.25rem (4px) | Gaps mínimos entre ícono y texto |
| `space-sm` | 0.5rem (8px) | Padding interno de badges y chips |
| `space-md` | 1rem (16px) | Gap entre tarjetas KPI, padding de secciones |
| `space-lg` | 1.5rem (24px) | Padding interno de paneles principales |
| `space-xl` | 2rem (32px) | Márgenes generales del área de contenido |
| `margin` | 2rem | Margen externo de bloques principales |
| `margin-sm` | 1.25rem | Margen reducido en vistas compactas |
| `gutter` | 1.5rem | Espacio entre columnas del grid |
| `gutter-sm` | 1rem | Espacio entre columnas en móvil |

---

## 8. Radios de Borde

| Token | Valor | Uso |
|---|---|---|
| `DEFAULT` | 0.25rem (4px) | Inputs, badges de código |
| `lg` | 0.5rem (8px) | Botones, items de navegación activos |
| `xl` | 0.75rem (12px) | Tarjetas KPI, paneles de contenido, tablas |
| `full` | 9999px | Avatares circulares, chips, badges de estado |
