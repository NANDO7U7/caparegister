from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Facultad, AreaFormacion, TipoModalidad, Proyecto, Proveedor
from django.core.exceptions import PermissionDenied
from apps.core.permissions import can_view_catalogs, visible_catalog, require_administrative_permission

def administracion_catalogos(request):
    """
    Vista de administración de catálogos institucionales.
    Inspirado en el prototipo Google Stitch de Administración de Catálogos.
    """
    if request.method == 'POST':
        tipo_catalogo = request.POST.get('tipo_catalogo')
        model_name = {'facultad': 'facultad', 'area': 'areaformacion'}.get(tipo_catalogo)
        if not model_name:
            raise PermissionDenied
        require_administrative_permission(request.user, f'catalogos.add_{model_name}')
        
        if tipo_catalogo == 'facultad':
            codigo = request.POST.get('codigo')
            nombre = request.POST.get('nombre')
            descripcion = request.POST.get('descripcion')
            if codigo and nombre:
                Facultad.objects.create(codigo=codigo, nombre=nombre, descripcion=descripcion)
                messages.success(request, f"Facultad '{nombre}' creada exitosamente.")
                
        elif tipo_catalogo == 'area':
            codigo = request.POST.get('codigo')
            nombre = request.POST.get('nombre')
            descripcion = request.POST.get('descripcion')
            if codigo and nombre:
                AreaFormacion.objects.create(codigo=codigo, nombre=nombre, descripcion=descripcion)
                messages.success(request, f"Área de Formación '{nombre}' creada exitosamente.")
                
        return redirect('catalogos:administracion')

    if not can_view_catalogs(request.user):
        raise PermissionDenied
    facultades = visible_catalog(request.user, Facultad).order_by('codigo')
    areas = visible_catalog(request.user, AreaFormacion).order_by('codigo')
    tipos_modalidad = visible_catalog(request.user, TipoModalidad).order_by('tipo', 'modalidad')
    proyectos = visible_catalog(request.user, Proyecto).order_by('codigo')
    proveedores = visible_catalog(request.user, Proveedor).order_by('nombre')

    context = {
        'facultades': facultades,
        'areas': areas,
        'tipos_modalidad': tipos_modalidad,
        'proyectos': proyectos,
        'proveedores': proveedores,
    }
    return render(request, 'catalogos/administracion.html', context)
