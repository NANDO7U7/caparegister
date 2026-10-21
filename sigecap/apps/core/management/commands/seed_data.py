from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from apps.catalogos.models import Facultad, AreaFormacion, TipoModalidad, Proyecto, Proveedor
from apps.personas.models import Persona
from apps.capacitaciones.models import Capacitacion, Participacion
from apps.costos.models import PresupuestoAnual, GastoCapacitacion

class Command(BaseCommand):
    help = 'Pobla la base de datos con catálogos base, personas y capacitaciones de ejemplo para SIGECAP.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Iniciando carga de datos iniciales..."))

        # 1. Facultades
        facultades_data = [
            ("FI", "Facultad de Ingeniería"),
            ("FCE", "Facultad de Ciencias Económicas"),
            ("FCS", "Facultad de Ciencias de la Salud"),
            ("FJC", "Facultad de Ciencias Jurídicas"),
            ("FHO", "Facultad de Humanidades"),
            ("UNID-ADM", "Dirección de Talento Humano y Administración"),
        ]
        fac_objs = {}
        for cod, nom in facultades_data:
            fac, _ = Facultad.objects.get_or_create(codigo=cod, defaults={'nombre': nom})
            fac_objs[cod] = fac

        # 2. Áreas Formativas
        areas_data = [
            ("EJE-PED", "Pedagogía y Didáctica Universitaria"),
            ("EJE-TEC", "Tecnología Educativa e IA"),
            ("EJE-INV", "Metodología de la Investigación Científica"),
            ("EJE-LID", "Liderazgo y Habilidades Blandas"),
            ("EJE-ADM", "Gestión y Normativa Universitaria"),
        ]
        area_objs = {}
        for cod, nom in areas_data:
            area, _ = AreaFormacion.objects.get_or_create(codigo=cod, defaults={'nombre': nom})
            area_objs[cod] = area

        # 3. Tipos y Modalidades
        tipos_data = [
            ("Taller", "Presencial"),
            ("Taller", "Virtual"),
            ("Curso", "Virtual"),
            ("Curso", "Híbrida"),
            ("Diplomado", "Híbrida"),
            ("Congreso", "Presencial"),
        ]
        tipo_objs = {}
        for t, m in tipos_data:
            tm, _ = TipoModalidad.objects.get_or_create(tipo=t, modalidad=m)
            tipo_objs[f"{t}-{m}"] = tm

        # 4. Proveedores
        prov1, _ = Proveedor.objects.get_or_create(
            codigo="PROV-01",
            defaults={'nombre': 'Instituto Tecnológico y de Innovación', 'tipo': 'Externo', 'contacto_email': 'contacto@itinnovacion.edu'}
        )
        prov2, _ = Proveedor.objects.get_or_create(
            codigo="PROV-02",
            defaults={'nombre': 'Unidad de Desarrollo Docente Interno', 'tipo': 'Interno', 'contacto_email': 'docencia@universidad.edu'}
        )

        # 5. Proyectos
        proy1, _ = Proyecto.objects.get_or_create(
            codigo="PROY-2026-FONDOS-PROPIOS",
            defaults={'nombre': 'Plan Operativo Anual de Capacitación', 'presupuesto_asignado': Decimal('500000.00')}
        )

        # 6. Presupuesto Anual
        PresupuestoAnual.objects.get_or_create(
            anio=2026,
            defaults={'monto_total_asignado': Decimal('650000.00'), 'proyecto': proy1}
        )

        # 7. Personas (Docentes y Administrativos)
        personas_data = [
            ("EMP-1001", "0801-1985-12345", "Carlos Roberto", "Mendoza Ramos", "Docente", "FI", "Ingeniería de Sistemas", "Profesor Titular", "carlos.mendoza@universidad.edu"),
            ("EMP-1002", "0801-1990-23456", "María Elena", "Santos Cruz", "Docente", "FCE", "Contaduría Pública", "Coordinadora Académica", "maria.santos@universidad.edu"),
            ("EMP-1003", "0801-1988-34567", "Jorge Alberto", "Vásquez Díaz", "Administrativo", "UNID-ADM", "Talento Humano", "Analista de Personal", "jorge.vasquez@universidad.edu"),
            ("EMP-1004", "0801-1992-45678", "Ana Lucía", "Gómez Pineda", "Docente", "FCS", "Medicina", "Docente Investigadora", "ana.gomez@universidad.edu"),
            ("EMP-1005", "0801-1983-56789", "Luis Fernando", "Hernández Silva", "Ambos", "FI", "Ingeniería Civil", "Jefe de Departamento", "luis.hernandez@universidad.edu"),
            ("EMP-1006", "0801-1995-67890", "Claudia Sofía", "Morales Meza", "Docente", "FHO", "Lenguas Extranjeras", "Docente Agregada", "claudia.morales@universidad.edu"),
        ]
        persona_objs = []
        for cod, dni, nom, ape, tip, fac_k, dep, carg, em in personas_data:
            p, _ = Persona.objects.get_or_create(
                codigo_empleado=cod,
                defaults={
                    'documento_identidad': dni,
                    'nombres': nom,
                    'apellidos': ape,
                    'tipo_personal': tip,
                    'facultad': fac_objs.get(fac_k),
                    'departamento_unidad': dep,
                    'cargo_actual': carg,
                    'email_institucional': em,
                }
            )
            persona_objs.append(p)

        # 8. Capacitaciones
        hoy = timezone.now().date()
        cap1, _ = Capacitacion.objects.get_or_create(
            codigo="CAP-2026-001",
            defaults={
                'nombre': 'Innovación Pedagógica y Metodologías Activas en el Aula',
                'descripcion': 'Taller práctico sobre aprendizaje basado en retos, flipped classroom y dinámicas colaborativas universitarias.',
                'area_formacion': area_objs["EJE-PED"],
                'tipo_modalidad': tipo_objs["Taller-Presencial"],
                'proveedor': prov2,
                'proyecto': proy1,
                'horas_duracion': 24,
                'fecha_inicio': hoy - timedelta(days=30),
                'fecha_fin': hoy - timedelta(days=26),
                'estado': 'Finalizada',
                'lugar_o_enlace': 'Auditorio 2, Edificio A',
                'cupo_maximo': 30,
            }
        )
        cap1.facultades.set([fac_objs["FI"], fac_objs["FCE"], fac_objs["FCS"]])

        cap2, _ = Capacitacion.objects.get_or_create(
            codigo="CAP-2026-002",
            defaults={
                'nombre': 'Integración de Herramientas Digitales e IA en la Docencia',
                'descripcion': 'Uso ético y efectivo de modelos de lenguaje e inteligencia artificial para preparación de material didáctico.',
                'area_formacion': area_objs["EJE-TEC"],
                'tipo_modalidad': tipo_objs["Curso-Virtual"],
                'proveedor': prov1,
                'proyecto': proy1,
                'horas_duracion': 40,
                'fecha_inicio': hoy - timedelta(days=10),
                'fecha_fin': hoy + timedelta(days=15),
                'estado': 'En Curso',
                'lugar_o_enlace': 'Campus Virtual Moodle / Microsoft Teams',
                'cupo_maximo': 45,
            }
        )
        cap2.facultades.set([fac_objs["FI"], fac_objs["FHO"]])

        cap3, _ = Capacitacion.objects.get_or_create(
            codigo="CAP-2026-003",
            defaults={
                'nombre': 'Redacción y Publicación de Artículos Científicos Scopus/WoS',
                'descripcion': 'Diplomado avanzado en estructuración de manuscritos, gestión bibliográfica y respuesta a revisores por pares.',
                'area_formacion': area_objs["EJE-INV"],
                'tipo_modalidad': tipo_objs["Diplomado-Híbrida"],
                'proveedor': prov1,
                'proyecto': proy1,
                'horas_duracion': 80,
                'fecha_inicio': hoy + timedelta(days=20),
                'fecha_fin': hoy + timedelta(days=90),
                'estado': 'Planificada',
                'lugar_o_enlace': 'Edificio de Posgrados',
                'cupo_maximo': 25,
            }
        )

        # 9. Participaciones / Inscripciones
        Participacion.objects.get_or_create(capacitacion=cap1, persona=persona_objs[0], defaults={'estado_asistencia': 'Aprobó', 'calificacion': Decimal('95.0'), 'horas_acreditadas': 24, 'certificado_emitido': True})
        Participacion.objects.get_or_create(capacitacion=cap1, persona=persona_objs[1], defaults={'estado_asistencia': 'Aprobó', 'calificacion': Decimal('88.5'), 'horas_acreditadas': 24, 'certificado_emitido': True})
        Participacion.objects.get_or_create(capacitacion=cap1, persona=persona_objs[3], defaults={'estado_asistencia': 'Aprobó', 'calificacion': Decimal('92.0'), 'horas_acreditadas': 24, 'certificado_emitido': True})
        Participacion.objects.get_or_create(capacitacion=cap1, persona=persona_objs[4], defaults={'estado_asistencia': 'Asistió', 'calificacion': Decimal('70.0'), 'horas_acreditadas': 24})

        Participacion.objects.get_or_create(capacitacion=cap2, persona=persona_objs[0], defaults={'estado_asistencia': 'Inscrito'})
        Participacion.objects.get_or_create(capacitacion=cap2, persona=persona_objs[2], defaults={'estado_asistencia': 'Inscrito'})
        Participacion.objects.get_or_create(capacitacion=cap2, persona=persona_objs[5], defaults={'estado_asistencia': 'Inscrito'})

        # 10. Gastos
        GastoCapacitacion.objects.get_or_create(
            capacitacion=cap1,
            rubro='Inscripción / Honorarios',
            defaults={'monto_planificado': Decimal('25000.00'), 'monto_ejecutado': Decimal('25000.00'), 'estado': 'Ejecutado', 'numero_comprobante': 'FACT-00921'}
        )
        GastoCapacitacion.objects.get_or_create(
            capacitacion=cap1,
            rubro='Materiales y Didácticos',
            defaults={'monto_planificado': Decimal('5000.00'), 'monto_ejecutado': Decimal('4200.00'), 'estado': 'Ejecutado', 'numero_comprobante': 'REC-1044'}
        )
        GastoCapacitacion.objects.get_or_create(
            capacitacion=cap2,
            rubro='Inscripción / Honorarios',
            defaults={'monto_planificado': Decimal('35000.00'), 'monto_ejecutado': Decimal('0.00'), 'estado': 'Planificado'}
        )

        self.stdout.write(self.style.SUCCESS("[OK] Carga de datos iniciales completada exitosamente."))
