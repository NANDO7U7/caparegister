import csv
from pathlib import Path

import openpyxl
from openpyxl.formula import Tokenizer
from openpyxl.utils.cell import range_boundaries
from django.conf import settings
from django.test import SimpleTestCase

from .management.commands.import_matriz_excel import Command


class PlantillasSinteticasTests(SimpleTestCase):
    def test_ruta_predeterminada_y_opcion_file(self):
        parser = Command().create_parser('manage.py', 'import_matriz_excel')
        ruta = Path(parser.parse_args([]).file)
        self.assertTrue(ruta.is_absolute())
        self.assertEqual(
            ruta, settings.BASE_DIR.parent / 'docs' / 'plantillas' /
            'plantilla_formaciones_sintetica.xlsx',
        )
        self.assertTrue(ruta.is_file())
        self.assertEqual(parser.parse_args(['--file', 'otro.xlsx']).file, 'otro.xlsx')

    def test_lectura_sin_importar_registros(self):
        ruta = Command().create_parser('manage.py', 'import_matriz_excel').parse_args([]).file
        libro = openpyxl.load_workbook(ruta, read_only=True, data_only=True)
        try:
            self.assertEqual(len(libro.sheetnames), 4)
            hoja = libro['Formación x persona D-SM']
            personas = [fila for fila in hoja.iter_rows(min_row=3, values_only=True)
                        if fila[3] not in (None, '', 0, '0')]
            self.assertEqual(len(personas), 1)
            persona = personas[0]
            self.assertIn('SINTETICO', persona[3])
            self.assertEqual(persona[2], 'Tiempo Completo')
            self.assertIn(persona[5], ('M', 'F'))
            self.assertEqual(persona[7], 'En Curso')
        finally:
            libro.close()

    def test_formulas_y_referencias_internas(self):
        ruta = Command().create_parser('manage.py', 'import_matriz_excel').parse_args([]).file
        libro = openpyxl.load_workbook(ruta, data_only=False)
        try:
            formulas = 0
            for hoja in libro:
                for fila in hoja:
                    for celda in fila:
                        if celda.data_type != 'f':
                            continue
                        formulas += 1
                        self.assertNotIn('#REF!', celda.value)
                        for token in Tokenizer(celda.value).items:
                            if token.type != 'OPERAND' or token.subtype != 'RANGE':
                                continue
                            referencia = token.value
                            self.assertNotIn('[', referencia)
                            if '!' in referencia:
                                nombre, referencia = referencia.rsplit('!', 1)
                                self.assertIn(nombre.strip("'").replace("''", "'"), libro.sheetnames)
                            range_boundaries(referencia)
            self.assertEqual(formulas, 93)
        finally:
            libro.close()

    def test_csv_sintetico(self):
        ruta = settings.BASE_DIR.parent / 'docs' / 'plantillas' / 'plantilla_migracion_sintetica.csv'
        with ruta.open(encoding='utf-8', newline='') as archivo:
            reader = csv.DictReader(archivo)
            self.assertEqual(len(reader.fieldnames), 21)
            filas = list(reader)
        self.assertEqual(len(filas), 5)
        for fila in filas:
            self.assertIn('SINTETICO', fila['Nombres_Participante'])
            self.assertTrue(fila['Codigo_Empleado'].startswith('SYN-'))
            self.assertTrue(fila['Email_Participante'].endswith('@example.invalid'))
