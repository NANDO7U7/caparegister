import os
from datetime import datetime
from django.conf import settings
from django.core.management.base import BaseCommand
import openpyxl
from apps.catalogos.models import Facultad
from apps.personas.models import Persona, CompetenciaMatriz, MatriculaMatrizDocente

class Command(BaseCommand):
    help = 'Importa y sincroniza la Matriz Docente desde la plantilla Excel institucional.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default=str(settings.BASE_DIR.parent / 'docs' / 'plantillas' / 'plantilla_formaciones_sintetica.xlsx'),
            help='Ruta del archivo Excel'
        )

    def handle(self, *args, **options):
        excel_path = options['file']
        if not os.path.exists(excel_path):
            self.stdout.write(self.style.ERROR(f"Archivo no encontrado: {excel_path}"))
            return

        self.stdout.write(self.style.NOTICE("1. Creando catálogo de competencias del Plan Integral Docente..."))

        # Definición de las 18 competencias de la Matriz Excel
        competencias_def = [
            # Formación Académica
            ("MAT-ACAD-01", "Maestría", "Formación Académica", 1),
            ("MAT-ACAD-02", "Doctorado", "Formación Académica", 2),
            
            # Formación Pedagógica
            ("MAT-PED-01", "Inducción Curricular para Docentes", "Formación Pedagógica", 3),
            ("MAT-PED-02", "Construcción de Competencias, Planeación y Evaluación en Educación Superior (Enfoque Socioformativo)", "Formación Pedagógica", 4),
            ("MAT-PED-03", "Estrategias Didácticas y Evaluación de Competencias desde el Enfoque Socioformativo", "Formación Pedagógica", 5),
            ("MAT-PED-04", "Tertulias Pedagógicas: Repensando nuestra práctica docente", "Formación Pedagógica", 6),
            ("MAT-PED-05", "Modelo de Aula Invertida", "Formación Pedagógica", 7),
            
            # Formación en Investigación
            ("MAT-INV-01", "Fundamentos para la Investigación", "Formación en Investigación", 8),
            ("MAT-INV-02", "Cómo elaborar un artículo académico", "Formación en Investigación", 9),
            ("MAT-INV-03", "Visibilización de la producción científica", "Formación en Investigación", 10),
            ("MAT-INV-04", "Elaboración de Encuestas y Análisis de Información", "Formación en Investigación", 11),
            
            # Formación Integral
            ("MAT-INT-01", "Género e Inclusión: Bases para su integración en la Educación Superior", "Formación Integral", 12),
            ("MAT-INT-02", "Lengua de Señas Salvadoreña (LESSA)", "Formación Integral", 13),
            
            # Formación en Virtualidad y Tecnología
            ("MAT-TEC-01", "Certificación en Diseño y Desarrollo para la Educación Virtual", "Formación en Virtualidad y Herramientas Tecnológicas", 14),
            ("MAT-TEC-02", "Inducción Profesor Tutor", "Formación en Virtualidad y Herramientas Tecnológicas", 15),
            ("MAT-TEC-03", "Experto en Tutoría Virtual", "Formación en Virtualidad y Herramientas Tecnológicas", 16),
            ("MAT-TEC-04", "Inducción a la Plataforma Genially", "Formación en Virtualidad y Herramientas Tecnológicas", 17),
            
            # Formación en Especialidad
            ("MAT-ESP-01", "Diplomado / Curso / Taller en Área de Especialidad", "Formación en el Área de Especialidad", 18),
        ]

        comp_objs = {}
        for cod, nom, cat, ord_num in competencias_def:
            c_obj, _ = CompetenciaMatriz.objects.get_or_create(
                codigo=cod,
                defaults={'nombre': nom, 'categoria': cat, 'orden': ord_num}
            )
            comp_objs[cod] = c_obj

        self.stdout.write(self.style.SUCCESS(f"[OK] {len(comp_objs)} Competencias de la Matriz configuradas."))

        # 2. Leer Hoja de Excel 'Formación x persona D-SM'
        self.stdout.write(self.style.NOTICE("2. Leyendo hoja 'Formación x persona D-SM'..."))
        wb = openpyxl.load_workbook(excel_path, data_only=True)
        if 'Formación x persona D-SM' not in wb.sheetnames:
            self.stdout.write(self.style.ERROR("No se encontró la hoja 'Formación x persona D-SM'."))
            return

        sheet = wb['Formación x persona D-SM']

        # Column mapping
        # Col 2: Facultad, Col 3: Tipo contrato, Col 4: Nombre, Col 5: Grado, Col 6: Sexo
        # Col 7: Maestría, Col 8: Doctorado
        # Col 9: Induccion, Col 10: Construccion, Col 11: Estrategias, Col 12: Tertulias, Col 13: Aula Invertida
        # Col 14: Fundamentos, Col 15: Como elaborar, Col 16: Visibilizacion, Col 17: Encuestas
        # Col 18: Genero, Col 19: LESSA
        # Col 20: Cert Virtual, Col 21: Induccion Tutor, Col 22: Experto Tutor, Col 23: Genially
        # Col 24: Especialidad Nombre, Col 25: Fecha
        
        col_to_comp = {
            7: "MAT-ACAD-01",
            8: "MAT-ACAD-02",
            9: "MAT-PED-01",
            10: "MAT-PED-02",
            11: "MAT-PED-03",
            12: "MAT-PED-04",
            13: "MAT-PED-05",
            14: "MAT-INV-01",
            15: "MAT-INV-02",
            16: "MAT-INV-03",
            17: "MAT-INV-04",
            18: "MAT-INT-01",
            19: "MAT-INT-02",
            20: "MAT-TEC-01",
            21: "MAT-TEC-02",
            22: "MAT-TEC-03",
            23: "MAT-TEC-04",
            24: "MAT-ESP-01",
        }

        docentes_importados = 0
        matriculas_creadas = 0

        for r in range(3, sheet.max_row + 1):
            nombre_raw = sheet.cell(row=r, column=4).value
            if not nombre_raw or str(nombre_raw).strip() == '' or str(nombre_raw) == '0':
                continue

            nombre_str = str(nombre_raw).strip()
            fac_nombre = sheet.cell(row=r, column=2).value or 'General'
            tipo_contrato = sheet.cell(row=r, column=3).value or 'Tiempo Completo'
            grado_acad = sheet.cell(row=r, column=5).value or 'Licenciatura / Ingeniería'
            sexo = sheet.cell(row=r, column=6).value or 'M'

            # Facultad
            fac_obj, _ = Facultad.objects.get_or_create(
                codigo=str(fac_nombre)[:10].upper().replace(" ", "_"),
                defaults={'nombre': str(fac_nombre)}
            )

            # Split name
            parts = nombre_str.split(' ')
            if len(parts) >= 3:
                apellidos = f"{parts[0]} {parts[1]}"
                nombres = " ".join(parts[2:])
            elif len(parts) == 2:
                apellidos = parts[0]
                nombres = parts[1]
            else:
                apellidos = nombre_str
                nombres = ""

            cod_emp = f"DOC-{r:04d}"

            docente, created = Persona.objects.get_or_create(
                nombres=nombres if nombres else nombre_str,
                apellidos=apellidos if nombres else "Docente",
                defaults={
                    'codigo_empleado': cod_emp,
                    'tipo_personal': 'Docente',
                    'tipo_contrato': tipo_contrato,
                    'grado_academico': grado_acad,
                    'sexo': sexo if sexo in ['M', 'F'] else 'M',
                    'facultad': fac_obj,
                    'cargo_actual': f'Docente ({tipo_contrato})',
                }
            )
            docentes_importados += 1

            # Procesar columnas de competencias
            for col_idx, comp_cod in col_to_comp.items():
                val = sheet.cell(row=r, column=col_idx).value
                if val is None or str(val).strip() == '':
                    continue

                val_str = str(val).strip()
                estado = 'Pendiente'
                fecha_comp = None
                especialidad_txt = None

                if isinstance(val, datetime):
                    estado = 'Aprobado'
                    fecha_comp = val.date()
                elif 'en curso' in val_str.lower():
                    estado = 'En Curso'
                elif val_str != '':
                    estado = 'Aprobado'
                    especialidad_txt = val_str

                comp_inst = comp_objs.get(comp_cod)
                if comp_inst:
                    MatriculaMatrizDocente.objects.update_or_create(
                        persona=docente,
                        competencia=comp_inst,
                        defaults={
                            'estado': estado,
                            'fecha_completado': fecha_comp,
                            'nombre_curso_especialidad': especialidad_txt,
                        }
                    )
                    matriculas_creadas += 1

        self.stdout.write(self.style.SUCCESS(f"[OK] Importación finalizada: {docentes_importados} docentes procesados y {matriculas_creadas} matrículas de competencias creadas."))
