import uuid
from datetime import datetime
from django.db import models
from django.utils import timezone
from apps.catalogos.models import Facultad

class Persona(models.Model):
    """
    Padrón único institucional de participantes (Docentes y Personal Administrativo).
    Garantiza trazabilidad y acumulación histórica de capacitaciones cursadas.
    """
    TIPO_PERSONAL = [
        ('Docente', 'Docente'),
        ('Administrativo', 'Administrativo'),
        ('Ambos', 'Docente y Administrativo'),
    ]

    TIPO_CONTRATO = [
        ('Tiempo Completo', 'Tiempo Completo'),
        ('Medio Tiempo', 'Medio Tiempo'),
        ('Hora Clase', 'Hora Clase'),
    ]

    GRADO_ACADEMICO = [
        ('Licenciatura / Ingeniería', 'Licenciatura / Ingeniería'),
        ('Especialidad', 'Especialidad'),
        ('Maestría', 'Maestría'),
        ('Doctorado', 'Doctorado'),
    ]

    SEXO = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo_empleado = models.CharField(max_length=50, unique=True, verbose_name="Código de Empleado")
    documento_identidad = models.CharField(max_length=50, unique=True, blank=True, null=True, verbose_name="DNI / Identidad")
    nombres = models.CharField(max_length=100, verbose_name="Nombres")
    apellidos = models.CharField(max_length=100, verbose_name="Apellidos")
    tipo_personal = models.CharField(max_length=20, choices=TIPO_PERSONAL, default='Docente', verbose_name="Tipo de Personal")
    tipo_contrato = models.CharField(max_length=30, choices=TIPO_CONTRATO, default='Tiempo Completo', verbose_name="Tipo de Contrato")
    grado_academico = models.CharField(max_length=50, choices=GRADO_ACADEMICO, default='Licenciatura / Ingeniería', verbose_name="Último Grado Académico")
    sexo = models.CharField(max_length=5, choices=SEXO, default='M', verbose_name="Sexo")
    
    meta_horas_anuales = models.PositiveIntegerField(default=40, verbose_name="Meta de Horas Anuales (Mínimo Institucional)")

    facultad = models.ForeignKey(
        Facultad, 
        on_delete=models.RESTRICT, 
        related_name='personal',
        null=True, 
        blank=True,
        verbose_name="Facultad / Unidad de Adscripción"
    )
    departamento_unidad = models.CharField(max_length=150, blank=True, null=True, verbose_name="Departamento / Área")
    cargo_actual = models.CharField(max_length=150, blank=True, null=True, verbose_name="Cargo o Puesto Actual")
    email_institucional = models.EmailField(max_length=150, unique=True, blank=True, null=True, verbose_name="Correo Electrónico Institucional")
    telefono = models.CharField(max_length=50, blank=True, null=True, verbose_name="Teléfono / Extensión")
    
    activo = models.BooleanField(default=True, verbose_name="Estado Activo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'personas'
        verbose_name = 'Persona / Participante'
        verbose_name_plural = 'Padrón de Personal (Docente y Administrativo)'
        ordering = ['apellidos', 'nombres']

    @property
    def nombre_completo(self):
        return f"{self.nombres} {self.apellidos}"

    @property
    def horas_anio_actual(self):
        """Calcula las horas aprobadas en el año en curso."""
        anio_actual = timezone.now().year
        total = self.participaciones.filter(
            estado_asistencia='Aprobó',
            capacitacion__fecha_inicio__year=anio_actual
        ).aggregate(total=models.Sum('horas_acreditadas'))['total'] or 0
        return total

    @property
    def porcentaje_meta_anual(self):
        """Porcentaje alcanzado respecto a la meta institucional de horas anuales."""
        if not self.meta_horas_anuales or self.meta_horas_anuales == 0:
            return 100
        pct = int((self.horas_anio_actual / self.meta_horas_anuales) * 100)
        return min(pct, 100)

    @property
    def total_horas_historicas(self):
        """Total histórico acumulado de todas las capacitaciones aprobadas."""
        total = self.participaciones.filter(
            estado_asistencia='Aprobó'
        ).aggregate(total=models.Sum('horas_acreditadas'))['total'] or 0
        return total

    def __str__(self):
        return f"{self.nombre_completo} ({self.codigo_empleado}) - {self.tipo_personal}"


class CompetenciaMatriz(models.Model):
    """
    Cursos y competencias predefinidas en el Plan Integral de Formación Docente
    (Extraído de la Matriz Institucional de Excel).
    """
    CATEGORIAS = [
        ('Formación Académica', 'Formación Académica'),
        ('Formación Pedagógica', 'Formación Pedagógica'),
        ('Formación en Investigación', 'Formación en Investigación'),
        ('Formación Integral', 'Formación Integral'),
        ('Formación en Virtualidad y Herramientas Tecnológicas', 'Formación en Virtualidad y Tecnología'),
        ('Formación en el Área de Especialidad', 'Formación en Especialidad'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo = models.CharField(max_length=50, unique=True, verbose_name="Código de Competencia/Curso")
    nombre = models.CharField(max_length=250, verbose_name="Nombre del Curso / Competencia")
    categoria = models.CharField(max_length=70, choices=CATEGORIAS, verbose_name="Categoría Formativa")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    orden = models.PositiveIntegerField(default=1, verbose_name="Orden en la Matriz")
    activo = models.BooleanField(default=True, verbose_name="Activo")

    class Meta:
        db_table = 'competencias_matriz'
        verbose_name = 'Competencia de Matriz Docente'
        verbose_name_plural = 'Competencias de Matriz Docente'
        ordering = ['categoria', 'orden', 'nombre']

    def __str__(self):
        return f"[{self.categoria}] {self.nombre}"


class MatriculaMatrizDocente(models.Model):
    """
    Registro individual de avance / matrícula de un docente en cada competencia del Plan Integral.
    """
    ESTADOS = [
        ('Aprobado', 'Aprobado / Completado'),
        ('En Curso', 'En Curso'),
        ('Pendiente', 'Pendiente / No Cursado'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    persona = models.ForeignKey(
        Persona, 
        on_delete=models.CASCADE, 
        related_name='matriculas_matriz',
        verbose_name="Docente"
    )
    competencia = models.ForeignKey(
        CompetenciaMatriz, 
        on_delete=models.CASCADE, 
        related_name='matriculas',
        verbose_name="Curso / Competencia de la Matriz"
    )
    estado = models.CharField(
        max_length=20, 
        choices=ESTADOS, 
        default='Pendiente',
        verbose_name="Estado de Matrícula / Avance"
    )
    fecha_completado = models.DateField(
        null=True, 
        blank=True, 
        verbose_name="Fecha de Finalización / Título / Certificado"
    )
    nombre_curso_especialidad = models.CharField(
        max_length=250, 
        blank=True, 
        null=True, 
        verbose_name="Nombre de Curso/Diplomado (si es Especialidad)"
    )
    observaciones = models.TextField(
        blank=True, 
        null=True, 
        verbose_name="Comentarios / Institución Emisora"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'matriculas_matriz_docente'
        verbose_name = 'Matrícula en Matriz Docente'
        verbose_name_plural = 'Matrículas en Matriz Docente'
        unique_together = ('persona', 'competencia')
        ordering = ['persona', 'competencia__orden']

    def __str__(self):
        return f"{self.persona.nombre_completo} - {self.competencia.nombre}: {self.estado}"
