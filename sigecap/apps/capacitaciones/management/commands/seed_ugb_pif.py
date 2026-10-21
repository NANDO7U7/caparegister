from django.core.management.base import BaseCommand
from decimal import Decimal
from datetime import date
from django.utils import timezone
from apps.catalogos.models import Facultad, AreaFormacion, TipoModalidad, Proyecto, Proveedor
from apps.personas.models import Persona
from apps.capacitaciones.models import Capacitacion, Participacion
from apps.costos.models import GastoCapacitacion, PresupuestoAnual

class Command(BaseCommand):
    help = 'Carga los catalogos institucionales UGB PIF y los registros semilla iniciales en PostgreSQL.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Iniciando carga de datos institucionales UGB · PIF..."))

        # 1. Facultades y Unidades UGB
        facultades = [
            ("FCT", "Facultad de Ciencia y Tecnología"),
            ("FIA", "Facultad de Ingeniería y Arquitectura"),
            ("FCH", "Facultad de Ciencias y Humanidades"),
            ("FCS", "Facultad de Ciencias de la Salud"),
            ("FDRI", "Facultad de Derecho y Relaciones Internacionales"),
            ("FCE", "Facultad de Ciencias Empresariales"),
            ("UEV", "Unidad de Educación Virtual"),
        ]
        fac_map = {}
        for cod, nom in facultades:
            fac, _ = Facultad.objects.get_or_create(codigo=cod, defaults={'nombre': nom, 'activo': True})
            fac_map[nom] = fac
            fac_map[cod] = fac

        # 2. Áreas PIF
        areas = [
            ("PIF-ESP", "Especialidad"),
            ("PIF-PED", "Pedagogía"),
            ("PIF-BAS", "Básica institucional"),
            ("PIF-INV", "Investigación"),
            ("PIF-INT", "Integral"),
            ("PIF-TEC", "Virtualidad y Herramientas Tecnológicas"),
            ("PIF-EXT", "Nivel internacional"),
        ]
        area_map = {}
        for cod, nom in areas:
            a, _ = AreaFormacion.objects.get_or_create(codigo=cod, defaults={'nombre': nom, 'activo': True})
            area_map[nom] = a

        # 3. Proyectos
        proyectos = [
            ("IGA004", "Innovación y Gestión Académica - Especialidad y Pedagogía", Decimal('2500.00')),
            ("IGA005", "Innovación y Gestión Académica - Enfoque Socioformativo", Decimal('1500.00')),
            ("FOR002", "Plan Integral de Formación Docente (Hoja Presupuesto)", Decimal('2000.00')),
        ]
        proy_map = {}
        for cod, nom, presup in proyectos:
            p, _ = Proyecto.objects.get_or_create(codigo=cod, defaults={'nombre': nom, 'presupuesto_asignado': presup, 'activo': True})
            p.presupuesto_asignado = presup
            p.save()
            proy_map[cod] = p
            # Presupuesto Anual
            PresupuestoAnual.objects.get_or_create(anio=2026, proyecto=p, defaults={'monto_total_asignado': presup})

        # 4. Tipos y Modalidades
        tipos = ['Taller', 'Curso', 'Seminario', 'Diplomado', 'Congreso', 'Conferencia / Seminario', 'Certificación', 'Otro']
        modalidades = ['Virtual', 'Presencial', 'Híbrida']
        tm_map = {}
        for t in tipos:
            for m in modalidades:
                tm, _ = TipoModalidad.objects.get_or_create(tipo=t, modalidad=m, defaults={'activo': True})
                tm_map[(t, m)] = tm

        # 5. Proveedores
        prov1, _ = Proveedor.objects.get_or_create(
            nombre="Ing. Carlos Roberto Martínez",
            defaults={'tipo': 'Externo', 'contacto_nombre': 'Ing. Carlos Roberto Martínez', 'pais': 'Nacional', 'codigo': 'PROV-CRM'}
        )
        prov2, _ = Proveedor.objects.get_or_create(
            nombre="Innovación y Gestión Académica - UGB",
            defaults={'tipo': 'Interno', 'contacto_nombre': 'Dirección IGA', 'pais': 'Nacional', 'codigo': 'PROV-IGA'}
        )
        prov3, _ = Proveedor.objects.get_or_create(
            nombre="Exequatur",
            defaults={'tipo': 'Externo', 'contacto_nombre': 'José Roberto Batista', 'pais': 'Nacional', 'codigo': 'PROV-EXEQ'}
        )

        # 6. Personas iniciales (Docente 1, Docente 2, Docente 3, Docente 4)
        docentes_data = [
            ("DOC-001", "Docente", "1", "Docente tiempo completo", "Facultad de Ciencia y Tecnología"),
            ("DOC-002", "Docente", "2", "Docente tiempo completo", "Facultad de Ciencia y Tecnología"),
            ("DOC-003", "Docente", "3", "Docente horas clase", "Facultad de Ciencia y Tecnología"),
            ("DOC-004", "Docente", "4", "Docente tiempo completo", "Facultad de Derecho y Relaciones Internacionales"),
        ]
        docente_map = {}
        for cod, nom, ape, cargo, fac_nom in docentes_data:
            p, _ = Persona.objects.get_or_create(
                codigo_empleado=cod,
                defaults={
                    'nombres': nom,
                    'apellidos': ape,
                    'cargo_actual': cargo,
                    'facultad': fac_map.get(fac_nom),
                    'tipo_personal': 'Docente'
                }
            )
            docente_map[f"{nom} {ape}"] = p

        # 7. Capacitaciones Semilla
        # Evento 1
        c1, created = Capacitacion.objects.get_or_create(
            codigo="CAP-2024-001",
            defaults={
                'nombre': "Taller de Blockchain para docentes",
                'area_formacion': area_map['Especialidad'],
                'tipo_modalidad': tm_map.get(('Taller', 'Virtual')),
                'proveedor': prov1,
                'proyecto': proy_map['IGA004'],
                'horas_duracion': 24,
                'fecha_inicio': date(2024, 12, 16),
                'fecha_fin': date(2024, 12, 16),
                'estado': 'Finalizada',
                'lugar_o_enlace': 'Plataforma Zoom',
                'cupo_maximo': 30,
                'observaciones': 'Horario: 8:00 AM a 12:00 PM'
            }
        )
        if created:
            c1.facultades.add(fac_map["Facultad de Ciencia y Tecnología"])
            for d_name, puesto in [("Docente 1", "Vicedecanatura"), ("Docente 2", "Docente tiempo completo"), ("Docente 3", "Docente horas clase")]:
                p = docente_map.get(d_name)
                if p:
                    Participacion.objects.get_or_create(capacitacion=c1, persona=p, defaults={'estado_asistencia': 'Aprobó', 'horas_acreditadas': 24})
            GastoCapacitacion.objects.create(
                capacitacion=c1, rubro='Inscripción / Honorarios', monto_planificado=Decimal('100.00'),
                monto_ejecutado=Decimal('200.00'), estado='Ejecutado'
            )

        # Evento 2
        c2, created = Capacitacion.objects.get_or_create(
            codigo="CAP-2024-002",
            defaults={
                'nombre': "Construcción de Competencias, Planeación y Evaluación en Educación Superior, desde el Enfoque Socioformativo",
                'area_formacion': area_map['Pedagogía'],
                'tipo_modalidad': tm_map.get(('Curso', 'Virtual')),
                'proveedor': prov2,
                'proyecto': proy_map['IGA005'],
                'horas_duracion': 40,
                'fecha_inicio': date(2024, 5, 13),
                'fecha_fin': date(2024, 5, 13),
                'estado': 'Finalizada',
                'lugar_o_enlace': 'Canvas y Zoom',
                'cupo_maximo': 35,
                'observaciones': 'Sesiones sincrónicas Martes 6:00 pm a 7:30 pm'
            }
        )
        if created:
            c2.facultades.add(fac_map["Facultad de Ciencias y Humanidades"], fac_map["Facultad de Ciencias de la Salud"])
            p = docente_map.get("Docente 1")
            if p:
                Participacion.objects.get_or_create(capacitacion=c2, persona=p, defaults={'estado_asistencia': 'Aprobó', 'horas_acreditadas': 40})
            GastoCapacitacion.objects.create(
                capacitacion=c2, rubro='Otro', monto_planificado=Decimal('250.00'),
                monto_ejecutado=Decimal('250.00'), estado='Ejecutado', descripcion='Costo publicado institucional'
            )

        # Evento 3
        c3, created = Capacitacion.objects.get_or_create(
            codigo="CAP-2024-003",
            defaults={
                'nombre': "Construcción de Competencias, Planeación y Evaluación en Educación Superior, desde el Enfoque Socioformativo (Grupo General)",
                'area_formacion': area_map['Pedagogía'],
                'tipo_modalidad': tm_map.get(('Curso', 'Virtual')),
                'proveedor': prov2,
                'proyecto': proy_map['IGA004'],
                'horas_duracion': 40,
                'fecha_inicio': date(2024, 5, 13),
                'fecha_fin': date(2024, 5, 13),
                'estado': 'Finalizada',
                'lugar_o_enlace': 'Canvas y Zoom',
                'cupo_maximo': 50,
                'observaciones': 'Sesiones sincrónicas Martes 6:00 pm a 7:30 pm'
            }
        )
        if created:
            for fac in [fac_map["Facultad de Ciencias y Humanidades"], fac_map["Facultad de Ciencias de la Salud"], fac_map["Facultad de Derecho y Relaciones Internacionales"], fac_map["Facultad de Ingeniería y Arquitectura"], fac_map["Unidad de Educación Virtual"], fac_map["Facultad de Ciencias Empresariales"], fac_map["Facultad de Ciencia y Tecnología"]]:
                c3.facultades.add(fac)
            for d_name in ["Docente 1", "Docente 2", "Docente 3"]:
                p = docente_map.get(d_name)
                if p:
                    Participacion.objects.get_or_create(capacitacion=c3, persona=p, defaults={'estado_asistencia': 'Aprobó', 'horas_acreditadas': 40})
            GastoCapacitacion.objects.create(
                capacitacion=c3, rubro='Otro', monto_planificado=Decimal('1000.00'),
                monto_ejecutado=Decimal('1000.00'), estado='Ejecutado', descripcion='Costo publicado institucional'
            )

        # Evento 4
        c4, created = Capacitacion.objects.get_or_create(
            codigo="CAP-2024-004",
            defaults={
                'nombre': "La presidencia y sistemas de ordenación protocolaria",
                'area_formacion': area_map['Especialidad'],
                'tipo_modalidad': tm_map.get(('Seminario', 'Presencial')) or tm_map.get(('Conferencia / Seminario', 'Presencial')),
                'proveedor': prov3,
                'proyecto': proy_map['IGA004'],
                'horas_duracion': 8,
                'fecha_inicio': date(2024, 8, 28),
                'fecha_fin': date(2024, 8, 28),
                'estado': 'Finalizada',
                'lugar_o_enlace': 'Delibanquetes, San Salvador',
                'cupo_maximo': 20,
                'observaciones': 'Horario: 8:00 AM a 5:00 PM'
            }
        )
        if created:
            c4.facultades.add(fac_map["Facultad de Derecho y Relaciones Internacionales"])
            p = docente_map.get("Docente 4")
            if p:
                Participacion.objects.get_or_create(capacitacion=c4, persona=p, defaults={'estado_asistencia': 'Aprobó', 'horas_acreditadas': 8})
            GastoCapacitacion.objects.create(capacitacion=c4, rubro='Inscripción / Honorarios', monto_planificado=Decimal('150.00'), monto_ejecutado=Decimal('169.50'), estado='Ejecutado')
            GastoCapacitacion.objects.create(capacitacion=c4, rubro='Alimentación / Coffee Break', monto_planificado=Decimal('0.00'), monto_ejecutado=Decimal('6.00'), estado='Ejecutado')
            GastoCapacitacion.objects.create(capacitacion=c4, rubro='Transporte / Pasajes', monto_planificado=Decimal('0.00'), monto_ejecutado=Decimal('37.84'), estado='Ejecutado')

        self.stdout.write(self.style.SUCCESS("¡Datos institucionales UGB · PIF cargados exitosamente en PostgreSQL!"))
