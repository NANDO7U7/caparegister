from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Facultad, AreaFormacion, TipoModalidad, Proyecto, Proveedor

def administracion_catalogos(request):
    """
    Vista de administración de catálogos institucionales.
    Inspirado en el prototipo Google Stitch de Administración de Catálogos.
    """
    if request.method == 'POST':
        tipo_catalogo = request.POST.get('tipo_catalogo')
        
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

    facultades = Facultad.objects.all().order_by('codigo')
    areas = AreaFormacion.objects.all().order_by('codigo')
    tipos_modalidad = TipoModalidad.objects.all().order_by('tipo', 'modalidad')
    proyectos = Proyecto.objects.all().order_by('codigo')
    proveedores = Proveedor.objects.all().order_by('nombre')

    context = {
        'facultades': facultades,
        'areas': areas,
        'tipos_modalidad': tipos_modalidad,
        'proyectos': proyectos,
        'proveedores': proveedores,
    }
    return render(request, 'catalogos/administracion.html', context)
