from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.db.models import Count, Sum, Avg, ProtectedError
from django.http import JsonResponse
from apps.capacitaciones.models import Capacitacion, Participacion, EncuestaSatisfaccion
from apps.personas.models import Persona
from apps.catalogos.models import Facultad, AreaFormacion, TipoModalidad, Proyecto, Proveedor
from apps.costos.models import GastoCapacitacion
from apps.core.models import AuditLog

def dashboard_view(request):
    """
    Vista del Dashboard Principal de SIGECAP (Inspirado en Prototipo Stitch).
    Calcula en tiempo real los KPIs institucionales, métricas de satisfacción y datos para las gráficas.
    """
    # 5 KPIs Principales
    total_capacitaciones = Capacitacion.objects.count()
    total_participantes_inscritos = Participacion.objects.count()
    total_aprobados = Participacion.objects.filter(estado_asistencia='Aprobó').count()
    
    total_docentes_capacitados = Persona.objects.filter(
        participaciones__estado_asistencia='Aprobó', 
        tipo_personal__in=['Docente', 'Ambos']
    ).distinct().count()

    total_horas_impartidas = Capacitacion.objects.filter(
        estado__in=['En Curso', 'Finalizada']
    ).aggregate(total=Sum('horas_duracion'))['total'] or 0

    presupuesto_ejecutado = GastoCapacitacion.objects.filter(
        estado='Ejecutado'
    ).aggregate(total=Sum('monto_ejecutado'))['total'] or 0

    # Métricas de Satisfacción
    encuestas = EncuestaSatisfaccion.objects.all()
    total_encuestas = encuestas.count()
    if total_encuestas > 0:
        promedios = [e.puntaje_general for e in encuestas]
        satisfaccion_promedio = round(sum(promedios) / len(promedios), 1)
        pct_satisfaccion = int((satisfaccion_promedio / 5.0) * 100)
    else:
        satisfaccion_promedio = 4.8
        pct_satisfaccion = 96

    # Capacitaciones Recientes o En Curso
    capacitaciones_recientes = Capacitacion.objects.select_related(
        'area_formacion', 'tipo_modalidad'
    ).all()[:6]

    # Distribución por Áreas Formativas
    areas_chart = AreaFormacion.objects.annotate(
        num_capacitaciones=Count('capacitaciones')
    ).values('nombre', 'num_capacitaciones')

    area_labels = [a['nombre'] for a in areas_chart]
    area_values = [a['num_capacitaciones'] for a in areas_chart]

    context = {
        'total_capacitaciones': total_capacitaciones,
        'total_participantes': total_participantes_inscritos,
        'total_aprobados': total_aprobados,
        'total_docentes': total_docentes_capacitados,
        'total_horas': total_horas_impartidas,
        'presupuesto_ejecutado': presupuesto_ejecutado,
        'satisfaccion_promedio': satisfaccion_promedio,
        'pct_satisfaccion': pct_satisfaccion,
        'total_encuestas': total_encuestas,
        'capacitaciones_recientes': capacitaciones_recientes,
        'area_labels': area_labels,
        'area_values': area_values,
    }
    return render(request, 'dashboard.html', context)


def registrar_log(request, accion, tabla, registro_id, detalles=None):
    """Registra eventos en la bitácora de auditoría inmutable."""
    try:
        ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', '127.0.0.1'))
        if ip and ',' in ip:
            ip = ip.split(',')[0].strip()
        AuditLog.objects.create(
            usuario=request.user if request.user.is_authenticated else None,
            tabla_afectada=tabla,
            registro_id=str(registro_id),
            accion=accion,
            detalles=detalles or {},
            ip_origen=ip[:45] if ip else '127.0.0.1',
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:250]
        )
    except Exception:
        pass


def panel_administracion_view(request):
    """
    Centro Integral de Administración Web de SIGECAP:
    Permite gestionar catálogos maestros, usuarios, roles, capacitaciones
    y bitácora de auditoría sin necesidad de acceder al panel externo de Django Admin.
    """
    tab_activa = request.GET.get('tab', 'catalogos')
    subtab = request.GET.get('subtab', 'facultades')

    facultades = Facultad.objects.all().order_by('codigo')
    areas = AreaFormacion.objects.all().order_by('codigo')
    tipos_modalidad = TipoModalidad.objects.all().order_by('tipo', 'modalidad')
    proveedores = Proveedor.objects.all().order_by('nombre')
    proyectos = Proyecto.objects.all().order_by('codigo')
    usuarios = User.objects.all().order_by('-is_superuser', 'username')
    capacitaciones = Capacitacion.objects.select_related(
        'area_formacion', 'tipo_modalidad', 'proveedor'
    ).annotate(total_inscritos=Count('participaciones')).order_by('-fecha_inicio')
    auditorias = AuditLog.objects.select_related('usuario').all().order_by('-fecha_hora')[:100]

    context = {
        'tab_activa': tab_activa,
        'subtab': subtab,
        'facultades': facultades,
        'areas': areas,
        'tipos_modalidad': tipos_modalidad,
        'proveedores': proveedores,
        'proyectos': proyectos,
        'usuarios': usuarios,
        'capacitaciones': capacitaciones,
        'auditorias': auditorias,
        'total_facultades': facultades.count(),
        'total_areas': areas.count(),
        'total_modalidades': tipos_modalidad.count(),
        'total_proveedores': proveedores.count(),
        'total_proyectos': proyectos.count(),
        'total_usuarios': usuarios.count(),
        'total_capacitaciones': capacitaciones.count(),
    }
    return render(request, 'administracion/panel.html', context)


def catalogo_crud_view(request, modelo, accion):
    """
    CRUD completo para los 5 catálogos maestros desde la interfaz web.
    """
    if request.method != 'POST':
        return redirect('core:panel_administracion')

    tab_redirect = f"tab=catalogos&subtab={modelo}s"

    try:
        # 1. FACULTADES
        if modelo == 'facultad':
            if accion == 'crear':
                codigo = request.POST.get('codigo', '').strip()
                nombre = request.POST.get('nombre', '').strip()
                descripcion = request.POST.get('descripcion', '').strip()
                if codigo and nombre:
                    obj = Facultad.objects.create(codigo=codigo, nombre=nombre, descripcion=descripcion)
                    registrar_log(request, 'INSERT', 'facultades', obj.id, {'codigo': codigo, 'nombre': nombre})
                    messages.success(request, f"Facultad '{nombre}' creada exitosamente.")
            elif accion == 'editar':
                obj_id = request.POST.get('id')
                obj = get_object_or_404(Facultad, pk=obj_id)
                obj.codigo = request.POST.get('codigo', obj.codigo).strip()
                obj.nombre = request.POST.get('nombre', obj.nombre).strip()
                obj.descripcion = request.POST.get('descripcion', '').strip()
                obj.activo = request.POST.get('activo') == 'on'
                obj.save()
                registrar_log(request, 'UPDATE', 'facultades', obj.id, {'codigo': obj.codigo, 'nombre': obj.nombre})
                messages.success(request, f"Facultad '{obj.nombre}' actualizada correctamente.")
            elif accion == 'eliminar':
                obj_id = request.POST.get('id')
                obj = get_object_or_404(Facultad, pk=obj_id)
                nom = obj.nombre
                registrar_log(request, 'DELETE', 'facultades', obj.id, {'codigo': obj.codigo, 'nombre': nom})
                obj.delete()
                messages.success(request, f"Facultad '{nom}' eliminada exitosamente.")

        # 2. ÁREAS FORMATIVAS
        elif modelo == 'area':
            tab_redirect = "tab=catalogos&subtab=areas"
            if accion == 'crear':
                codigo = request.POST.get('codigo', '').strip()
                nombre = request.POST.get('nombre', '').strip()
                descripcion = request.POST.get('descripcion', '').strip()
                if codigo and nombre:
                    obj = AreaFormacion.objects.create(codigo=codigo, nombre=nombre, descripcion=descripcion)
                    registrar_log(request, 'INSERT', 'areas_formacion', obj.id, {'codigo': codigo, 'nombre': nombre})
                    messages.success(request, f"Área de Formación '{nombre}' creada exitosamente.")
            elif accion == 'editar':
                obj_id = request.POST.get('id')
                obj = get_object_or_404(AreaFormacion, pk=obj_id)
                obj.codigo = request.POST.get('codigo', obj.codigo).strip()
                obj.nombre = request.POST.get('nombre', obj.nombre).strip()
                obj.descripcion = request.POST.get('descripcion', '').strip()
                obj.activo = request.POST.get('activo') == 'on'
                obj.save()
                registrar_log(request, 'UPDATE', 'areas_formacion', obj.id, {'codigo': obj.codigo, 'nombre': obj.nombre})
                messages.success(request, f"Área '{obj.nombre}' actualizada correctamente.")
            elif accion == 'eliminar':
                obj_id = request.POST.get('id')
                obj = get_object_or_404(AreaFormacion, pk=obj_id)
                nom = obj.nombre
                registrar_log(request, 'DELETE', 'areas_formacion', obj.id, {'codigo': obj.codigo, 'nombre': nom})
                obj.delete()
                messages.success(request, f"Área '{nom}' eliminada exitosamente.")

        # 3. TIPOS Y MODALIDADES
        elif modelo == 'tipo_modalidad':
            tab_redirect = "tab=catalogos&subtab=modalidades"
            if accion == 'crear':
                tipo = request.POST.get('tipo', '').strip()
                modalidad = request.POST.get('modalidad', '').strip()
                descripcion = request.POST.get('descripcion', '').strip()
                if tipo and modalidad:
                    obj = TipoModalidad.objects.create(tipo=tipo, modalidad=modalidad, descripcion=descripcion)
                    registrar_log(request, 'INSERT', 'tipos_modalidad', obj.id, {'tipo': tipo, 'modalidad': modalidad})
                    messages.success(request, f"Tipo/Modalidad '{tipo} ({modalidad})' registrado exitosamente.")
            elif accion == 'editar':
                obj_id = request.POST.get('id')
                obj = get_object_or_404(TipoModalidad, pk=obj_id)
                obj.tipo = request.POST.get('tipo', obj.tipo).strip()
                obj.modalidad = request.POST.get('modalidad', obj.modalidad).strip()
                obj.descripcion = request.POST.get('descripcion', '').strip()
                obj.activo = request.POST.get('activo') == 'on'
                obj.save()
                registrar_log(request, 'UPDATE', 'tipos_modalidad', obj.id, {'tipo': obj.tipo, 'modalidad': obj.modalidad})
                messages.success(request, f"Registro '{obj.tipo} ({obj.modalidad})' actualizado.")
            elif accion == 'eliminar':
                obj_id = request.POST.get('id')
                obj = get_object_or_404(TipoModalidad, pk=obj_id)
                nom = f"{obj.tipo} ({obj.modalidad})"
                registrar_log(request, 'DELETE', 'tipos_modalidad', obj.id, {'nombre': nom})
                obj.delete()
                messages.success(request, f"Tipo/Modalidad '{nom}' eliminado exitosamente.")

        # 4. PROVEEDORES
        elif modelo == 'proveedor':
            tab_redirect = "tab=catalogos&subtab=proveedores"
            if accion == 'crear':
                nombre = request.POST.get('nombre', '').strip()
                tipo = request.POST.get('tipo', 'Externo')
                codigo = request.POST.get('codigo', '').strip() or None
                pais = request.POST.get('pais', 'Local').strip()
                contacto_nombre = request.POST.get('contacto_nombre', '').strip()
                contacto_email = request.POST.get('contacto_email', '').strip()
                contacto_telefono = request.POST.get('contacto_telefono', '').strip()
                if nombre:
                    obj = Proveedor.objects.create(
                        nombre=nombre, tipo=tipo, codigo=codigo, pais=pais,
                        contacto_nombre=contacto_nombre, contacto_email=contacto_email,
                        contacto_telefono=contacto_telefono
                    )
                    registrar_log(request, 'INSERT', 'proveedores', obj.id, {'nombre': nombre})
                    messages.success(request, f"Proveedor '{nombre}' registrado exitosamente.")
            elif accion == 'editar':
                obj_id = request.POST.get('id')
                obj = get_object_or_404(Proveedor, pk=obj_id)
                obj.nombre = request.POST.get('nombre', obj.nombre).strip()
                obj.tipo = request.POST.get('tipo', obj.tipo)
                obj.pais = request.POST.get('pais', obj.pais).strip()
                obj.contacto_nombre = request.POST.get('contacto_nombre', '').strip()
                obj.contacto_email = request.POST.get('contacto_email', '').strip()
                obj.contacto_telefono = request.POST.get('contacto_telefono', '').strip()
                obj.activo = request.POST.get('activo') == 'on'
                obj.save()
                registrar_log(request, 'UPDATE', 'proveedores', obj.id, {'nombre': obj.nombre})
                messages.success(request, f"Proveedor '{obj.nombre}' actualizado.")
            elif accion == 'eliminar':
                obj_id = request.POST.get('id')
                obj = get_object_or_404(Proveedor, pk=obj_id)
                nom = obj.nombre
                registrar_log(request, 'DELETE', 'proveedores', obj.id, {'nombre': nom})
                obj.delete()
                messages.success(request, f"Proveedor '{nom}' eliminado exitosamente.")

        # 5. PROYECTOS / FONDOS
        elif modelo == 'proyecto':
            tab_redirect = "tab=catalogos&subtab=proyectos"
            if accion == 'crear':
                codigo = request.POST.get('codigo', '').strip()
                nombre = request.POST.get('nombre', '').strip()
                fuente = request.POST.get('fuente_financiamiento', '').strip()
                presupuesto = request.POST.get('presupuesto_asignado') or 0
                if codigo and nombre:
                    obj = Proyecto.objects.create(
                        codigo=codigo, nombre=nombre, fuente_financiamiento=fuente,
                        presupuesto_asignado=presupuesto
                    )
                    registrar_log(request, 'INSERT', 'proyectos', obj.id, {'codigo': codigo, 'nombre': nombre})
                    messages.success(request, f"Proyecto/Fondo '{nombre}' creado exitosamente.")
            elif accion == 'editar':
                obj_id = request.POST.get('id')
                obj = get_object_or_404(Proyecto, pk=obj_id)
                obj.codigo = request.POST.get('codigo', obj.codigo).strip()
                obj.nombre = request.POST.get('nombre', obj.nombre).strip()
                obj.fuente_financiamiento = request.POST.get('fuente_financiamiento', '').strip()
                obj.presupuesto_asignado = request.POST.get('presupuesto_asignado') or obj.presupuesto_asignado
                obj.activo = request.POST.get('activo') == 'on'
                obj.save()
                registrar_log(request, 'UPDATE', 'proyectos', obj.id, {'codigo': obj.codigo, 'nombre': obj.nombre})
                messages.success(request, f"Proyecto '{obj.nombre}' actualizado.")
            elif accion == 'eliminar':
                obj_id = request.POST.get('id')
                obj = get_object_or_404(Proyecto, pk=obj_id)
                nom = obj.nombre
                registrar_log(request, 'DELETE', 'proyectos', obj.id, {'nombre': nom})
                obj.delete()
                messages.success(request, f"Proyecto '{nom}' eliminado exitosamente.")

    except ProtectedError as pe:
        messages.error(request, f"No se puede eliminar este registro porque está vinculado a cursos o registros activos.")
    except Exception as e:
        messages.error(request, f"Error al procesar la operación: {str(e)}")

    return redirect(f"{redirect('core:panel_administracion').url}?{tab_redirect}")


def usuario_crud_view(request, accion):
    """
    CRUD completo de usuarios y asignación de roles desde la web.
    """
    if request.method != 'POST':
        return redirect(f"{redirect('core:panel_administracion').url}?tab=usuarios")

    try:
        if accion == 'crear':
            username = request.POST.get('username', '').strip().lower()
            password = request.POST.get('password', '').strip()
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            email = request.POST.get('email', '').strip()
            rol = request.POST.get('rol', 'COORDINADOR')

            if not username or not password:
                messages.error(request, "El nombre de usuario y la contraseña son obligatorios.")
                return redirect(f"{redirect('core:panel_administracion').url}?tab=usuarios")

            if User.objects.filter(username=username).exists():
                messages.error(request, f"El usuario '{username}' ya existe.")
                return redirect(f"{redirect('core:panel_administracion').url}?tab=usuarios")

            is_super = (rol == 'ADMIN')
            is_stf = (rol in ['ADMIN', 'UGB_PIF', 'COORDINADOR'])

            user = User.objects.create_user(
                username=username,
                password=password,
                first_name=first_name,
                last_name=last_name,
                email=email,
                is_superuser=is_super,
                is_staff=is_stf
            )
            registrar_log(request, 'INSERT', 'auth_user', user.id, {'username': username, 'rol': rol})
            messages.success(request, f"Usuario '{username}' creado exitosamente con rol {rol}.")

        elif accion == 'editar':
            user_id = request.POST.get('user_id')
            user = get_object_or_404(User, pk=user_id)
            user.first_name = request.POST.get('first_name', user.first_name).strip()
            user.last_name = request.POST.get('last_name', user.last_name).strip()
            user.email = request.POST.get('email', user.email).strip()
            user.is_active = (request.POST.get('is_active') == 'on')

            rol = request.POST.get('rol')
            if rol:
                user.is_superuser = (rol == 'ADMIN')
                user.is_staff = (rol in ['ADMIN', 'UGB_PIF', 'COORDINADOR'])

            user.save()
            registrar_log(request, 'UPDATE', 'auth_user', user.id, {'username': user.username, 'rol': rol})
            messages.success(request, f"Usuario '{user.username}' actualizado correctamente.")

        elif accion == 'password':
            user_id = request.POST.get('user_id')
            nueva_pass = request.POST.get('nueva_password', '').strip()
            if not nueva_pass:
                messages.error(request, "La nueva contraseña no puede estar vacía.")
                return redirect(f"{redirect('core:panel_administracion').url}?tab=usuarios")

            user = get_object_or_404(User, pk=user_id)
            user.set_password(nueva_pass)
            user.save()
            registrar_log(request, 'UPDATE', 'auth_user', user.id, {'accion': 'reset_password'})
            messages.success(request, f"Contraseña actualizada para el usuario '{user.username}'.")

        elif accion == 'eliminar':
            user_id = request.POST.get('user_id')
            user = get_object_or_404(User, pk=user_id)

            if request.user.is_authenticated and request.user.id == user.id:
                messages.error(request, "No puedes eliminar tu propio usuario activo en sesión.")
                return redirect(f"{redirect('core:panel_administracion').url}?tab=usuarios")

            uname = user.username
            registrar_log(request, 'DELETE', 'auth_user', user.id, {'username': uname})
            user.delete()
            messages.success(request, f"Usuario '{uname}' eliminado exitosamente.")

    except Exception as e:
        messages.error(request, f"Error al procesar usuario: {str(e)}")

    return redirect(f"{redirect('core:panel_administracion').url}?tab=usuarios")


def cambiar_estado_capacitacion_view(request, pk):
    """Cambia el estado de una capacitación de 1 clic desde la web."""
    if request.method == 'POST':
        cap = get_object_or_404(Capacitacion, pk=pk)
        nuevo_estado = request.POST.get('nuevo_estado')
        if nuevo_estado in ['Planificada', 'En Curso', 'Finalizada', 'Cancelada']:
            estado_anterior = cap.estado
            cap.estado = nuevo_estado
            cap.save()
            registrar_log(request, 'UPDATE', 'capacitaciones', cap.id, {
                'codigo': cap.codigo, 'estado_anterior': estado_anterior, 'nuevo_estado': nuevo_estado
            })
            messages.success(request, f"Estado de '{cap.codigo}' actualizado a '{nuevo_estado}'.")
    return redirect(f"{redirect('core:panel_administracion').url}?tab=capacitaciones")


def conmutar_rol_web_view(request):
    """
    Conmutador rápido de sesión y permisos web:
    Permite iniciar sesión instantáneamente como Administrador, UGB · PIF o Coordinador.
    """
    if request.method == 'POST':
        username = request.POST.get('username', '').strip().lower()
        user = User.objects.filter(username=username).first()
        if user:
            login(request, user)
            messages.success(request, f"Sesión activa cambiada a: '{user.username.upper()}'. Permisos administrativos sincronizados.")
        else:
            messages.error(request, f"El usuario '{username}' no existe en el sistema.")

        next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or '/'
        return redirect(next_url)

    return redirect('/')
