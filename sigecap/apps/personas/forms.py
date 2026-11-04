from django import forms

from .models import Persona


class PersonaForm(forms.ModelForm):
    class Meta:
        model = Persona
        fields = (
            'codigo_empleado', 'documento_identidad', 'nombres', 'apellidos',
            'sexo', 'tipo_personal', 'tipo_contrato', 'grado_academico',
            'facultad', 'departamento_unidad', 'cargo_actual',
            'email_institucional', 'telefono', 'meta_horas_anuales',
        )
        error_messages = {
            'codigo_empleado': {'unique': 'Ya existe una persona con este código.'},
            'documento_identidad': {'unique': 'Ya existe una persona con este documento.'},
            'email_institucional': {'unique': 'Ya existe una persona con este correo.'},
        }

    def __init__(self, data=None, *args, **kwargs):
        instance = kwargs.get('instance')
        if data is not None:
            data = data.copy()
            # Conservar los valores que las vistas aceptaban omitir en el POST.
            for name in (
                'codigo_empleado', 'nombres', 'apellidos', 'tipo_personal',
                'tipo_contrato', 'grado_academico', 'sexo', 'meta_horas_anuales',
            ):
                if name not in data:
                    field = Persona._meta.get_field(name)
                    if instance is not None:
                        data[name] = getattr(instance, name)
                    elif field.has_default():
                        data[name] = field.get_default()
            if not data.get('meta_horas_anuales'):
                data['meta_horas_anuales'] = 40
        super().__init__(data, *args, **kwargs)

    def clean_documento_identidad(self):
        return self.cleaned_data['documento_identidad'] or None

    def clean_email_institucional(self):
        return self.cleaned_data['email_institucional'] or None
