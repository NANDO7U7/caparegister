import uuid
from django.db import models

class Facultad(models.Model):
    """Facultad, Centro Regional o Unidad Organizacional Universitaria."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo = models.CharField(max_length=20, unique=True, verbose_name="Código")
    nombre = models.CharField(max_length=150, verbose_name="Nombre de la Facultad/Unidad")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    activo = models.BooleanField(default=True, verbose_name="Estado Activo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'facultades'
        verbose_name = 'Facultad / Unidad'
        verbose_name_plural = 'Facultades y Unidades'
        ordering = ['nombre']

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


class AreaFormacion(models.Model):
    """Área o Eje Formativo de las capacitaciones."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo = models.CharField(max_length=20, unique=True, verbose_name="Código")
    nombre = models.CharField(max_length=100, verbose_name="Área de Formación")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    activo = models.BooleanField(default=True, verbose_name="Estado Activo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'areas_formacion'
        verbose_name = 'Área de Formación'
        verbose_name_plural = 'Áreas de Formación'
        ordering = ['nombre']

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


class TipoModalidad(models.Model):
    """Tipos (Taller, Curso, Diplomado, etc.) y Modalidades (Presencial, Virtual, Híbrida)."""
    TIPOS = [
        ('Taller', 'Taller'),
        ('Curso', 'Curso'),
        ('Diplomado', 'Diplomado'),
        ('Congreso', 'Congreso'),
        ('Conferencia / Seminario', 'Conferencia / Seminario'),
        ('Certificación', 'Certificación'),
        ('Otro', 'Otro'),
    ]
    MODALIDADES = [
        ('Presencial', 'Presencial'),
        ('Virtual', 'Virtual'),
        ('Híbrida', 'Híbrida'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tipo = models.CharField(max_length=50, choices=TIPOS, verbose_name="Tipo de Formación")
    modalidad = models.CharField(max_length=30, choices=MODALIDADES, verbose_name="Modalidad")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    activo = models.BooleanField(default=True, verbose_name="Estado Activo")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tipos_modalidad'
        verbose_name = 'Tipo y Modalidad'
        verbose_name_plural = 'Tipos y Modalidades'
        unique_together = ('tipo', 'modalidad')
        ordering = ['tipo', 'modalidad']

    def __str__(self):
        return f"{self.tipo} ({self.modalidad})"


class Proyecto(models.Model):
    """Proyecto institucional o fuente de financiamiento para capacitaciones."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo = models.CharField(max_length=50, unique=True, verbose_name="Código del Proyecto")
    nombre = models.CharField(max_length=200, verbose_name="Nombre del Proyecto")
    fuente_financiamiento = models.CharField(max_length=100, blank=True, null=True, verbose_name="Fuente de Financiamiento")
    presupuesto_asignado = models.DecimalField(max_digits=14, decimal_places=2, default=0.00, verbose_name="Presupuesto Asignado (L/USD)")
    activo = models.BooleanField(default=True, verbose_name="Estado Activo")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'proyectos'
        verbose_name = 'Proyecto / Fondo'
        verbose_name_plural = 'Proyectos y Fondos'
        ordering = ['codigo']

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


class Proveedor(models.Model):
    """Proveedor, Consultor o Institución Externa capacitadora."""
    TIPOS = [
        ('Interno', 'Interno (Universidad)'),
        ('Externo', 'Externo (Empresa / Consultor)'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo = models.CharField(max_length=30, unique=True, blank=True, null=True, verbose_name="Código")
    nombre = models.CharField(max_length=200, verbose_name="Nombre / Razón Social")
    tipo = models.CharField(max_length=20, choices=TIPOS, default='Externo', verbose_name="Tipo de Proveedor")
    pais = models.CharField(max_length=80, default='Local', verbose_name="País")
    contacto_nombre = models.CharField(max_length=150, blank=True, null=True, verbose_name="Nombre de Contacto")
    contacto_email = models.EmailField(max_length=150, blank=True, null=True, verbose_name="Email de Contacto")
    contacto_telefono = models.CharField(max_length=50, blank=True, null=True, verbose_name="Teléfono")
    observaciones = models.TextField(blank=True, null=True, verbose_name="Observaciones")
    activo = models.BooleanField(default=True, verbose_name="Estado Activo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'proveedores'
        verbose_name = 'Proveedor / Entidad Capacitadora'
        verbose_name_plural = 'Proveedores e Instituciones'
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.tipo})"
