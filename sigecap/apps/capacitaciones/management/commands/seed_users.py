from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Comando retirado: no crea cuentas ni modifica permisos o contraseñas.'

    def handle(self, *args, **options):
        raise CommandError(
            'seed_users fue retirado por seguridad. Usa createsuperuser de forma '
            'interactiva y administra usuarios y permisos desde Django Admin. '
            'Consulta docs/seguridad.md. No se modificó ninguna cuenta.'
        )
