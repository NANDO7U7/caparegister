from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
import time

from django.contrib.auth.models import User
from django.core import signing
from django.db import IntegrityError, close_old_connections
from django.test import TestCase, TransactionTestCase, override_settings
from django.urls import reverse

from apps.catalogos.models import Facultad

from .forms import PersonaForm
from .models import Persona
from .registro import registrar_persona, siguiente_codigo


class CodigosPersonaTests(TestCase):
    def setUp(self):
        self.client.force_login(User.objects.create_superuser(username='codigos_admin'))
        self.data = {'nombres': 'Ana', 'apellidos': 'Perez', 'tipo_personal': 'Administrativo'}

    def test_creacion_consecutiva(self):
        for codigo in ('EMP-0001', 'EMP-0002', 'EMP-0003'):
            response = self.client.post(reverse('personas:crear'), self.data)
            self.assertEqual(response.status_code, 302)
            self.assertTrue(Persona.objects.filter(codigo_empleado=codigo).exists())

    def test_huecos_y_codigo_numerico_manual(self):
        for codigo in ('EMP-0001', 'EMP-0003', 'EMP-0010', 'MANUAL-ABC'):
            Persona.objects.create(codigo_empleado=codigo, nombres='Existente', apellidos='Perez')
        self.assertEqual(siguiente_codigo(), 'EMP-0011')
        self.client.post(reverse('personas:crear'), self.data)
        self.assertEqual(Persona.objects.count(), 5)
        self.assertTrue(Persona.objects.filter(codigo_empleado='EMP-0011').exists())

    def test_codigo_manual_se_conserva_y_duplicado_se_rechaza(self):
        data = {**self.data, 'codigo_empleado': 'EMP-0042'}
        self.assertEqual(self.client.post(reverse('personas:crear'), data).status_code, 302)
        response = self.client.post(reverse('personas:crear'), data)
        self.assertIn('codigo_empleado', response.context['form'].errors)
        self.assertEqual(Persona.objects.get().codigo_empleado, 'EMP-0042')

    def test_eliminacion_no_provoca_colision(self):
        for codigo in ('EMP-0001', 'EMP-0002', 'EMP-0003'):
            Persona.objects.create(codigo_empleado=codigo, nombres='Ana', apellidos='Perez')
        Persona.objects.get(codigo_empleado='EMP-0002').delete()
        response = self.client.post(reverse('personas:crear'), self.data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Persona.objects.filter(codigo_empleado='EMP-0004').exists())

    def test_reintenta_integrity_error_automatico(self):
        guardar = PersonaForm.save
        intentos = []

        def guardar_con_conflicto(form):
            intentos.append(True)
            if len(intentos) == 1:
                raise IntegrityError('conflicto simulado')
            return guardar(form)

        with patch.object(PersonaForm, 'save', guardar_con_conflicto):
            response = self.client.post(reverse('personas:crear'), self.data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(intentos), 2)
        self.assertEqual(Persona.objects.count(), 1)

    def test_sugerencia_desactualizada(self):
        response = self.client.get(reverse('personas:crear'))
        codigo = response.context['form']['codigo_empleado'].value()
        token = response.context['codigo_sugerido']
        Persona.objects.create(codigo_empleado=codigo, nombres='Otra', apellidos='Persona')
        response = self.client.post(reverse('personas:crear'), {
            **self.data, 'codigo_empleado': codigo, 'codigo_sugerido': token,
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(set(Persona.objects.values_list('codigo_empleado', flat=True)),
                         {'EMP-0001', 'EMP-0002'})

    def test_token_alterado_no_reemplaza_codigo_manual(self):
        Persona.objects.create(codigo_empleado='EMP-0001', nombres='Otra', apellidos='Persona')
        response = self.client.post(reverse('personas:crear'), {
            **self.data, 'codigo_empleado': 'EMP-0001', 'codigo_sugerido': 'alterado',
        })
        self.assertIn('codigo_empleado', response.context['form'].errors)
        self.assertEqual(Persona.objects.count(), 1)

    def test_error_conserva_identificacion_automatica_para_reintento(self):
        token = signing.dumps('EMP-0001', salt='personas.codigo')
        response = self.client.post(reverse('personas:crear'), {
            **self.data, 'nombres': '', 'codigo_empleado': 'EMP-0001',
            'codigo_sugerido': token,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(signing.loads(response.context['codigo_sugerido'], salt='personas.codigo'),
                         response.context['form']['codigo_empleado'].value())


class FirmasCodigoTests(TestCase):
    def setUp(self):
        self.client.force_login(User.objects.create_superuser(username='firmas_admin'))
        self.data = {'nombres': 'Ana', 'apellidos': 'Perez',
                     'tipo_personal': 'Administrativo', 'codigo_empleado': 'EMP-0001'}

    def test_manual_igual_a_sugerencia_no_emite_firma_tras_error(self):
        response = self.client.post(reverse('personas:crear'), {
            **self.data, 'nombres': '', 'modo_codigo': 'manual',
            'codigo_sugerido': signing.dumps('EMP-0001', salt='personas.codigo'),
        })
        self.assertEqual(response.context['modo_codigo'], 'manual')
        self.assertEqual(response.context['codigo_sugerido'], '')
        self.assertNotContains(response, 'name="codigo_sugerido"')
        Persona.objects.create(codigo_empleado='EMP-0001', nombres='Otra', apellidos='Persona')
        response = self.client.post(reverse('personas:crear'), {
            **self.data, 'modo_codigo': 'manual',
        })
        self.assertIn('codigo_empleado', response.context['form'].errors)
        self.assertEqual(response.context['form']['codigo_empleado'].value(), 'EMP-0001')
        self.assertEqual(Persona.objects.count(), 1)

    def test_manual_sin_modo_conserva_codigo_tras_error(self):
        response = self.client.post(reverse('personas:crear'), {**self.data, 'nombres': ''})
        self.assertEqual(response.context['modo_codigo'], 'manual')
        self.assertEqual(response.context['codigo_sugerido'], '')
        response = self.client.post(reverse('personas:crear'), self.data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Persona.objects.get().codigo_empleado, 'EMP-0001')

    def test_manual_ignora_firma_manipulada(self):
        response = self.client.post(reverse('personas:crear'), {
            **self.data, 'modo_codigo': 'manual', 'codigo_sugerido': 'alterada',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Persona.objects.get().codigo_empleado, 'EMP-0001')

    def test_automatica_valida(self):
        response = self.client.get(reverse('personas:crear'))
        response = self.client.post(reverse('personas:crear'), {
            **self.data, 'modo_codigo': 'automatico',
            'codigo_sugerido': response.context['codigo_sugerido'],
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Persona.objects.get().codigo_empleado, 'EMP-0001')

    @override_settings(PERSONAS_CODIGO_MAX_AGE=60)
    def test_vencida_manipulada_y_ausente_conservan_datos(self):
        with patch('django.core.signing.time.time', return_value=time.time() - 120):
            vencida = signing.dumps('EMP-0001', salt='personas.codigo')
        for token in (vencida, 'manipulada', ''):
            with self.subTest(token=token):
                response = self.client.post(reverse('personas:crear'), {
                    **self.data, 'modo_codigo': 'automatico', 'codigo_sugerido': token,
                })
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.context['form'].non_field_errors())
                self.assertEqual(response.context['form']['nombres'].value(), 'Ana')
                self.assertEqual(response.context['form']['codigo_empleado'].value(), 'EMP-0001')
                self.assertEqual(Persona.objects.count(), 0)
                renovada = response.context['codigo_sugerido']
                self.assertEqual(signing.loads(renovada, salt='personas.codigo', max_age=60), 'EMP-0001')
                response = self.client.post(reverse('personas:crear'), {
                    **self.data, 'modo_codigo': 'automatico', 'codigo_sugerido': renovada,
                })
                self.assertEqual(response.status_code, 302)
                Persona.objects.all().delete()


class ConcurrenciaCodigosTests(TransactionTestCase):
    def test_dos_creaciones_simultaneas(self):
        barrera = Barrier(2)
        generar = siguiente_codigo

        def crear(indice):
            close_old_connections()
            try:
                form, persona = registrar_persona({
                    'nombres': str(indice), 'apellidos': 'Perez',
                    'tipo_personal': 'Administrativo',
                }, True)
                return persona.codigo_empleado if persona else str(form.errors)
            finally:
                close_old_connections()

        import threading
        local = threading.local()

        def candidato_con_barrera():
            codigo = generar()
            if not getattr(local, 'leyo', False):
                local.leyo = True
                barrera.wait(timeout=10)
            return codigo

        with patch('apps.personas.registro.siguiente_codigo', candidato_con_barrera):
            with ThreadPoolExecutor(max_workers=2) as executor:
                codigos = list(executor.map(crear, range(2)))
        self.assertEqual(set(codigos), {'EMP-0001', 'EMP-0002'})
        self.assertEqual(Persona.objects.count(), 2)


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
