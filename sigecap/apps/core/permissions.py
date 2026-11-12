"""Small authorization policy built on Django's model permissions."""
from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


CATALOG_MODELS = {
    'facultad': 'facultad', 'area': 'areaformacion',
    'tipo_modalidad': 'tipomodalidad', 'proveedor': 'proveedor', 'proyecto': 'proyecto',
}
CATALOG_ACTIONS = {'crear': 'add', 'editar': 'change', 'eliminar': 'delete'}


def is_administrator(user):
    return user.is_active and (user.is_superuser or user.is_staff)


def require_administrative_permission(user, permission):
    if not is_administrator(user) or not user.has_perm(permission):
        raise PermissionDenied


def administrative_permission_required(permission):
    def decorate(view):
        @login_required
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            require_administrative_permission(request.user, permission)
            return view(request, *args, **kwargs)
        return wrapped
    return decorate


def can_view_catalogs(user):
    return is_administrator(user) and any(
        user.has_perm(f'catalogos.view_{model}') for model in CATALOG_MODELS.values()
    )


def visible_catalog(user, model):
    query = model.objects.all()
    return query if user.has_perm(f'catalogos.view_{model._meta.model_name}') else query.none()


def catalog_get_or_create(request, model, **kwargs):
    lookup = {key: value for key, value in kwargs.items() if key != 'defaults'}
    try:
        return model.objects.get(**lookup), False
    except model.DoesNotExist:
        require_administrative_permission(request.user, f'catalogos.add_{model._meta.model_name}')
        return model.objects.get_or_create(**kwargs)


def record_get_or_create(request, model, **kwargs):
    lookup = {key: value for key, value in kwargs.items() if key != 'defaults'}
    try:
        return model.objects.get(**lookup), False
    except model.DoesNotExist:
        if not request.user.has_perm(f'{model._meta.app_label}.add_{model._meta.model_name}'):
            raise PermissionDenied
        return model.objects.get_or_create(**kwargs)


def pif_user_profile(user):
    can_create = user.has_perm('capacitaciones.add_capacitacion')
    can_edit = user.has_perm('capacitaciones.change_capacitacion')
    can_delete = user.has_perm('capacitaciones.delete_capacitacion')
    if user.is_superuser:
        role, label = 'ADMIN', 'Edición Total'
    elif can_create or can_edit or can_delete:
        role, label = 'UGB_PIF', 'Edición UGB · PIF'
    else:
        role, label = 'CONSULTA', 'Solo Lectura'
    return {'username': user.username, 'nombre': user.get_full_name() or user.username,
            'rol': role, 'label': label, 'can_create': can_create,
            'can_edit': can_edit, 'can_delete': can_delete}
