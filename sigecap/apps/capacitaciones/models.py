import uuid
from django.db import models
from apps.catalogos.models import Facultad, AreaFormacion, TipoModalidad, Proyecto, Proveedor
from apps.personas.models import Persona

class Capacitacion(models.Model):
    """
    Registro central de eventos de capacitación formativa (talleres, cursos, diplomados, etc.)
    """
    ESTADOS = [
        ('Planificada', 'Planificada'),
        ('En Curso', 'En Curso'),
        ('Finalizada', 'Finalizada'),
        ('Cancelada', 'Cancelada'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo = models.CharField(max_length=50, unique=True, verbose_name="Código del Evento (ej. CAP-2026-001)")
    nombre = models.CharField(max_length=250, verbose_name="Nombre de la Capacitación")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Objetivo y Descripción")
    
    area_formacion = models.ForeignKey(
        AreaFormacion, 
        on_delete=models.RESTRICT, 
        related_name='capacitaciones',
        verbose_name="Área de Formación"
    )
    tipo_modalidad = models.ForeignKey(
        TipoModalidad, 
        on_delete=models.RESTRICT, 
        related_name='capacitaciones',
        verbose_name="Tipo y Modalidad"
    )
    proveedor = models.ForeignKey(
        Proveedor, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='capacitaciones',
        verbose_name="Proveedor o Facilitador"
    )
    proyecto = models.ForeignKey(
        Proyecto, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='capacitaciones',
        verbose_name="Proyecto / Fondo de Financiamiento"
    )

    horas_duracion = models.PositiveIntegerField(default=1, verbose_name="Horas Totales")
    fecha_inicio = models.DateField(verbose_name="Fecha de Inicio")
    fecha_fin = models.DateField(verbose_name="Fecha de Finalización")
    estado = models.CharField(max_length=20, choices=ESTADOS, default='Planificada', verbose_name="Estado de la Capacitación")
    
    lugar_o_enlace = models.CharField(max_length=250, blank=True, null=True, verbose_name="Lugar / Plataforma Virtual")
    cupo_maximo = models.PositiveIntegerField(default=30, verbose_name="Cupo Máximo")
    
    facultades = models.ManyToManyField(
        Facultad, 
        blank=True,
        related_name='capacitaciones_dirigidas',
        verbose_name="Facultades Beneficiadas / Destinatarias"
    )

    asistencia_qr_habilitada = models.BooleanField(default=True, verbose_name="Registro de Asistencia por QR Habilitado")

    observaciones = models.TextField(blank=True, null=True, verbose_name="Observaciones Generales")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'capacitaciones'
        verbose_name = 'Capacitación'
        verbose_name_plural = 'Capacitaciones'
        ordering = ['-fecha_inicio']

    def __str__(self):
        return f"{self.codigo} - {self.nombre} ({self.estado})"

    @property
    def total_inscritos(self):
        return self.participaciones.count()

    @property
    def total_aprobados(self):
        return self.participaciones.filter(estado_asistencia='Aprobó').count()

    @property
    def total_asistencias(self):
        return self.participaciones.filter(estado_asistencia__in=['Asistió', 'Aprobó']).count()

    @property
    def tiene_evidencias_pendientes(self):
        """Verifica si un curso finalizado carece de evidencias digitales cargadas."""
        return self.estado == 'Finalizada' and self.evidencias.count() == 0

    @property
    def estado_evidencias_label(self):
        """Etiqueta descriptiva del estado de evidencias digitales."""
        count = self.evidencias.count()
        if self.estado == 'Finalizada':
            if count == 0:
                return 'Pendientes (Crítico)'
            return f'Completas ({count} archivos)'
        if count > 0:
            return f'Parciales ({count} archivos)'
        return 'En Plazo'

    @property
    def promedio_satisfaccion(self):
        """Promedio global de satisfacción de las encuestas recibidas."""
        encuestas = self.encuestas.all()
        if not encuestas.exists():
            return None
        promedios = [e.puntaje_general for e in encuestas]
        return round(sum(promedios) / len(promedios), 1)


class Participacion(models.Model):
    """
    Inscripción, asistencia y evaluación de un participante en una capacitación específica.
    """
    ESTADO_ASISTENCIA = [
        ('Inscrito', 'Inscrito'),
        ('Asistió', 'Asistió'),
        ('Aprobó', 'Aprobó'),
        ('No Completó', 'No Completó / Reprobó'),
        ('Cancelado', 'Cancelado'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    capacitacion = models.ForeignKey(Capacitacion, on_delete=models.CASCADE, related_name='participaciones')
    persona = models.ForeignKey(Persona, on_delete=models.RESTRICT, related_name='participaciones')
    
    estado_asistencia = models.CharField(
        max_length=25, 
        choices=ESTADO_ASISTENCIA, 
        default='Inscrito', 
        verbose_name="Estado de Participación"
    )
    calificacion = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True, 
        verbose_name="Calificación Final (0-100)"
    )
    horas_acreditadas = models.PositiveIntegerField(
        null=True, 
        blank=True, 
        verbose_name="Horas Acreditadas"
    )
    certificado_emitido = models.BooleanField(default=False, verbose_name="Certificado Emitido")
    fecha_inscripcion = models.DateTimeField(auto_now_add=True)
    observaciones = models.TextField(blank=True, null=True, verbose_name="Comentarios / Observaciones")

    class Meta:
        db_table = 'participaciones'
        verbose_name = 'Participación / Inscripción'
        verbose_name_plural = 'Participaciones e Inscripciones'
        unique_together = ('capacitacion', 'persona')
        ordering = ['persona__apellidos', 'persona__nombres']

    def __str__(self):
        return f"{self.persona.nombre_completo} en {self.capacitacion.codigo} [{self.estado_asistencia}]"

    def save(self, *args, **kwargs):
        if self.estado_asistencia == 'Aprobó' and not self.horas_acreditadas:
            self.horas_acreditadas = self.capacitacion.horas_duracion
        super().save(*args, **kwargs)


class Evidencia(models.Model):
    """
    Archivos y respaldos documentales digitales de la capacitación.
    """
    TIPOS_EVIDENCIA = [
        ('Lista de Asistencia', 'Lista de Asistencia Firmada'),
        ('Fotografías', 'Fotografías del Evento'),
        ('Informe Final', 'Informe Final de Resultados'),
        ('Temario / Sílabo', 'Temario / Plan de Curso'),
        ('Certificados Emitidos', 'Copia de Certificados'),
        ('Facturas / Recibos', 'Comprobantes Financieros'),
        ('Otro', 'Otro Documento'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    capacitacion = models.ForeignKey(Capacitacion, on_delete=models.CASCADE, related_name='evidencias')
    tipo_evidencia = models.CharField(max_length=50, choices=TIPOS_EVIDENCIA, verbose_name="Tipo de Evidencia")
    archivo = models.FileField(upload_to='evidencias/%Y/%m/', verbose_name="Archivo Digital")
    nombre_original = models.CharField(max_length=255, verbose_name="Nombre Original del Archivo")
    tamano_bytes = models.BigIntegerField(default=0, verbose_name="Tamaño en Bytes")
    mime_type = models.CharField(max_length=100, blank=True, null=True, verbose_name="Tipo MIME")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción o Nota")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'evidencias'
        verbose_name = 'Evidencia Digital'
        verbose_name_plural = 'Evidencias y Documentos de Respaldo'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.tipo_evidencia} - {self.nombre_original} ({self.capacitacion.codigo})"


class EncuestaSatisfaccion(models.Model):
    """
    Encuesta de satisfacción y retroalimentación institucional respondida por los participantes.
    """
    PUNTAJES = [
        (5, '5 - Excelente / Totalmente de acuerdo'),
        (4, '4 - Muy Bueno / De acuerdo'),
        (3, '3 - Bueno / Neutral'),
        (2, '2 - Regular / En desacuerdo'),
        (1, '1 - Deficiente / Totalmente en desacuerdo'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    capacitacion = models.ForeignKey(Capacitacion, on_delete=models.CASCADE, related_name='encuestas', verbose_name="Capacitación")
    participante = models.ForeignKey(Persona, on_delete=models.SET_NULL, null=True, blank=True, related_name='encuestas_respondidas', verbose_name="Participante (Opcional)")
    
    claridad_facilitador = models.PositiveSmallIntegerField(choices=PUNTAJES, default=5, verbose_name="Claridad y Metodología del Facilitador")
    dominio_tema = models.PositiveSmallIntegerField(choices=PUNTAJES, default=5, verbose_name="Dominio del Tema por el Instructor")
    utilidad_practica = models.PositiveSmallIntegerField(choices=PUNTAJES, default=5, verbose_name="Aplicabilidad y Utilidad en su Labor")
    materiales_recursos = models.PositiveSmallIntegerField(choices=PUNTAJES, default=5, verbose_name="Calidad de Materiales y Plataforma")
    
    aspectos_positivos = models.TextField(blank=True, null=True, verbose_name="¿Qué aspectos destaca positivamente de esta formación?")
    aspectos_mejora = models.TextField(blank=True, null=True, verbose_name="¿Qué aspectos sugiere mejorar para futuros eventos?")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Respuesta")

    class Meta:
        db_table = 'encuestas_satisfaccion'
        verbose_name = 'Encuesta de Satisfacción'
        verbose_name_plural = 'Encuestas de Satisfacción'
        ordering = ['-created_at']

    @property
    def puntaje_general(self):
        """Calcula el promedio general de los 4 criterios (escala 1 a 5)."""
        return round((self.claridad_facilitador + self.dominio_tema + self.utilidad_practica + self.materiales_recursos) / 4.0, 2)

    @property
    def porcentaje_satisfaccion(self):
        """Porcentaje de satisfacción (0% - 100%)."""
        return int((self.puntaje_general / 5.0) * 100)

    def __str__(self):
        return f"Encuesta {self.capacitacion.codigo} - Promedio: {self.puntaje_general}/5.0"
