import json
import re
from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.capacitaciones.models import Capacitacion, Participacion, EncuestaSatisfaccion
from apps.catalogos.models import AreaFormacion, TipoModalidad
from apps.costos.models import GastoCapacitacion
from apps.personas.models import Persona


class DashboardTests(TestCase):
    def setUp(self):
        self.client.force_login(get_user_model().objects.create_user('dashboard_reader'))
        self.year = timezone.localdate().year

    def area(self, codigo='AREA', nombre='Área real'):
        return AreaFormacion.objects.create(codigo=codigo, nombre=nombre)

    def course(self, codigo='CAP1', estado='Finalizada', mes=1, year=None, **extra):
        area = extra.pop('area_formacion', None) or AreaFormacion.objects.first() or self.area()
        tipo, _ = TipoModalidad.objects.get_or_create(tipo='Curso', modalidad='Virtual')
        return Capacitacion.objects.create(
            codigo=codigo, nombre=codigo, area_formacion=area, tipo_modalidad=tipo,
            fecha_inicio=date(year or self.year, mes, 1),
            fecha_fin=date(year or self.year, mes, 2), estado=estado,
            horas_duracion=extra.pop('horas_duracion', 8), **extra,
        )

    def person(self, codigo='P1', tipo='Docente'):
        return Persona.objects.create(codigo_empleado=codigo, nombres=codigo,
                                      apellidos='Prueba', tipo_personal=tipo)

    def survey(self, course, score):
        return EncuestaSatisfaccion.objects.create(
            capacitacion=course, claridad_facilitador=score, dominio_tema=score,
            utilidad_practica=score, materiales_recursos=score,
        )

    def chart(self, response, element):
        match = re.search(r'<script id="' + element + r'" type="application/json">(.*?)</script>',
                          response.content.decode(), flags=re.S)
        self.assertIsNotNone(match)
        return json.loads(match.group(1))

    def test_empty_database_has_no_demo_statistics(self):
        response = self.client.get('/')
        for key in ('total_capacitaciones', 'total_participantes', 'total_aprobados',
                    'total_docentes', 'total_horas', 'presupuesto_ejecutado', 'total_encuestas'):
            self.assertEqual(response.context[key], 0, key)
        self.assertIsNone(response.context['satisfaccion_promedio'])
        self.assertIsNone(response.context['pct_satisfaccion'])
        self.assertContains(response, 'Sin datos disponibles', count=3)
        self.assertNotContains(response, '<canvas')
        self.assertNotContains(response, 'CSAT')
        self.assertEqual(self.chart(response, 'dashboard-area-values'), [])
        self.assertEqual(self.chart(response, 'dashboard-trend-formaciones'), [0] * 12)
        self.assertEqual(self.chart(response, 'dashboard-trend-participaciones'), [0] * 12)

    def test_real_records_without_join_multiplication(self):
        area = self.area()
        self.area('EMPTY', 'Área sin eventos')
        a = self.course(area_formacion=area)
        b = self.course('CAP2', 'En Curso', mes=2, horas_duracion=6)
        self.course('PLAN', 'Planificada', horas_duracion=50)
        self.course('CANCEL', 'Cancelada', horas_duracion=100)
        docent = self.person()
        both = self.person('P2', 'Ambos')
        admin = self.person('P3', 'Administrativo')
        absent = self.person('P4')
        for course, person, status in ((a, docent, 'Aprobó'), (b, docent, 'Aprobó'),
                                       (a, both, 'Aprobó'), (a, admin, 'Aprobó'),
                                       (a, absent, 'Inscrito'), (b, absent, 'Asistió')):
            Participacion.objects.create(capacitacion=course, persona=person, estado_asistencia=status)
        for status, amount in (('Ejecutado', '12.34'), ('Ejecutado', '12.34'),
                               ('Planificado', '100'), ('Comprometido', '200'), ('Cancelado', '300')):
            GastoCapacitacion.objects.create(capacitacion=a, rubro='Otro', estado=status,
                                             monto_ejecutado=Decimal(amount))
        self.survey(a, 5)
        self.survey(a, 3)
        self.survey(b, 1)
        response = self.client.get('/')
        for key, expected in {'total_capacitaciones': 4, 'total_participantes': 6,
                              'total_aprobados': 4, 'total_docentes': 2, 'total_horas': 14,
                              'presupuesto_ejecutado': Decimal('24.68'), 'total_encuestas': 3,
                              'satisfaccion_promedio': 3.0, 'pct_satisfaccion': 60.0}.items():
            self.assertEqual(response.context[key], expected, key)
        self.assertEqual(self.chart(response, 'dashboard-area-values'), [4])
        self.assertEqual(self.chart(response, 'dashboard-trend-formaciones'), [1, 1] + [0] * 10)
        self.assertEqual(self.chart(response, 'dashboard-trend-participaciones'), [3, 2] + [0] * 10)
        self.assertEqual(response.context['capacitaciones_recientes'][0], b)

    def test_reload_reflects_new_records_and_status_changes(self):
        self.assertEqual(self.client.get('/').context['total_capacitaciones'], 0)
        course = self.course(estado='Planificada')
        self.assertEqual(self.client.get('/').context['total_capacitaciones'], 1)
        self.assertEqual(self.client.get('/').context['total_horas'], 0)
        course.estado = 'Finalizada'
        course.save()
        Participacion.objects.create(capacitacion=course, persona=self.person(), estado_asistencia='Aprobó')
        self.survey(course, 4)
        GastoCapacitacion.objects.create(capacitacion=course, rubro='Otro', estado='Ejecutado', monto_ejecutado=7)
        response = self.client.get('/')
        self.assertEqual(response.context['total_horas'], 8)
        self.assertEqual(response.context['total_docentes'], 1)
        self.assertEqual(response.context['satisfaccion_promedio'], 4)
        self.assertEqual(response.context['pct_satisfaccion'], 80)
        self.assertEqual(response.context['presupuesto_ejecutado'], 7)
        self.assertEqual(self.chart(response, 'dashboard-area-values'), [1])

    def test_monthly_scope_and_attendance_states(self):
        historical = self.course(year=self.year - 1)
        current = self.course('CURRENT', mes=12)
        cancelled = self.course('CANCEL', 'Cancelada')
        for i, status in enumerate(('Inscrito', 'Asistió', 'Aprobó', 'No Completó', 'Cancelado')):
            Participacion.objects.create(capacitacion=current, persona=self.person(str(i)), estado_asistencia=status)
        Participacion.objects.create(capacitacion=historical, persona=self.person('old'), estado_asistencia='Aprobó')
        Participacion.objects.create(capacitacion=cancelled, persona=self.person('cancel'), estado_asistencia='Asistió')
        response = self.client.get('/')
        self.assertEqual(self.chart(response, 'dashboard-trend-formaciones'), [0] * 11 + [1])
        self.assertEqual(self.chart(response, 'dashboard-trend-participaciones'), [0] * 11 + [2])
        self.assertEqual(response.context['total_capacitaciones'], 3)
        self.assertEqual(response.context['total_participantes'], 7)

    def test_catalogs_without_events_are_empty_and_labels_are_safe(self):
        area = self.area(nombre='Área "especial" </script><script>alert(1)</script>')
        self.assertEqual(self.client.get('/').context['area_labels'], [])
        self.course(area_formacion=area)
        response = self.client.get('/')
        self.assertEqual(self.chart(response, 'dashboard-area-labels'), [area.nombre])
        self.assertNotContains(response, '</script><script>alert(1)</script>')

    def test_anonymous_access_still_requires_login(self):
        self.client.logout()
        self.assertRedirects(self.client.get('/'), '/login/?next=/')

    def test_satisfaction_weights_responses_and_all_four_questions(self):
        a = self.course()
        b = self.course('OTHER')
        self.survey(a, 5)
        self.survey(a, 5)
        EncuestaSatisfaccion.objects.create(capacitacion=b, claridad_facilitador=1,
            dominio_tema=2, utilidad_practica=3, materiales_recursos=3)
        response = self.client.get('/')
        # (5 + 5 + 2.25) / 3, not an average of the two course averages.
        self.assertEqual(response.context['satisfaccion_promedio'], 4.1)
        self.assertEqual(response.context['pct_satisfaccion'], 81.7)

    def test_recent_list_limits_to_six_and_prioritizes_in_progress(self):
        for month in range(2, 10):
            self.course(str(month), mes=month)
        ongoing = self.course('ONGOING', 'En Curso', mes=1)
        recent = list(self.client.get('/').context['capacitaciones_recientes'])
        self.assertEqual(len(recent), 6)
        self.assertEqual(recent[0], ongoing)
        self.assertEqual([course.codigo for course in recent[1:]], ['9', '8', '7', '6', '5'])
