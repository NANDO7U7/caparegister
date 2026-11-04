from unittest.mock import patch

from django.contrib.auth.models import User
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse

from apps.catalogos.models import Facultad

from .forms import PersonaForm
from .models import Persona


class MetaHorasAnualesTests(TestCase):
    def setUp(self):
        usuario = User.objects.create_superuser(
            username='admin_pruebas', password='solo-pruebas'
        )
        self.client.force_login(usuario)

    def test_editar_otro_campo_conserva_meta_existente(self):
        persona = Persona.objects.create(
            codigo_empleado='EMP-TEST-80',
            nombres='Ana',
            apellidos='Perez',
            meta_horas_anuales=80,
        )

        response = self.client.post(
            reverse('personas:editar', args=[persona.pk]),
            {'nombres': 'Ana Maria'},
        )

        self.assertRedirects(
            response,
            reverse('personas:ficha', args=[persona.pk]),
            fetch_redirect_response=False,
        )
        persona.refresh_from_db()
        self.assertEqual(persona.nombres, 'Ana Maria')
        self.assertEqual(persona.meta_horas_anuales, 80)

    def test_crear_sin_meta_utiliza_cuarenta(self):
        response = self.client.post(
            reverse('personas:crear'),
            {
                'codigo_empleado': 'EMP-TEST-40',
                'nombres': 'Luis',
                'apellidos': 'Perez',
                'tipo_personal': 'Administrativo',
            },
        )

        persona = Persona.objects.get(codigo_empleado='EMP-TEST-40')
        self.assertRedirects(
            response,
            reverse('personas:ficha', args=[persona.pk]),
            fetch_redirect_response=False,
        )
        self.assertEqual(persona.meta_horas_anuales, 40)


    def test_modelo_nuevo_utiliza_cuarenta_por_defecto(self):
        persona = Persona.objects.create(
            codigo_empleado='EMP-TEST-DEFAULT',
            nombres='Maria',
            apellidos='Perez',
        )

        persona.refresh_from_db()
        self.assertEqual(persona.meta_horas_anuales, 40)

class PersonaFormularioTests(TestCase):
    def setUp(self):
        self.client.force_login(User.objects.create_superuser(username='test_admin'))
        self.facultad = Facultad.objects.create(codigo='TEST', nombre='Facultad Test')
        self.persona = Persona.objects.create(
            codigo_empleado='EMP-EXISTENTE', nombres='Ana', apellidos='Perez',
            documento_identidad='DOC-EXISTENTE',
            email_institucional='ana@example.com', meta_horas_anuales=80,
        )
        self.data = {
            'codigo_empleado': 'EMP-NUEVO', 'documento_identidad': 'DOC-NUEVO',
            'nombres': 'Luis', 'apellidos': 'Lopez',
            'email_institucional': 'luis@example.com', 'sexo': 'F',
            'tipo_personal': 'Administrativo', 'tipo_contrato': 'Medio Tiempo',
            'grado_academico': 'Doctorado', 'facultad': str(self.facultad.pk),
            'departamento_unidad': 'Escuela', 'cargo_actual': 'Analista',
            'telefono': '12345678',
        }

    def test_creacion_valida(self):
        response = self.client.post(reverse('personas:crear'), self.data)
        self.assertEqual(response.status_code, 302)
        nueva = Persona.objects.get(codigo_empleado='EMP-NUEVO')
        self.assertEqual(nueva.facultad_id, self.facultad.pk)
        self.assertEqual(nueva.email_institucional, 'luis@example.com')
        self.assertEqual(nueva.meta_horas_anuales, 40)

    def test_duplicados_en_alta_conservan_textos_y_selecciones(self):
        for field in ('codigo_empleado', 'documento_identidad', 'email_institucional'):
            with self.subTest(field=field):
                data = {**self.data, field: getattr(self.persona, field)}
                response = self.client.post(reverse('personas:crear'), data)
                self.assertEqual(response.status_code, 200)
                form = response.context['form']
                self.assertEqual(form.errors.as_data()[field][0].code, 'unique')
                for name, value in data.items():
                    self.assertEqual(form[name].value(), value)
                self.assertContains(response, 'value="Luis"')
                self.assertContains(response, 'value="Doctorado" selected')
                self.assertContains(response, f'value="{self.facultad.pk}" selected')
                self.assertEqual(Persona.objects.count(), 1)

    def test_editar_con_identificadores_propios(self):
        data = {**self.data, **{
            field: getattr(self.persona, field)
            for field in ('codigo_empleado', 'documento_identidad', 'email_institucional')
        }}
        response = self.client.post(
            reverse('personas:editar', args=[self.persona.pk]), data,
        )
        self.assertEqual(response.status_code, 302)
        self.persona.refresh_from_db()
        self.assertEqual(self.persona.nombres, 'Luis')
        self.assertEqual(self.persona.meta_horas_anuales, 80)

    def test_duplicados_en_edicion_no_modifican_registros(self):
        otra = Persona.objects.create(
            codigo_empleado='EMP-OTRA', documento_identidad='DOC-OTRA',
            email_institucional='otra@example.com', nombres='Otra', apellidos='Persona',
        )
        for field in ('codigo_empleado', 'documento_identidad', 'email_institucional'):
            with self.subTest(field=field):
                data = {**self.data, **{
                    name: getattr(self.persona, name)
                    for name in ('codigo_empleado', 'documento_identidad', 'email_institucional')
                }, field: getattr(otra, field)}
                response = self.client.post(
                    reverse('personas:editar', args=[self.persona.pk]), data,
                )
                self.assertIn(field, response.context['form'].errors)
                self.assertContains(response, 'value="Luis"')
                self.persona.refresh_from_db()
                otra.refresh_from_db()
                self.assertEqual(self.persona.nombres, 'Ana')
                self.assertEqual(self.persona.meta_horas_anuales, 80)
                self.assertEqual(otra.nombres, 'Otra')

    def test_documento_y_correo_vacios_permiten_multiples_personas(self):
        for codigo in ('EMP-VACIO-1', 'EMP-VACIO-2'):
            response = self.client.post(reverse('personas:crear'), {
                **self.data, 'codigo_empleado': codigo,
                'documento_identidad': '', 'email_institucional': '',
            })
            self.assertEqual(response.status_code, 302)
            persona = Persona.objects.get(codigo_empleado=codigo)
            self.assertIsNone(persona.documento_identidad)
            self.assertIsNone(persona.email_institucional)

    def test_conflicto_concurrente_muestra_error_seguro_y_conserva_valores(self):
        for url in (reverse('personas:crear'), reverse('personas:editar', args=[self.persona.pk])):
            with self.subTest(url=url):
                original_save = PersonaForm.save

                def guardar_y_fallar(form):
                    original_save(form)
                    raise IntegrityError('DETALLE SQL PRIVADO')

                with patch.object(PersonaForm, 'save', guardar_y_fallar):
                    response = self.client.post(url, self.data)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'existe un conflicto con otro registro')
                self.assertNotContains(response, 'DETALLE SQL PRIVADO')
                self.assertContains(response, 'value="Luis"')
                self.assertEqual(Persona.objects.count(), 1)
                self.persona.refresh_from_db()
                self.assertEqual(self.persona.nombres, 'Ana')
                self.assertEqual(self.persona.meta_horas_anuales, 80)
