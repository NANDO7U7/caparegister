from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

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
