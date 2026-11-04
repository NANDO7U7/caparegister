# Plantillas sintéticas

Estos archivos contienen datos ficticios identificados con `SINTETICO`,
`FICTICIO` o `SYN`. No representan personas ni información institucional real.

- [Excel de formaciones](plantilla_formaciones_sintetica.xlsx): mantiene las
  cuatro hojas, encabezados, fórmulas, tipos de columnas, rangos combinados y
  tabla estructurada de la plantilla de referencia. No había validaciones de
  datos definidas. Se excluyeron comentarios, imagen y metadatos originales.
- [CSV de migración](plantilla_migracion_sintetica.csv): conserva las 21 columnas
  y cinco registros ficticios. Los correos usan `example.invalid`.

El Excel se verificó con `openpyxl` en modo de solo lectura y con el mapeo
de columnas utilizado por `import_matriz_excel`. No se ejecutó el comando de
importación ni se conectó a una base de datos. Las fórmulas se conservan, pero
openpyxl no calcula sus resultados: Excel debe recalcularlas al abrir el libro.
El importador de personas consume la tercera hoja, sin fórmulas.

## Uso y originales institucionales

El importador `import_matriz_excel` selecciona por defecto este Excel mediante
una ruta absoluta calculada desde la raíz del proyecto, independiente del
directorio de trabajo. `--file` conserva la posibilidad de seleccionar otro
archivo. Ejecutar el importador escribe en la base de datos y requiere una base
autorizada; la validación de estas plantillas solo realiza lecturas.

El usuario confirmó un respaldo externo privado y restringido de los cuatro
originales. Se retiraron del seguimiento los dos Excel institucionales, el CSV
original y el Word de directorios; las copias locales se conservan e ignoran.
Los respaldos externos no fueron modificados ni eliminados.

El comentario diferente entre ambos Excel queda conservado en los respaldos:
misma celda, autor y longitud, con texto distinto. La variante no aporta valores
de celdas ni fórmulas exclusivos. Su interpretación queda para revisión privada.

La retirada no elimina los datos del historial Git. Cualquier limpieza del
historial requiere una autorización independiente.
