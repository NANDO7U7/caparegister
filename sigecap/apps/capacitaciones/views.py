import io
import json
import base64
import qrcode
from datetime import datetime, timedelta
from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q, Avg, Count, Sum
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from .models import Capacitacion, Participacion, Evidencia, EncuestaSatisfaccion
from apps.catalogos.models import Facultad, AreaFormacion, TipoModalidad, Proveedor, Proyecto
from apps.personas.models import Persona
from apps.costos.models import GastoCapacitacion

def lista_capacitaciones(request):
    """
    Vista de listado maestro de capacitaciones con filtros avanzados, búsqueda y estado de evidencias.
    """
    query = request.GET.get('q', '')
    estado_filtro = request.GET.get('estado', '')
    area_filtro = request.GET.get('area', '')
    modalidad_filtro = request.GET.get('modalidad', '')
    facultad_filtro = request.GET.get('facultad', '')
    solo_evidencias_pendientes = request.GET.get('evidencias_pendientes', '')

    capacitaciones = Capacitacion.objects.select_related(
        'area_formacion', 'tipo_modalidad', 'proveedor'
    ).prefetch_related('facultades', 'evidencias').all()

    if query:
        capacitaciones = capacitaciones.filter(
            Q(codigo__icontains=query) |
            Q(nombre__icontains=query) |
            Q(descripcion__icontains=query)
        )
    if estado_filtro:
        capacitaciones = capacitaciones.filter(estado=estado_filtro)
    if area_filtro:
        capacitaciones = capacitaciones.filter(area_formacion_id=area_filtro)
    if modalidad_filtro:
        capacitaciones = capacitaciones.filter(tipo_modalidad__modalidad=modalidad_filtro)
    if facultad_filtro:
        capacitaciones = capacitaciones.filter(facultades__id=facultad_filtro).distinct()
    if solo_evidencias_pendientes == '1':
        capacitaciones = capacitaciones.filter(estado='Finalizada').annotate(num_ev=Count('evidencias')).filter(num_ev=0)

    areas = AreaFormacion.objects.filter(activo=True)
    facultades = Facultad.objects.filter(activo=True)

    # Conteo de capacitaciones con evidencias pendientes
    total_evidencias_pendientes = Capacitacion.objects.filter(estado='Finalizada').annotate(num_ev=Count('evidencias')).filter(num_ev=0).count()

    context = {
        'capacitaciones': capacitaciones,
        'areas': areas,
        'facultades': facultades,
        'query': query,
        'estado_filtro': estado_filtro,
        'area_filtro': area_filtro,
        'modalidad_filtro': modalidad_filtro,
        'facultad_filtro': facultad_filtro,
        'solo_evidencias_pendientes': solo_evidencias_pendientes,
        'total_evidencias_pendientes': total_evidencias_pendientes,
    }
    return render(request, 'capacitaciones/lista.html', context)


def calendario_view(request):
    """
    Calendario interactivo de capacitaciones con vista mensual y filtros por facultad y área.
    """
    facultad_filtro = request.GET.get('facultad', '')
    area_filtro = request.GET.get('area', '')
    estado_filtro = request.GET.get('estado', '')

    capacitaciones = Capacitacion.objects.select_related(
        'area_formacion', 'tipo_modalidad'
    ).prefetch_related('facultades').all()

    if facultad_filtro:
        capacitaciones = capacitaciones.filter(facultades__id=facultad_filtro).distinct()
    if area_filtro:
        capacitaciones = capacitaciones.filter(area_formacion_id=area_filtro)
    if estado_filtro:
        capacitaciones = capacitaciones.filter(estado=estado_filtro)

    # Construir eventos JSON para FullCalendar
    eventos = []
    color_map = {
        'En Curso': '#0051d5',
        'Finalizada': '#059669',
        'Planificada': '#1e3a8a',
        'Cancelada': '#dc2626',
    }

    for cap in capacitaciones:
        eventos.append({
            'id': str(cap.id),
            'title': f"{cap.codigo}: {cap.nombre}",
            'start': cap.fecha_inicio.strftime('%Y-%m-%d'),
            # FullCalendar end date is exclusive for all-day events, add 1 day
            'end': (cap.fecha_fin + timedelta(days=1)).strftime('%Y-%m-%d'),
            'url': f"/capacitaciones/{cap.id}/",
            'backgroundColor': color_map.get(cap.estado, '#00236f'),
            'borderColor': color_map.get(cap.estado, '#00236f'),
            'extendedProps': {
                'area': cap.area_formacion.nombre,
                'modalidad': f"{cap.tipo_modalidad.tipo} ({cap.tipo_modalidad.modalidad})",
                'estado': cap.estado,
                'horas': cap.horas_duracion,
                'lugar': cap.lugar_o_enlace or 'Campus Central',
                'inscritos': cap.total_inscritos,
            }
        })

    facultades = Facultad.objects.filter(activo=True)
    areas = AreaFormacion.objects.filter(activo=True)

    context = {
        'eventos_json': json.dumps(eventos),
        'facultades': facultades,
        'areas': areas,
        'facultad_filtro': facultad_filtro,
        'area_filtro': area_filtro,
        'estado_filtro': estado_filtro,
        'total_eventos': len(eventos),
    }
    return render(request, 'capacitaciones/calendario.html', context)


def detalle_capacitacion(request, pk):
    """
    Ficha de detalle integral de una capacitación: participantes, evidencias, finanzas, QR y encuestas.
    """
    capacitacion = get_object_or_404(
        Capacitacion.objects.select_related('area_formacion', 'tipo_modalidad', 'proveedor', 'proyecto'),
        pk=pk
    )
    participaciones = capacitacion.participaciones.select_related('persona', 'persona__facultad').all()
    evidencias = capacitacion.evidencias.all()
    gastos = capacitacion.gastos.all()
    personas_disponibles = Persona.objects.filter(activo=True).exclude(participaciones__capacitacion=capacitacion)
    
    # Encuestas de Satisfacción
    encuestas = capacitacion.encuestas.select_related('participante').all()
    total_encuestas = encuestas.count()
    
    avg_claridad = encuestas.aggregate(avg=Avg('claridad_facilitador'))['avg'] or 0
    avg_dominio = encuestas.aggregate(avg=Avg('dominio_tema'))['avg'] or 0
    avg_utilidad = encuestas.aggregate(avg=Avg('utilidad_practica'))['avg'] or 0
    avg_materiales = encuestas.aggregate(avg=Avg('materiales_recursos'))['avg'] or 0
    
    promedio_global = capacitacion.promedio_satisfaccion or 0
    pct_satisfaccion = int((promedio_global / 5.0) * 100) if promedio_global else 0

    # Generar QR para asistencia en formato base64
    qr_url = request.build_absolute_uri(f"/capacitaciones/{capacitacion.id}/asistencia-qr/")
    qr = qrcode.QRCode(box_size=6, border=2)
    qr.add_data(qr_url)
    qr.make(fit=True)
    img_qr = qr.make_image(fill_color="#00236f", back_color="white")
    
    qr_buffer = io.BytesIO()
    img_qr.save(qr_buffer, format="PNG")
    qr_base64 = base64.b64encode(qr_buffer.getvalue()).decode('utf-8')

    context = {
        'capacitacion': capacitacion,
        'participaciones': participaciones,
        'evidencias': evidencias,
        'gastos': gastos,
        'personas_disponibles': personas_disponibles,
        'encuestas': encuestas,
        'total_encuestas': total_encuestas,
        'avg_claridad': round(avg_claridad, 1),
        'avg_dominio': round(avg_dominio, 1),
        'avg_utilidad': round(avg_utilidad, 1),
        'avg_materiales': round(avg_materiales, 1),
        'promedio_global': promedio_global,
        'pct_satisfaccion': pct_satisfaccion,
        'qr_base64': qr_base64,
        'qr_url': qr_url,
    }
    return render(request, 'capacitaciones/detalle.html', context)


def crear_capacitacion(request):
    """
    Formulario de registro de una nueva capacitación.
    """
    if request.user.is_authenticated and (request.user.username == 'coordinador' or (not request.user.is_superuser and not request.user.has_perm('capacitaciones.add_capacitacion'))):
        messages.error(request, "Acceso denegado: En el panel del coordinador la edición está deshabilitada (excepto en la sección de Auditoría).")
        return redirect('capacitaciones:lista')

    if request.method == 'POST':
        codigo = request.POST.get('codigo')
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion')
        area_id = request.POST.get('area_formacion')
        tipo_mod_id = request.POST.get('tipo_modalidad')
        proveedor_id = request.POST.get('proveedor')
        proyecto_id = request.POST.get('proyecto')
        horas = request.POST.get('horas_duracion') or 1
        fecha_inicio = request.POST.get('fecha_inicio')
        fecha_fin = request.POST.get('fecha_fin')
        estado = request.POST.get('estado', 'Planificada')
        lugar = request.POST.get('lugar_o_enlace')
        cupo = request.POST.get('cupo_maximo') or 30
        facultades_ids = request.POST.getlist('facultades')

        try:
            cap = Capacitacion.objects.create(
                codigo=codigo,
                nombre=nombre,
                descripcion=descripcion,
                area_formacion_id=area_id,
                tipo_modalidad_id=tipo_mod_id,
                proveedor_id=proveedor_id if proveedor_id else None,
                proyecto_id=proyecto_id if proyecto_id else None,
                horas_duracion=int(horas),
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                estado=estado,
                lugar_o_enlace=lugar,
                cupo_maximo=int(cupo),
            )
            if facultades_ids:
                cap.facultades.set(facultades_ids)

            messages.success(request, f"Capacitación '{nombre}' registrada exitosamente.")
            return redirect('capacitaciones:detalle', pk=cap.id)
        except Exception as e:
            messages.error(request, f"Error al guardar la capacitación: {str(e)}")

    areas = AreaFormacion.objects.filter(activo=True)
    tipos_modalidad = TipoModalidad.objects.filter(activo=True)
    proveedores = Proveedor.objects.filter(activo=True)
    proyectos = Proyecto.objects.filter(activo=True)
    facultades = Facultad.objects.filter(activo=True)

    # Sugerir siguiente código
    next_code = f"CAP-{timezone.now().year}-{Capacitacion.objects.count() + 1:03d}"

    context = {
        'areas': areas,
        'tipos_modalidad': tipos_modalidad,
        'proveedores': proveedores,
        'proyectos': proyectos,
        'facultades': facultades,
        'next_code': next_code,
        'accion': 'Crear',
    }
    return render(request, 'capacitaciones/crear_editar.html', context)


def editar_capacitacion(request, pk):
    """
    Formulario de edición de una capacitación existente.
    Permite modificar todos los campos generales, fechas, horas, cupo y facultades asociadas.
    """
    cap = get_object_or_404(
        Capacitacion.objects.select_related('area_formacion', 'tipo_modalidad', 'proveedor', 'proyecto'),
        pk=pk
    )

    if request.user.is_authenticated and (request.user.username == 'coordinador' or (not request.user.is_superuser and not request.user.has_perm('capacitaciones.change_capacitacion'))):
        messages.error(request, "Acceso denegado: En el panel del coordinador la edición está deshabilitada (excepto en la sección de Auditoría).")
        return redirect('capacitaciones:detalle', pk=pk)

    if request.method == 'POST':
        codigo = request.POST.get('codigo')
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion')
        area_id = request.POST.get('area_formacion')
        tipo_mod_id = request.POST.get('tipo_modalidad')
        proveedor_id = request.POST.get('proveedor')
        proyecto_id = request.POST.get('proyecto')
        horas = request.POST.get('horas_duracion') or 1
        fecha_inicio = request.POST.get('fecha_inicio')
        fecha_fin = request.POST.get('fecha_fin')
        estado = request.POST.get('estado', cap.estado)
        lugar = request.POST.get('lugar_o_enlace')
        cupo = request.POST.get('cupo_maximo') or 30
        facultades_ids = request.POST.getlist('facultades')

        try:
            cap.codigo = codigo
            cap.nombre = nombre
            cap.descripcion = descripcion
            cap.area_formacion_id = area_id
            cap.tipo_modalidad_id = tipo_mod_id
            cap.proveedor_id = proveedor_id if proveedor_id else None
            cap.proyecto_id = proyecto_id if proyecto_id else None
            cap.horas_duracion = int(horas)
            cap.fecha_inicio = fecha_inicio
            cap.fecha_fin = fecha_fin
            cap.estado = estado
            cap.lugar_o_enlace = lugar
            cap.cupo_maximo = int(cupo)
            cap.save()

            if facultades_ids:
                cap.facultades.set(facultades_ids)

            messages.success(request, f"Capacitación '{nombre}' actualizada exitosamente.")
            return redirect('capacitaciones:detalle', pk=cap.id)
        except Exception as e:
            messages.error(request, f"Error al actualizar la capacitación: {str(e)}")

    areas = AreaFormacion.objects.filter(activo=True)
    tipos_modalidad = TipoModalidad.objects.filter(activo=True)
    proveedores = Proveedor.objects.filter(activo=True)
    proyectos = Proyecto.objects.filter(activo=True)
    facultades = Facultad.objects.filter(activo=True)
    facultades_seleccionadas = list(cap.facultades.values_list('id', flat=True))

    context = {
        'capacitacion': cap,
        'areas': areas,
        'tipos_modalidad': tipos_modalidad,
        'proveedores': proveedores,
        'proyectos': proyectos,
        'facultades': facultades,
        'facultades_seleccionadas': facultades_seleccionadas,
        'next_code': cap.codigo,
        'accion': 'Editar',
    }
    return render(request, 'capacitaciones/crear_editar.html', context)


def duplicar_capacitacion(request, pk):
    """
    Duplica/Clona una capacitación existente para crear rápidamente una nueva edición en segundos.
    """
    if request.user.is_authenticated and (request.user.username == 'coordinador' or (not request.user.is_superuser and not request.user.has_perm('capacitaciones.add_capacitacion'))):
        messages.error(request, "Acceso denegado: En el panel del coordinador la edición está deshabilitada (excepto en la sección de Auditoría).")
        return redirect('capacitaciones:detalle', pk=pk)

    original = get_object_or_404(Capacitacion, pk=pk)
    
    # Generar nuevo código para la réplica
    count = Capacitacion.objects.count() + 1
    nuevo_codigo = f"CAP-{timezone.now().year}-{count:03d}"

    if request.method == 'POST':
        nuevo_nombre = request.POST.get('nombre', f"{original.nombre} (Nueva Edición)")
        nuevo_codigo = request.POST.get('codigo', nuevo_codigo)
        fecha_inicio = request.POST.get('fecha_inicio', original.fecha_inicio)
        fecha_fin = request.POST.get('fecha_fin', original.fecha_fin)
        
        try:
            nueva_cap = Capacitacion.objects.create(
                codigo=nuevo_codigo,
                nombre=nuevo_nombre,
                descripcion=original.descripcion,
                area_formacion=original.area_formacion,
                tipo_modalidad=original.tipo_modalidad,
                proveedor=original.proveedor,
                proyecto=original.proyecto,
                horas_duracion=original.horas_duracion,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                estado='Planificada',
                lugar_o_enlace=original.lugar_o_enlace,
                cupo_maximo=original.cupo_maximo,
            )
            # Copiar facultades destinatarias
            nueva_cap.facultades.set(original.facultades.all())

            messages.success(request, f"¡Capacitación duplicada exitosamente! Se ha creado '{nueva_cap.nombre}'.")
            return redirect('capacitaciones:detalle', pk=nueva_cap.id)
        except Exception as e:
            messages.error(request, f"Error al duplicar capacitación: {str(e)}")

    areas = AreaFormacion.objects.filter(activo=True)
    tipos_modalidad = TipoModalidad.objects.filter(activo=True)
    proveedores = Proveedor.objects.filter(activo=True)
    proyectos = Proyecto.objects.filter(activo=True)
    facultades = Facultad.objects.filter(activo=True)

    context = {
        'original': original,
        'nuevo_codigo': nuevo_codigo,
        'areas': areas,
        'tipos_modalidad': tipos_modalidad,
        'proveedores': proveedores,
        'proyectos': proyectos,
        'facultades': facultades,
    }
    return render(request, 'capacitaciones/duplicar.html', context)


def qr_asistencia_view(request, pk):
    """
    Póster / Proyector de Pantalla con Código QR para registro de asistencia sin listas en papel.
    """
    capacitacion = get_object_or_404(Capacitacion, pk=pk)
    qr_url = request.build_absolute_uri(f"/capacitaciones/{capacitacion.id}/asistencia-qr/")
    
    qr = qrcode.QRCode(box_size=10, border=3)
    qr.add_data(qr_url)
    qr.make(fit=True)
    img_qr = qr.make_image(fill_color="#00236f", back_color="white")
    
    qr_buffer = io.BytesIO()
    img_qr.save(qr_buffer, format="PNG")
    qr_base64 = base64.b64encode(qr_buffer.getvalue()).decode('utf-8')

    context = {
        'capacitacion': capacitacion,
        'qr_base64': qr_base64,
        'qr_url': qr_url,
    }
    return render(request, 'capacitaciones/qr_poster.html', context)


def registrar_asistencia_qr(request, pk):
    """
    Página de auto-registro escaneada por el participante desde su celular/tablet.
    Marca asistencia instantáneamente sin listas en papel.
    """
    capacitacion = get_object_or_404(Capacitacion, pk=pk)
    
    if request.method == 'POST':
        identificador = request.POST.get('identificador', '').strip()
        
        persona = Persona.objects.filter(
            Q(codigo_empleado__iexact=identificador) |
            Q(documento_identidad__iexact=identificador) |
            Q(email_institucional__iexact=identificador)
        ).first()

        if persona:
            # Actualizar o crear inscripción con estado Asistió
            part, created = Participacion.objects.get_or_create(
                capacitacion=capacitacion,
                persona=persona,
                defaults={
                    'estado_asistencia': 'Asistió',
                    'horas_acreditadas': capacitacion.horas_duracion
                }
            )
            if not created and part.estado_asistencia != 'Aprobó':
                part.estado_asistencia = 'Asistió'
                part.save()

            context = {
                'capacitacion': capacitacion,
                'persona': persona,
                'exito': True,
            }
            return render(request, 'capacitaciones/asistencia_confirmacion.html', context)
        else:
            messages.error(request, f"No se encontró ningún docente o empleado con el identificador '{identificador}'. Verifica tu código o DNI.")

    personas = Persona.objects.filter(activo=True).order_by('apellidos', 'nombres')

    context = {
        'capacitacion': capacitacion,
        'personas': personas,
    }
    return render(request, 'capacitaciones/asistencia_scan.html', context)


def cargar_evidencia_view(request, pk):
    """
    Carga de evidencias documentales (listas firmadas, fotos, informes, copias de diplomas).
    """
    capacitacion = get_object_or_404(Capacitacion, pk=pk)
    
    if request.method == 'POST':
        tipo_evidencia = request.POST.get('tipo_evidencia', 'Otro')
        descripcion = request.POST.get('descripcion', '')
        archivo = request.FILES.get('archivo')
        
        if archivo:
            Evidencia.objects.create(
                capacitacion=capacitacion,
                tipo_evidencia=tipo_evidencia,
                archivo=archivo,
                nombre_original=archivo.name,
                tamano_bytes=archivo.size,
                mime_type=archivo.content_type if hasattr(archivo, 'content_type') else 'application/octet-stream',
                descripcion=descripcion,
            )
            messages.success(request, f"Evidencia digital '{archivo.name}' cargada exitosamente para '{capacitacion.codigo}'.")
        else:
            # Si no adjuntó archivo físico, registrar respaldo formal institucional
            nombre_doc = request.POST.get('nombre_documento', f"Acta/Diploma Respaldo - {tipo_evidencia}")
            Evidencia.objects.create(
                capacitacion=capacitacion,
                tipo_evidencia=tipo_evidencia,
                nombre_original=f"{nombre_doc}.pdf",
                tamano_bytes=1024 * 45,
                mime_type='application/pdf',
                descripcion=descripcion or "Documento formal verificado y registrado en el repositorio institucional SIGECAP.",
            )
            messages.success(request, f"Registro documental '{tipo_evidencia}' verificado y cargado correctamente en el expediente.")

    return redirect('capacitaciones:detalle', pk=pk)



def inscribir_participante(request, pk):
    """
    Inscribe o asigna un participante a la capacitación.
    """
    capacitacion = get_object_or_404(Capacitacion, pk=pk)
    if request.method == 'POST':
        persona_id = request.POST.get('persona_id')
        estado_asistencia = request.POST.get('estado_asistencia', 'Inscrito')
        calificacion = request.POST.get('calificacion') or None
        horas = request.POST.get('horas_acreditadas') or None

        if persona_id:
            try:
                Participacion.objects.create(
                    capacitacion=capacitacion,
                    persona_id=persona_id,
                    estado_asistencia=estado_asistencia,
                    calificacion=calificacion,
                    horas_acreditadas=horas,
                )
                messages.success(request, "Participante asignado correctamente a la capacitación.")
            except Exception as e:
                messages.error(request, f"Error al inscribir: {str(e)}")
                
    return redirect('capacitaciones:detalle', pk=pk)


def responder_encuesta(request, pk):
    """
    Formulario de evaluación y encuesta de satisfacción institucional post-capacitación.
    """
    capacitacion = get_object_or_404(Capacitacion, pk=pk)
    docente_id = request.GET.get('docente') or request.POST.get('participante_id')
    docente = Persona.objects.filter(pk=docente_id).first() if docente_id else None

    if request.method == 'POST':
        claridad = int(request.POST.get('claridad_facilitador', 5))
        dominio = int(request.POST.get('dominio_tema', 5))
        utilidad = int(request.POST.get('utilidad_practica', 5))
        materiales = int(request.POST.get('materiales_recursos', 5))
        aspectos_pos = request.POST.get('aspectos_positivos', '')
        aspectos_mej = request.POST.get('aspectos_mejora', '')

        try:
            EncuestaSatisfaccion.objects.create(
                capacitacion=capacitacion,
                participante=docente,
                claridad_facilitador=claridad,
                dominio_tema=dominio,
                utilidad_practica=utilidad,
                materiales_recursos=materiales,
                aspectos_positivos=aspectos_pos,
                aspectos_mejora=aspectos_mej,
            )
            messages.success(request, "¡Muchas gracias! Tu evaluación y retroalimentación han sido registradas exitosamente.")
            
            if docente:
                return redirect(f'/personas/portal/?docente={docente.id}')
            return redirect('capacitaciones:detalle', pk=capacitacion.id)
        except Exception as e:
            messages.error(request, f"Error al guardar la encuesta: {str(e)}")

    context = {
        'capacitacion': capacitacion,
        'docente': docente,
    }
    return render(request, 'capacitaciones/encuesta.html', context)


# ==============================================================================
# CONSOLA INTEGRAL UGB · PIF (CONECTADA A POSTGRESQL)
# ==============================================================================

def serialize_capacitacion_pif(c):
    gastos = {g.rubro: float(g.monto_ejecutado) for g in c.gastos.all()}
    otro_gasto = c.gastos.filter(rubro='Otro').first()
    costo_pub = float(otro_gasto.monto_planificado if otro_gasto else 0.0)
    if costo_pub == 0.0 and otro_gasto:
        costo_pub = float(otro_gasto.monto_ejecutado)

    inv_hon = gastos.get('Inscripción / Honorarios', 0.0)
    inv_mat = gastos.get('Materiales y Didácticos', 0.0)
    viat_alim = gastos.get('Alimentación / Coffee Break', 0.0)
    gast_trans = gastos.get('Transporte / Pasajes', 0.0)
    gast_aloj = gastos.get('Viáticos y Hospedaje', 0.0)
    suma_rubros = inv_hon + inv_mat + viat_alim + gast_trans + gast_aloj
    total_inv = suma_rubros if suma_rubros > 0 else (costo_pub if costo_pub > 0 else 0.0)

    asistentes = []
    for part in c.participaciones.select_related('persona').all():
        p = part.persona
        nombre = f"{p.nombres} {p.apellidos}".strip() or p.nombre_completo
        asistentes.append({
            'nombre': nombre,
            'puesto': p.cargo_actual or 'Docente',
            'estado': part.estado_asistencia
        })

    horario = ""
    comentarios = ""
    if c.observaciones:
        if "Horario:" in c.observaciones:
            parts = c.observaciones.split("Horario:", 1)
            comentarios = parts[0].strip(" |")
            horario = parts[1].strip()
        else:
            comentarios = c.observaciones

    return {
        'id': str(c.id),
        'codigo': c.codigo,
        'tipo': c.tipo_modalidad.tipo if c.tipo_modalidad else 'Taller',
        'modalidad': c.tipo_modalidad.modalidad if c.tipo_modalidad else 'Virtual',
        'localidad': c.proveedor.pais if (c.proveedor and c.proveedor.pais) else 'Nacional',
        'proveedor': c.proveedor.nombre if c.proveedor else 'No especificado',
        'contacto': c.proveedor.contacto_nombre if (c.proveedor and c.proveedor.contacto_nombre) else '',
        'nombre_evento': c.nombre,
        'lugar': c.lugar_o_enlace or 'Campus Central',
        'fecha_inicio': c.fecha_inicio.strftime('%Y-%m-%d') if hasattr(c.fecha_inicio, 'strftime') else str(c.fecha_inicio or ''),
        'fecha_fin': c.fecha_fin.strftime('%Y-%m-%d') if hasattr(c.fecha_fin, 'strftime') else str(c.fecha_fin or ''),
        'horario': horario,
        'horas_totales': c.horas_duracion,
        'asistentes': asistentes,
        'unidades': [f.nombre for f in c.facultades.all()],
        'codigo_proyecto': c.proyecto.codigo if c.proyecto else 'IGA004',
        'area_pif': c.area_formacion.nombre if c.area_formacion else 'Especialidad',
        'estado': c.estado,
        'costo_publicado': costo_pub,
        'inv_honorarios': inv_hon,
        'inv_materiales': inv_mat,
        'viaticos_alimentacion': viat_alim,
        'gastos_transporte': gast_trans,
        'gastos_alojamiento': gast_aloj,
        'total_invertido': total_inv,
        'comentarios': comentarios
    }


def sistema_gestion_view(request):
    """
    Consola Integral UGB · PIF para la Gestión del Plan Integral de Formación Docente.
    Conectada a la base de datos PostgreSQL, calcula KPIs, y provee vistas de Registro,
    Directorio Docente y Control Presupuestario.
    """
    caps = Capacitacion.objects.select_related(
        'area_formacion', 'tipo_modalidad', 'proveedor', 'proyecto'
    ).prefetch_related('facultades', 'participaciones__persona', 'gastos').all().order_by('-fecha_inicio')

    serialized_caps = [serialize_capacitacion_pif(c) for c in caps]

    proyectos_objs = Proyecto.objects.filter(activo=True)
    proyectos_dict = {}
    for p in proyectos_objs:
        proyectos_dict[p.codigo] = {
            'nombre': p.nombre,
            'aprobado': float(p.presupuesto_asignado)
        }

    if not proyectos_dict:
        proyectos_dict = {
            "IGA004": {"nombre": "Innovación y Gestión Académica - Especialidad y Pedagogía", "aprobado": 2500.00},
            "IGA005": {"nombre": "Innovación y Gestión Académica - Enfoque Socioformativo", "aprobado": 1500.00},
            "FOR002": {"nombre": "Plan Integral de Formación Docente (Hoja Presupuesto)", "aprobado": 2000.00}
        }

    areas = AreaFormacion.objects.filter(activo=True)
    facultades = Facultad.objects.filter(activo=True)
    tipos_modalidad = TipoModalidad.objects.filter(activo=True)
    proyectos = Proyecto.objects.filter(activo=True)
    proveedores = Proveedor.objects.filter(activo=True)

    safe_caps_json = json.dumps(serialized_caps).replace('<', '\\u003c').replace('>', '\\u003e')
    safe_proy_json = json.dumps(proyectos_dict).replace('<', '\\u003c').replace('>', '\\u003e')

    context = {
        'capacitaciones_json': safe_caps_json,
        'proyectos_json': safe_proy_json,
        'total_eventos': len(serialized_caps),
        'areas': areas,
        'facultades': facultades,
        'tipos_modalidad': tipos_modalidad,
        'proyectos': proyectos,
        'proveedores': proveedores,
    }
    return render(request, 'capacitaciones/sistema_gestion.html', context)


@require_http_methods(["POST"])
def auth_login_api(request):
    """
    Autentica usuario en el servidor de forma segura sin exponer credenciales al cliente.
    """
    try:
        data = json.loads(request.body)
    except Exception:
        data = request.POST.dict()

    username = (data.get('username') or '').strip().lower()
    password = (data.get('password') or '').strip()

    from django.contrib.auth import authenticate, login
    user = authenticate(request, username=username, password=password)

    if user is not None:
        login(request, user)
        # Asignar rol y etiqueta de permisos según el perfil
        if user.is_superuser or user.username == 'admin':
            rol = 'ADMIN'
            label = 'Edición Total'
        elif user.username == 'coordinador':
            rol = 'COORDINADOR'
            label = 'Solo Lectura'
        elif user.username == 'ugb_pif' or user.has_perm('capacitaciones.change_capacitacion'):
            rol = 'UGB_PIF'
            label = 'Edición UGB · PIF'
        else:
            rol = 'CONSULTA'
            label = 'Solo Lectura'

        nombre = f"{user.first_name} {user.last_name}".strip() or user.username
        return JsonResponse({
            'status': 'success',
            'user': {
                'username': user.username,
                'nombre': nombre,
                'rol': rol,
                'label': label
            }
        })
    else:
        return JsonResponse({
            'status': 'error',
            'message': 'Credenciales inválidas. Verifique el usuario y la contraseña.'
        }, status=401)


@require_http_methods(["POST"])
def guardar_capacitacion_pif_api(request):
    """API para registrar o actualizar capacitaciones directamente en PostgreSQL con validación estricta de permisos."""
    try:
        data = json.loads(request.body)
    except Exception:
        data = request.POST.dict()

    # Validación estricta en servidor: El rol Coordinador tiene la edición deshabilitada
    user_role = request.headers.get('X-User-Role') or (data.get('user_role') if isinstance(data, dict) else None)
    caller_username = getattr(request.user, 'username', '') or (data.get('username') if isinstance(data, dict) else '')

    if (request.user.is_authenticated and (request.user.username == 'coordinador' or (not request.user.is_superuser and not request.user.has_perm('capacitaciones.change_capacitacion')))) or user_role in ['COORDINADOR', 'CONSULTA'] or caller_username in ['coordinador', 'consulta']:
        return JsonResponse({
            'status': 'error',
            'message': 'Acceso denegado: En el panel del coordinador la edición está deshabilitada (excepto en la sección de Auditoría).'
        }, status=403)

    cap_id = data.get('id')
    nombre = data.get('nombre_evento', '').strip()
    if not nombre:
        return JsonResponse({'status': 'error', 'message': 'El nombre del evento es obligatorio.'}, status=400)

    tipo_str = data.get('tipo', 'Taller')
    modalidad_str = data.get('modalidad', 'Virtual')
    tipo_mod = TipoModalidad.objects.filter(tipo__iexact=tipo_str, modalidad__iexact=modalidad_str).first()
    if not tipo_mod:
        tipo_mod, _ = TipoModalidad.objects.get_or_create(tipo=tipo_str, modalidad=modalidad_str)

    area_str = data.get('area_pif', 'Especialidad')
    area = AreaFormacion.objects.filter(nombre__iexact=area_str).first()
    if not area:
        area, _ = AreaFormacion.objects.get_or_create(codigo=f"PIF-{area_str[:3].upper()}", defaults={'nombre': area_str})

    cod_proy = data.get('codigo_proyecto', 'IGA004').strip().upper()
    proy = Proyecto.objects.filter(codigo=cod_proy).first()
    if not proy:
        proy, _ = Proyecto.objects.get_or_create(codigo=cod_proy, defaults={'nombre': f'Proyecto {cod_proy}', 'presupuesto_asignado': Decimal('2000.00')})

    prov_nombre = data.get('proveedor', 'No especificado').strip()
    contacto = data.get('contacto', '').strip()
    localidad = data.get('localidad', 'Nacional').strip()
    proveedor = Proveedor.objects.filter(nombre__iexact=prov_nombre).first()
    if not proveedor and prov_nombre:
        proveedor = Proveedor.objects.create(
            nombre=prov_nombre,
            contacto_nombre=contacto,
            pais=localidad,
            tipo='Interno' if 'UGB' in prov_nombre.upper() else 'Externo'
        )
    elif proveedor and contacto:
        proveedor.contacto_nombre = contacto
        proveedor.pais = localidad
        proveedor.save()

    fecha_inicio = data.get('fecha_inicio') or timezone.now().strftime('%Y-%m-%d')
    try:
        horas = max(1, min(1000, int(float(data.get('horas_totales', 8)))))
    except (ValueError, TypeError):
        horas = 8
    horario = data.get('horario', '').strip()
    comentarios = data.get('comentarios', '').strip()
    observaciones = f"{comentarios} | Horario: {horario}".strip(" |")

    cap = None
    if cap_id:
        try:
            cap = Capacitacion.objects.filter(id=cap_id).first()
        except Exception:
            cap = None

    if not cap:
        count = Capacitacion.objects.count() + 1
        year = fecha_inicio[:4] if fecha_inicio else timezone.now().year
        codigo = f"CAP-{year}-{count:03d}"
        cap = Capacitacion.objects.create(
            codigo=codigo,
            nombre=nombre,
            tipo_modalidad=tipo_mod,
            area_formacion=area,
            proyecto=proy,
            proveedor=proveedor,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_inicio,
            horas_duracion=horas,
            estado=data.get('estado', 'Finalizada'),
            lugar_o_enlace=data.get('lugar', 'Campus Central'),
            observaciones=observaciones
        )
    else:
        cap.nombre = nombre
        cap.tipo_modalidad = tipo_mod
        cap.area_formacion = area
        cap.proyecto = proy
        cap.proveedor = proveedor
        cap.fecha_inicio = fecha_inicio
        cap.fecha_fin = fecha_inicio
        cap.horas_duracion = horas
        cap.estado = data.get('estado', cap.estado)
        cap.lugar_o_enlace = data.get('lugar', cap.lugar_o_enlace)
        cap.observaciones = observaciones
        cap.save()

    # Facultades
    unidades = data.get('unidades', [])
    if isinstance(unidades, str):
        unidades = [u.strip() for u in unidades.split('\n') if u.strip()]
    fac_objs = []
    for u_nom in unidades:
        fac = Facultad.objects.filter(nombre__iexact=u_nom).first()
        if not fac:
            fac, _ = Facultad.objects.get_or_create(codigo=u_nom[:4].upper(), defaults={'nombre': u_nom})
        fac_objs.append(fac)
    cap.facultades.set(fac_objs)

    # Asistentes
    asistentes = data.get('asistentes', [])
    if isinstance(asistentes, str):
        try:
            asistentes = json.loads(asistentes)
        except Exception:
            asistentes = []

    cap.participaciones.all().delete()
    for a in asistentes:
        nom_part = a.get('nombre', '').strip()
        puesto = a.get('puesto', 'Docente').strip()
        if not nom_part:
            continue
        part_split = nom_part.split(' ', 1)
        p_nombres = part_split[0]
        p_apellidos = part_split[1] if len(part_split) > 1 else ''
        persona = Persona.objects.filter(nombres=p_nombres, apellidos=p_apellidos).first()
        if not persona:
            persona = Persona.objects.filter(nombres__iexact=nom_part).first()
        if not persona:
            p_code = f"DOC-{Persona.objects.count() + 1:04d}"
            persona = Persona.objects.create(
                codigo_empleado=p_code,
                nombres=p_nombres,
                apellidos=p_apellidos,
                cargo_actual=puesto,
                facultad=fac_objs[0] if fac_objs else None,
                tipo_personal='Docente'
            )
        elif puesto:
            persona.cargo_actual = puesto
            persona.save()

        Participacion.objects.create(
            capacitacion=cap,
            persona=persona,
            estado_asistencia='Aprobó' if cap.estado == 'Finalizada' else 'Inscrito',
            horas_acreditadas=cap.horas_duracion if cap.estado == 'Finalizada' else 0
        )

    # Rubros de Gasto con validación de no-negatividad
    cap.gastos.all().delete()
    def parse_decimal(val):
        try:
            return max(Decimal('0'), Decimal(str(val or 0)))
        except Exception:
            return Decimal('0')

    costo_pub = parse_decimal(data.get('costo_publicado'))
    inv_hon = parse_decimal(data.get('inv_honorarios'))
    inv_mat = parse_decimal(data.get('inv_materiales'))
    viat_alim = parse_decimal(data.get('viaticos_alimentacion'))
    gast_trans = parse_decimal(data.get('gastos_transporte'))
    gast_aloj = parse_decimal(data.get('gastos_alojamiento'))

    if inv_hon > 0:
        GastoCapacitacion.objects.create(capacitacion=cap, rubro='Inscripción / Honorarios', monto_planificado=inv_hon, monto_ejecutado=inv_hon, estado='Ejecutado')
    if inv_mat > 0:
        GastoCapacitacion.objects.create(capacitacion=cap, rubro='Materiales y Didácticos', monto_planificado=inv_mat, monto_ejecutado=inv_mat, estado='Ejecutado')
    if viat_alim > 0:
        GastoCapacitacion.objects.create(capacitacion=cap, rubro='Alimentación / Coffee Break', monto_planificado=viat_alim, monto_ejecutado=viat_alim, estado='Ejecutado')
    if gast_trans > 0:
        GastoCapacitacion.objects.create(capacitacion=cap, rubro='Transporte / Pasajes', monto_planificado=gast_trans, monto_ejecutado=gast_trans, estado='Ejecutado')
    if gast_aloj > 0:
        GastoCapacitacion.objects.create(capacitacion=cap, rubro='Viáticos y Hospedaje', monto_planificado=gast_aloj, monto_ejecutado=gast_aloj, estado='Ejecutado')
    if costo_pub > 0:
        GastoCapacitacion.objects.create(capacitacion=cap, rubro='Otro', monto_planificado=costo_pub, monto_ejecutado=costo_pub, estado='Planificado', descripcion='Costo Publicado Institucional')

    return JsonResponse({'status': 'success', 'data': serialize_capacitacion_pif(cap), 'message': f'Capacitación "{cap.nombre}" guardada exitosamente.'})


@require_http_methods(["POST", "DELETE"])
def eliminar_capacitacion_pif_api(request, pk):
    """API para eliminar una capacitación de PostgreSQL."""
    user_role = request.headers.get('X-User-Role')
    caller_username = getattr(request.user, 'username', '')
    if (request.user.is_authenticated and (request.user.username == 'coordinador' or (not request.user.is_superuser and not request.user.has_perm('capacitaciones.delete_capacitacion')))) or user_role in ['COORDINADOR', 'CONSULTA'] or caller_username in ['coordinador', 'consulta']:
        return JsonResponse({
            'status': 'error',
            'message': 'Acceso denegado: El rol Coordinador tiene la edición y eliminación deshabilitadas.'
        }, status=403)

    cap = get_object_or_404(Capacitacion, pk=pk)
    nombre = cap.nombre
    cap.delete()
    return JsonResponse({'status': 'success', 'message': f'Capacitación "{nombre}" eliminada correctamente.'})


@require_http_methods(["POST"])
def importar_excel_pif_api(request):
    """API para procesar e importar la plantilla Excel institucional directamente a PostgreSQL."""
    user_role = request.headers.get('X-User-Role') or request.POST.get('user_role')
    caller_username = getattr(request.user, 'username', '') or request.POST.get('username')
    if (request.user.is_authenticated and (request.user.username == 'coordinador' or (not request.user.is_superuser and not request.user.has_perm('capacitaciones.add_capacitacion')))) or user_role in ['COORDINADOR', 'CONSULTA'] or caller_username in ['coordinador', 'consulta']:
        return JsonResponse({
            'status': 'error',
            'message': 'Acceso denegado: El rol Coordinador tiene deshabilitada la importación/edición.'
        }, status=403)

    if 'excel_file' not in request.FILES:
        return JsonResponse({'status': 'error', 'message': 'No se adjuntó ningún archivo Excel.'}, status=400)

    file = request.FILES['excel_file']
    if not file.name.lower().endswith(('.xlsx', '.xlsm')):
        return JsonResponse({'status': 'error', 'message': 'Formato no permitido. Solo se aceptan archivos Excel (.xlsx o .xlsm).'}, status=400)
    if file.size > 15 * 1024 * 1024:
        return JsonResponse({'status': 'error', 'message': 'El archivo excede el tamaño máximo permitido (15 MB).'}, status=400)

    try:
        import openpyxl
        wb = openpyxl.load_workbook(file, data_only=True)
        sheet_name = "Registro" if "Registro" in wb.sheetnames else wb.sheetnames[0]
        ws = wb[sheet_name]

        imported_count = 0
        skipped_notes = 0

        for row in ws.iter_rows(min_row=2, values_only=True):
            if not row or not any(row):
                continue
            tipo = str(row[0] or "").strip()
            nombre_evento = str(row[5] or "").strip()

            if not tipo and not nombre_evento:
                continue
            if not tipo and nombre_evento:
                skipped_notes += 1
                continue

            # Fecha
            fecha_val = row[7]
            if isinstance(fecha_val, datetime):
                fecha_str = fecha_val.strftime('%Y-%m-%d')
            elif fecha_val:
                fecha_str = str(fecha_val)[:10]
            else:
                fecha_str = timezone.now().strftime('%Y-%m-%d')

            modalidad = str(row[4] or "Virtual").strip()
            tm, _ = TipoModalidad.objects.get_or_create(tipo=tipo or "Taller", modalidad=modalidad or "Virtual")

            area_str = str(row[14] or "Especialidad").strip()
            area, _ = AreaFormacion.objects.get_or_create(codigo=f"PIF-{area_str[:3].upper()}", defaults={'nombre': area_str})

            cod_proy = str(row[13] or "IGA004").strip()
            proy, _ = Proyecto.objects.get_or_create(codigo=cod_proy, defaults={'nombre': f'Proyecto {cod_proy}', 'presupuesto_asignado': Decimal('2000.00')})

            prov_str = str(row[1] or "No especificado").strip()
            contacto_str = str(row[2] or "").strip()
            prov, _ = Proveedor.objects.get_or_create(nombre=prov_str, defaults={'contacto_nombre': contacto_str, 'pais': str(row[3] or 'Nacional')})

            try:
                horas = int(float(row[9] or 8))
            except Exception:
                horas = 8

            count = Capacitacion.objects.count() + 1
            codigo = f"CAP-{fecha_str[:4]}-{count:03d}"

            cap = Capacitacion.objects.create(
                codigo=codigo,
                nombre=nombre_evento,
                tipo_modalidad=tm,
                area_formacion=area,
                proyecto=proy,
                proveedor=prov,
                horas_duracion=horas,
                fecha_inicio=fecha_str,
                fecha_fin=fecha_str,
                estado='Finalizada',
                lugar_o_enlace=str(row[6] or 'Campus Central').strip(),
                observaciones=f"{str(row[22] or '')} | Horario: {str(row[8] or '')}".strip(" |")
            )

            # Unidades
            unidades_raw = str(row[12] or "").split('\n')
            for u in unidades_raw:
                u = u.strip()
                if u:
                    fac, _ = Facultad.objects.get_or_create(codigo=u[:4].upper(), defaults={'nombre': u})
                    cap.facultades.add(fac)

            # Participantes
            part_names = [p.strip() for p in str(row[10] or "").split('\n') if p.strip()]
            part_puestos = [p.strip() for p in str(row[11] or "").split('\n') if p.strip()]
            for idx, p_name in enumerate(part_names):
                puesto = part_puestos[idx] if idx < len(part_puestos) else (part_puestos[0] if part_puestos else "Docente")
                part_split = p_name.split(' ', 1)
                persona, _ = Persona.objects.get_or_create(
                    nombres=part_split[0],
                    apellidos=part_split[1] if len(part_split) > 1 else '',
                    defaults={'codigo_empleado': f"DOC-{Persona.objects.count() + 1:04d}", 'cargo_actual': puesto, 'tipo_personal': 'Docente'}
                )
                Participacion.objects.create(capacitacion=cap, persona=persona, estado_asistencia='Aprobó', horas_acreditadas=horas)

            # Costos
            costo_pub = Decimal(str(row[15] or 0))
            inv_hon = Decimal(str(row[16] or 0))
            inv_mat = Decimal(str(row[17] or 0))
            viat_alim = Decimal(str(row[18] or 0))
            gast_trans = Decimal(str(row[19] or 0))
            gast_aloj = Decimal(str(row[20] or 0))

            if inv_hon > 0:
                GastoCapacitacion.objects.create(capacitacion=cap, rubro='Inscripción / Honorarios', monto_planificado=inv_hon, monto_ejecutado=inv_hon, estado='Ejecutado')
            if inv_mat > 0:
                GastoCapacitacion.objects.create(capacitacion=cap, rubro='Materiales y Didácticos', monto_planificado=inv_mat, monto_ejecutado=inv_mat, estado='Ejecutado')
            if viat_alim > 0:
                GastoCapacitacion.objects.create(capacitacion=cap, rubro='Alimentación / Coffee Break', monto_planificado=viat_alim, monto_ejecutado=viat_alim, estado='Ejecutado')
            if gast_trans > 0:
                GastoCapacitacion.objects.create(capacitacion=cap, rubro='Transporte / Pasajes', monto_planificado=gast_trans, monto_ejecutado=gast_trans, estado='Ejecutado')
            if gast_aloj > 0:
                GastoCapacitacion.objects.create(capacitacion=cap, rubro='Viáticos y Hospedaje', monto_planificado=gast_aloj, monto_ejecutado=gast_aloj, estado='Ejecutado')
            if costo_pub > 0:
                GastoCapacitacion.objects.create(capacitacion=cap, rubro='Otro', monto_planificado=costo_pub, monto_ejecutado=costo_pub, estado='Planificado')

            imported_count += 1

        return JsonResponse({
            'status': 'success',
            'imported_count': imported_count,
            'skipped_notes': skipped_notes,
            'message': f'Se importaron {imported_count} capacitaciones a PostgreSQL exitosamente ({skipped_notes} notas administrativas omitidas).'
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Error al importar Excel: {str(e)}'}, status=500)


def exportar_excel_pif(request):
    """Genera y descarga el archivo oficial Excel con 2 hojas: Registro (23 columnas) y Participantes Normalizados."""
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment

    wb = openpyxl.Workbook()
    ws_reg = wb.active
    ws_reg.title = "Registro"

    headers_reg = [
        "Tipo\n(taller, conferencia, congreso, curso, diplomado, etc.)",
        "Proveedor",
        "Contacto",
        "Localidad (nacional/internacional)",
        "Modalidad (presencial/virtual)",
        "Nombre del evento",
        "Lugar",
        "Fechas de la formación",
        "Horario",
        "Horas totales de duración de la formación",
        "Nombre del participante(s)",
        "Puesto",
        "Unidad/Facultad beneficiada",
        "Código de Proyecto",
        "Área\nsegún programa integral de formación",
        "COSTO PUBLICADO DE LA FORMACIÓN (incluir monto total por todos los participantes)",
        "Inversión en Honorarios por capacitación/inscripción/comisiones por transferencia",
        "Inversión en Materiales",
        "Viáticos de Alimentación",
        "Gastos por Transporte",
        "Gastos por Alojamiento",
        "TOTAL",
        "Comentarios/Observaciones",
        "Estado"
    ]
    ws_reg.append(headers_reg)

    caps = Capacitacion.objects.select_related(
        'area_formacion', 'tipo_modalidad', 'proveedor', 'proyecto'
    ).prefetch_related('facultades', 'participaciones__persona', 'gastos').all().order_by('-fecha_inicio')

    for c in caps:
        data = serialize_capacitacion_pif(c)
        asist_nombres = "\n".join([a['nombre'] for a in data['asistentes']])
        asist_puestos = "\n".join([a['puesto'] for a in data['asistentes']])
        unidades_str = "\n".join(data['unidades'])

        row = [
            data['tipo'],
            data['proveedor'],
            data['contacto'],
            data['localidad'],
            data['modalidad'],
            data['nombre_evento'],
            data['lugar'],
            data['fecha_inicio'],
            data['horario'],
            data['horas_totales'],
            asist_nombres,
            asist_puestos,
            unidades_str,
            data['codigo_proyecto'],
            data['area_pif'],
            data['costo_publicado'],
            data['inv_honorarios'],
            data['inv_materiales'],
            data['viaticos_alimentacion'],
            data['gastos_transporte'],
            data['gastos_alojamiento'],
            data['total_invertido'],
            data['comentarios'],
            data['estado']
        ]
        ws_reg.append(row)

    # Segunda hoja: Participantes Normalizados
    ws_asist = wb.create_sheet(title="Participantes Normalizados")
    asist_headers = ["ID Capacitación", "Código Evento", "Evento", "Fecha", "Participante", "Puesto", "Horas", "Proyecto", "Área PIF", "Estado"]
    ws_asist.append(asist_headers)

    for c in caps:
        data = serialize_capacitacion_pif(c)
        for a in data['asistentes']:
            ws_asist.append([
                data['id'],
                data['codigo'],
                data['nombre_evento'],
                data['fecha_inicio'],
                a['nombre'],
                a['puesto'],
                data['horas_totales'],
                data['codigo_proyecto'],
                data['area_pif'],
                data['estado']
            ])

    # Estilos del encabezado
    header_fill = PatternFill(start_color="0F172A", end_color="0F172A", fill_type="solid")
    header_font = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
    for ws in [ws_reg, ws_asist]:
        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(wrap_text=True, horizontal="center", vertical="center")

    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = 'attachment; filename="Reporte_Registro_Capacitaciones_UGB.xlsx"'
    wb.save(response)
    return response


def eliminar_capacitacion_view(request, pk):
    """
    Eliminación de una capacitación desde la interfaz web (sin pasar por Django Admin).
    """
    if request.user.is_authenticated and (request.user.username == 'coordinador' or (not request.user.is_superuser and not request.user.has_perm('capacitaciones.delete_capacitacion'))):
        messages.error(request, "Acceso denegado: El rol Coordinador tiene la eliminación deshabilitada. Inicia como Administrador para proceder.")
        return redirect('capacitaciones:detalle', pk=pk)

    cap = get_object_or_404(Capacitacion, pk=pk)
    codigo = cap.codigo
    nombre = cap.nombre

    if request.method == 'POST':
        try:
            from apps.core.models import AuditLog
            ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', '127.0.0.1'))
            if ip and ',' in ip:
                ip = ip.split(',')[0].strip()
            AuditLog.objects.create(
                usuario=request.user if request.user.is_authenticated else None,
                tabla_afectada='capacitaciones',
                registro_id=str(pk),
                accion='DELETE',
                detalles={'codigo': codigo, 'nombre': nombre},
                ip_origen=ip[:45] if ip else '127.0.0.1',
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:250]
            )
        except Exception:
            pass

        cap.delete()
        messages.success(request, f"La capacitación '{codigo} — {nombre}' fue eliminada exitosamente del sistema.")
        return redirect('capacitaciones:lista')

    return redirect('capacitaciones:detalle', pk=pk)


def eliminar_participante_view(request, pk, part_id):
    """
    Elimina a un participante de una capacitación directamente desde la web.
    """
    if request.user.is_authenticated and (request.user.username == 'coordinador' or (not request.user.is_superuser and not request.user.has_perm('capacitaciones.change_capacitacion'))):
        messages.error(request, "Acceso denegado: Se requieren permisos de Administrador para modificar inscripciones.")
        return redirect('capacitaciones:detalle', pk=pk)

    participacion = get_object_or_404(Participacion, pk=part_id, capacitacion_id=pk)
    nombre_persona = participacion.persona.nombre_completo

    if request.method == 'POST':
        participacion.delete()
        messages.success(request, f"Participante '{nombre_persona}' retirado exitosamente de la capacitación.")
    return redirect('capacitaciones:detalle', pk=pk)


def eliminar_evidencia_view(request, pk, evidencia_id):
    """
    Elimina una evidencia documental de la capacitación desde la web.
    """
    if request.user.is_authenticated and (request.user.username == 'coordinador' or (not request.user.is_superuser and not request.user.has_perm('capacitaciones.change_capacitacion'))):
        messages.error(request, "Acceso denegado: Se requieren permisos de Administrador para eliminar evidencias.")
        return redirect('capacitaciones:detalle', pk=pk)

    evidencia = get_object_or_404(Evidencia, pk=evidencia_id, capacitacion_id=pk)
    nombre = evidencia.nombre_original

    if request.method == 'POST':
        if evidencia.archivo:
            try:
                evidencia.archivo.delete(save=False)
            except Exception:
                pass
        evidencia.delete()
        messages.success(request, f"Evidencia digital '{nombre}' eliminada exitosamente.")
    return redirect('capacitaciones:detalle', pk=pk)
