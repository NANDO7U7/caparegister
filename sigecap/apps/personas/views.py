from django.contrib.auth.decorators import permission_required
import os
import io
from datetime import datetime
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db import IntegrityError, transaction
from django.db.models import Q, Sum, Count, Avg
from django.http import HttpResponse
from django.utils import timezone
from django.conf import settings
from django.core import signing

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
from reportlab.lib.units import inch

from .registro import registrar_persona, siguiente_codigo
from .forms import PersonaForm
from .models import Persona, CompetenciaMatriz, MatriculaMatrizDocente
from apps.catalogos.models import Facultad
from apps.capacitaciones.models import Capacitacion, Participacion, EncuestaSatisfaccion

def lista_personas(request):
    """
    Padrón general de participantes con acumulador histórico de horas y metas anuales.
    """
    query = request.GET.get('q', '')
    tipo_filtro = request.GET.get('tipo', '')
    facultad_filtro = request.GET.get('facultad', '')

    personas = Persona.objects.select_related('facultad').annotate(
        total_cursos=Count('participaciones'),
        total_aprobados=Count('participaciones', filter=Q(participaciones__estado_asistencia='Aprobó')),
        total_horas_acumuladas=Sum('participaciones__horas_acreditadas', filter=Q(participaciones__estado_asistencia='Aprobó'))
    ).all()

    if query:
        personas = personas.filter(
            Q(nombres__icontains=query) |
            Q(apellidos__icontains=query) |
            Q(codigo_empleado__icontains=query) |
            Q(documento_identidad__icontains=query)
        )
    if tipo_filtro:
        personas = personas.filter(tipo_personal=tipo_filtro)
    if facultad_filtro:
        personas = personas.filter(facultad_id=facultad_filtro)

    facultades = Facultad.objects.filter(activo=True)

    context = {
        'personas': personas,
        'facultades': facultades,
        'query': query,
        'tipo_filtro': tipo_filtro,
        'facultad_filtro': facultad_filtro,
    }
    return render(request, 'personas/lista.html', context)


def portal_docente_view(request):
    """
    Portal del Docente / 'Mi Trayectoria'.
    Línea de tiempo con horas acumuladas, metas anuales, diplomas y retroalimentación.
    """
    persona_id = request.GET.get('docente')
    if persona_id:
        docente = get_object_or_404(Persona.objects.select_related('facultad'), pk=persona_id)
    else:
        docente = Persona.objects.filter(tipo_personal__in=['Docente', 'Ambos']).select_related('facultad').first()

    if not docente:
        docente = Persona.objects.first()

    docentes_list = Persona.objects.filter(tipo_personal__in=['Docente', 'Ambos']).order_by('apellidos')

    # Línea de tiempo cronológica de participaciones
    participaciones_timeline = []
    if docente:
        participaciones_timeline = Participacion.objects.select_related(
            'capacitacion', 'capacitacion__area_formacion', 'capacitacion__tipo_modalidad', 'capacitacion__proveedor'
        ).filter(persona=docente).order_by('-capacitacion__fecha_inicio')

    # Identificar capacitaciones que ya aprobó pero que no ha respondido encuesta de satisfacción
    encuestas_respondidas_ids = EncuestaSatisfaccion.objects.filter(participante=docente).values_list('capacitacion_id', flat=True) if docente else []
    
    # Progreso de meta anual
    horas_anio = docente.horas_anio_actual if docente else 0
    meta_anual = docente.meta_horas_anuales if docente else 40
    pct_meta = docente.porcentaje_meta_anual if docente else 0
    horas_faltantes = max(0, meta_anual - horas_anio)

    # Matrículas de la matriz docente
    matriculas_matriz = MatriculaMatrizDocente.objects.select_related('competencia').filter(persona=docente).order_by('competencia__orden') if docente else []

    context = {
        'docente': docente,
        'docentes_list': docentes_list,
        'timeline': participaciones_timeline,
        'encuestas_respondidas_ids': list(encuestas_respondidas_ids),
        'horas_anio': horas_anio,
        'meta_anual': meta_anual,
        'pct_meta': pct_meta,
        'horas_faltantes': horas_faltantes,
        'matriculas_matriz': matriculas_matriz,
    }
    return render(request, 'personas/portal_docente.html', context)


def descargar_constancia_pdf(request, pk):
    """
    Genera y descarga en formato PDF oficial la Constancia de Trayectoria Formativa
    utilizando ReportLab con diseño institucional universitario y firmas de acreditación.
    """
    persona = get_object_or_404(Persona.objects.select_related('facultad'), pk=pk)
    participaciones = Participacion.objects.select_related(
        'capacitacion', 'capacitacion__area_formacion', 'capacitacion__tipo_modalidad'
    ).filter(persona=persona, estado_asistencia='Aprobó').order_by('capacitacion__fecha_inicio')

    total_horas = participaciones.aggregate(total=Sum('horas_acreditadas'))['total'] or 0
    promedio_notas = participaciones.aggregate(avg=Avg('calificacion'))['avg'] or 0

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()
    
    # Estilos tipográficos personalizados
    title_style = ParagraphStyle(
        'UniversityTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        alignment=1, # Center
        textColor=colors.HexColor('#00236f')
    )
    subtitle_style = ParagraphStyle(
        'SubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        alignment=1,
        textColor=colors.HexColor('#475569')
    )
    doc_header_style = ParagraphStyle(
        'DocHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        alignment=1,
        textColor=colors.HexColor('#0051d5'),
        spaceAfter=12
    )
    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor('#1e293b'),
        alignment=4 # Justified
    )
    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#0f172a')
    )
    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.white,
        alignment=1
    )

    elements = []

    # Encabezado Institucional
    elements.append(Paragraph("UNIVERSIDAD NACIONAL AUTÓNOMA / INSTITUCIÓN DE EDUCACIÓN SUPERIOR", title_style))
    elements.append(Paragraph("DIRECCIÓN DE TALENTO HUMANO • UNIDAD DE DESARROLLO Y CAPACITACIÓN DOCENTE", subtitle_style))
    elements.append(Paragraph("SISTEMA INSTITUCIONAL DE GESTIÓN DE CAPACITACIONES (SIGECAP)", subtitle_style))
    elements.append(Spacer(1, 8))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#00236f'), spaceAfter=14))

    # Título del Documento
    elements.append(Paragraph("CONSTANCIA OFICIAL DE TRAYECTORIA FORMATIVA Y DESARROLLO DOCENTE", doc_header_style))
    
    # Texto Legal
    texto_constancia = f"""
    La Dirección de Talento Humano y la Unidad de Capacitación Docente de la Institución Universitaria, 
    por medio de la presente <b>HACE CONSTAR</b> que el(la) profesional <b>{persona.nombre_completo.upper()}</b>, 
    identificado(a) con Código de Empleado <b>{persona.codigo_empleado}</b>
    {f' y Documento de Identidad <b>{persona.documento_identidad}</b>' if persona.documento_identidad else ''}, 
    adscrito(a) a la <b>{persona.facultad.nombre if persona.facultad else "Unidad Académica Central"}</b> 
    en calidad de <b>{persona.tipo_personal} ({persona.tipo_contrato})</b>, ha cursado y aprobado satisfactoriamente 
    los siguientes programas de formación, actualización pedagógica, científica y tecnológica:
    """
    elements.append(Paragraph(texto_constancia, body_style))
    elements.append(Spacer(1, 14))

    # Tabla de Cursos Acreditados
    table_data = [[
        Paragraph("<b>N°</b>", table_header_style),
        Paragraph("<b>Código</b>", table_header_style),
        Paragraph("<b>Nombre de la Formación</b>", table_header_style),
        Paragraph("<b>Área / Eje</b>", table_header_style),
        Paragraph("<b>Período / Fecha</b>", table_header_style),
        Paragraph("<b>Horas</b>", table_header_style),
        Paragraph("<b>Calificación</b>", table_header_style),
    ]]

    for idx, part in enumerate(participaciones, start=1):
        cap = part.capacitacion
        calif_str = f"{part.calificacion:.1f}" if part.calificacion else "Aprobado"
        fecha_str = f"{cap.fecha_inicio.strftime('%d/%m/%Y')} al {cap.fecha_fin.strftime('%d/%m/%Y')}"
        
        table_data.append([
            Paragraph(str(idx), table_cell_style),
            Paragraph(f"<b>{cap.codigo}</b>", table_cell_style),
            Paragraph(f"<b>{cap.nombre}</b><br/><font color='#64748b'>{cap.tipo_modalidad.tipo} ({cap.tipo_modalidad.modalidad})</font>", table_cell_style),
            Paragraph(cap.area_formacion.nombre, table_cell_style),
            Paragraph(fecha_str, table_cell_style),
            Paragraph(f"<b>{part.horas_acreditadas or cap.horas_duracion} hrs</b>", table_cell_style),
            Paragraph(calif_str, table_cell_style),
        ])

    if not participaciones:
        table_data.append([
            Paragraph("1", table_cell_style),
            Paragraph("-", table_cell_style),
            Paragraph("Sin capacitaciones con estado Aprobado a la fecha", table_cell_style),
            Paragraph("-", table_cell_style),
            Paragraph("-", table_cell_style),
            Paragraph("0", table_cell_style),
            Paragraph("-", table_cell_style),
        ])

    col_widths = [20, 55, 170, 95, 100, 45, 45]
    t = Table(table_data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#00236f')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 14))

    # Resumen Consolidado
    summary_text = f"""
    <b>RESUMEN CONSOLIDADO:</b> Total de Cursos Aprobados: <b>{participaciones.count()}</b> | 
    Total de Horas Académicas Acreditadas: <b>{total_horas} Horas</b> 
    {f'| Promedio General de Calificaciones: <b>{promedio_notas:.1f} / 100</b>' if promedio_notas > 0 else ''}.
    """
    elements.append(Paragraph(summary_text, body_style))
    elements.append(Spacer(1, 10))

    # Párrafo de Cierre y Emisión
    hoy = timezone.now()
    meses = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']
    fecha_emision = f"Dado en la sede universitaria central, a los {hoy.day} días del mes de {meses[hoy.month - 1]} del año {hoy.year}."
    elements.append(Paragraph(fecha_emision, body_style))
    elements.append(Spacer(1, 30))

    # Firmas de Autoridad Universitaria
    firmas_data = [
        [
            Paragraph("________________________________________<br/><b>Lic. Carlos Valenzuela</b><br/>Coordinador de Capacitación Docente", ParagraphStyle('Firma1', parent=styles['Normal'], alignment=1, fontSize=8)),
            Paragraph("________________________________________<br/><b>MSc. Roberto Mendoza</b><br/>Director de Talento Humano", ParagraphStyle('Firma2', parent=styles['Normal'], alignment=1, fontSize=8))
        ]
    ]
    firmas_table = Table(firmas_data, colWidths=[260, 260])
    firmas_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(KeepTogether([firmas_table]))

    # Pie de Página con Token de Verificación
    elements.append(Spacer(1, 20))
    token_str = f"Código de Verificación Digital: SIGECAP-EXP-{persona.id.hex[:12].upper()} • Generado el {hoy.strftime('%Y-%m-%d %H:%M')}"
    elements.append(Paragraph(f"<font color='#94a3b8' size='7'>{token_str}</font>", ParagraphStyle('Token', parent=styles['Normal'], alignment=1)))

    doc.build(elements)
    buffer.seek(0)

    filename = f"Constancia_Formativa_{persona.codigo_empleado}_{persona.apellidos.replace(' ', '_')}.pdf"
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@permission_required('personas.add_persona', raise_exception=True)
def crear_persona(request):
    """
    Formulario de registro para dar de alta a un nuevo docente o colaborador administrativo.
    """

    form = PersonaForm()
    automatico = True
    if request.method == 'POST':
        data = request.POST.copy()
        codigo = data.get('codigo_empleado', '').strip()
        modo = data.get('modo_codigo')
        automatico = modo == 'automatico' or (modo is None and not codigo)
        firma_invalida = False
        if modo != 'manual' and data.get('codigo_sugerido'):
            try:
                sugerido = signing.loads(
                    data['codigo_sugerido'], salt='personas.codigo',
                    max_age=getattr(settings, 'PERSONAS_CODIGO_MAX_AGE', 1800),
                )
                automatico = codigo == sugerido or (automatico and not codigo)
            except signing.BadSignature:
                firma_invalida = modo == 'automatico'
        elif modo == 'automatico':
            firma_invalida = True
        if firma_invalida:
            form = PersonaForm(data)
            form.is_valid()
            form.add_error(None, 'La sugerencia de código venció o no es válida. Revise los datos y vuelva a guardar.')
        else:
            form, persona = registrar_persona(data, automatico)
            if persona is not None:
                messages.success(request, f"Docente/Colaborador '{persona.nombre_completo}' registrado exitosamente.")
                return redirect('personas:ficha', pk=persona.id)

    facultades = Facultad.objects.filter(activo=True)
    tipos_personal = Persona.TIPO_PERSONAL
    tipos_contrato = Persona.TIPO_CONTRATO
    grados_academicos = Persona.GRADO_ACADEMICO
    sexos = Persona.SEXO
    next_code = siguiente_codigo() if request.method != 'POST' else form['codigo_empleado'].value()

    form.initial['codigo_empleado'] = next_code
    form.initial['grado_academico'] = 'Maestría'

    context = {
        'form': form,
        'facultades': facultades,
        'tipos_personal': tipos_personal,
        'tipos_contrato': tipos_contrato,
        'grados_academicos': grados_academicos,
        'sexos': sexos,
        'next_code': next_code,
        'modo_codigo': 'automatico' if automatico else 'manual',
        'codigo_sugerido': signing.dumps(
            form['codigo_empleado'].value() if automatico else next_code,
            salt='personas.codigo',
        ) if automatico else '',
        'accion': 'Registrar',
    }
    return render(request, 'personas/crear_editar.html', context)


@permission_required('personas.change_persona', raise_exception=True)
def editar_persona(request, pk):
    """
    Formulario para editar la información de un docente o colaborador existente.
    """
    persona = get_object_or_404(Persona, pk=pk)


    form = PersonaForm(instance=persona)
    if request.method == 'POST':
        form = PersonaForm(request.POST, instance=persona)
        if form.is_valid():
            try:
                with transaction.atomic():
                    form.save()
            except IntegrityError:
                form.add_error(None, 'No se pudo guardar: existe un conflicto con otro registro. Revise el código, documento y correo e intente nuevamente.')
            else:
                messages.success(request, f"Datos de '{persona.nombre_completo}' actualizados exitosamente.")
                return redirect('personas:ficha', pk=persona.id)

    facultades = Facultad.objects.filter(activo=True)
    tipos_personal = Persona.TIPO_PERSONAL
    tipos_contrato = Persona.TIPO_CONTRATO
    grados_academicos = Persona.GRADO_ACADEMICO
    sexos = Persona.SEXO

    context = {
        'form': form,
        'persona': persona,
        'facultades': facultades,
        'tipos_personal': tipos_personal,
        'tipos_contrato': tipos_contrato,
        'grados_academicos': grados_academicos,
        'sexos': sexos,
        'accion': 'Editar',
    }
    return render(request, 'personas/crear_editar.html', context)


def ficha_persona(request, pk):
    """
    Ficha de Participante (Historial Acumulativo Personal).
    """
    persona = get_object_or_404(
        Persona.objects.select_related('facultad'),
        pk=pk
    )

    participaciones = Participacion.objects.select_related(
        'capacitacion', 'capacitacion__area_formacion', 'capacitacion__tipo_modalidad'
    ).filter(persona=persona).order_by('-capacitacion__fecha_inicio')

    total_horas = participaciones.filter(estado_asistencia='Aprobó').aggregate(
        total=Sum('horas_acreditadas')
    )['total'] or 0

    total_aprobados = participaciones.filter(estado_asistencia='Aprobó').count()
    total_en_curso = participaciones.filter(estado_asistencia='Inscrito').count()
    matriculas_matriz = MatriculaMatrizDocente.objects.select_related('competencia').filter(persona=persona).order_by('competencia__orden')

    context = {
        'persona': persona,
        'participaciones': participaciones,
        'matriculas_matriz': matriculas_matriz,
        'total_horas': total_horas,
        'total_aprobados': total_aprobados,
        'total_en_curso': total_en_curso,
    }
    return render(request, 'personas/ficha.html', context)


def matriz_docente_view(request):
    """
    Vista de la Matriz de Seguimiento y Matrícula del Plan Integral Docente.
    """
    facultad_filtro = request.GET.get('facultad', '')
    contrato_filtro = request.GET.get('contrato', '')
    query = request.GET.get('q', '')

    docentes = Persona.objects.filter(tipo_personal__in=['Docente', 'Ambos']).select_related('facultad')

    if query:
        docentes = docentes.filter(
            Q(nombres__icontains=query) |
            Q(apellidos__icontains=query) |
            Q(codigo_empleado__icontains=query)
        )
    if facultad_filtro:
        docentes = docentes.filter(facultad_id=facultad_filtro)
    if contrato_filtro:
        docentes = docentes.filter(tipo_contrato=contrato_filtro)

    competencias = CompetenciaMatriz.objects.filter(activo=True).order_by('orden')
    matriculas = MatriculaMatrizDocente.objects.select_related('competencia').all()
    matriculas_map = {(m.persona_id, m.competencia_id): m for m in matriculas}

    matriz_filas = []
    for doc in docentes:
        celdas = []
        aprobados_count = 0
        en_curso_count = 0
        for comp in competencias:
            mat = matriculas_map.get((doc.id, comp.id))
            if mat:
                if mat.estado == 'Aprobado':
                    aprobados_count += 1
                elif mat.estado == 'En Curso':
                    en_curso_count += 1
            celdas.append({
                'competencia': comp,
                'matricula': mat,
            })
        
        pct_avance = int((aprobados_count / len(competencias) * 100)) if competencias.exists() else 0
        matriz_filas.append({
            'docente': doc,
            'celdas': celdas,
            'aprobados': aprobados_count,
            'en_curso': en_curso_count,
            'pct_avance': pct_avance,
        })

    facultades = Facultad.objects.filter(activo=True)

    context = {
        'matriz_filas': matriz_filas,
        'competencias': competencias,
        'facultades': facultades,
        'facultad_filtro': facultad_filtro,
        'contrato_filtro': contrato_filtro,
        'query': query,
        'total_docentes': docentes.count(),
        'total_competencias': competencias.count(),
    }
    return render(request, 'personas/matriz_docente.html', context)


@permission_required('personas.change_matriculamatrizdocente', raise_exception=True)
def matricular_docente_matriz(request):
    """
    Registra o actualiza el estado de un docente en una competencia específica de la Matriz.
    """

    if request.method == 'POST':
        persona_id = request.POST.get('persona_id')
        competencia_id = request.POST.get('competencia_id')
        estado = request.POST.get('estado', 'Pendiente')
        fecha = request.POST.get('fecha_completado') or None
        especialidad = request.POST.get('nombre_curso_especialidad', '')
        observaciones = request.POST.get('observaciones', '')

        if persona_id and competencia_id:
            mat, created = MatriculaMatrizDocente.objects.update_or_create(
                persona_id=persona_id,
                competencia_id=competencia_id,
                defaults={
                    'estado': estado,
                    'fecha_completado': fecha if fecha else None,
                    'nombre_curso_especialidad': especialidad,
                    'observaciones': observaciones,
                }
            )
            messages.success(request, f"Matrícula actualizada para {mat.persona.nombre_completo}: {mat.competencia.nombre} [{estado}].")

    return redirect(request.META.get('HTTP_REFERER', 'personas:matriz_docente'))
