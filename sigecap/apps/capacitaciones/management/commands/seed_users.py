import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Permission

class Command(BaseCommand):
    help = "Crea los 3 usuarios y roles oficiales del sistema SIGECAP: admin, coordinador y consulta."

    def handle(self, *args, **options):
        # 1. Admin
        admin_user, created_admin = User.objects.get_or_create(username='admin')
        admin_user.set_password('admin2026')
        admin_user.is_superuser = True
        admin_user.is_staff = True
        admin_user.first_name = 'Administrador'
        admin_user.last_name = 'Gestión Académica'
        admin_user.email = 'admin@institucion.edu'
        admin_user.save()
        self.stdout.write(self.style.SUCCESS(f"[OK] Usuario Administrador {'creado' if created_admin else 'actualizado'}: admin / admin2026 (Control Total)"))

        # 2. Coordinador
        coord_user, created_coord = User.objects.get_or_create(username='coordinador')
        coord_user.set_password('coord2026')
        coord_user.is_superuser = False
        coord_user.is_staff = True
        coord_user.first_name = 'Coordinador'
        coord_user.last_name = 'PIF / Capacitaciones'
        coord_user.email = 'coordinador@institucion.edu'
        coord_user.save()

        # Permisos para coordinador: Edición deshabilitada en capacitaciones, personas, catálogos y costos (solo lectura).
        # En la sección de Auditoría (core.AuditLog), mantiene permisos para ver y gestionar la bitácora.
        coord_view_perms = Permission.objects.filter(
            content_type__app_label__in=['capacitaciones', 'personas', 'catalogos', 'costos'],
            codename__startswith='view'
        )
        coord_audit_perms = Permission.objects.filter(
            content_type__app_label='core'
        )
        coord_user.user_permissions.set(list(coord_view_perms) + list(coord_audit_perms))
        self.stdout.write(self.style.SUCCESS(f"[OK] Usuario Coordinacion {'creado' if created_coord else 'actualizado'}: coordinador (Solo Lectura general, Auditoría habilitada)"))

        # 3. Consulta
        consulta_user, created_cons = User.objects.get_or_create(username='consulta')
        consulta_user.set_password('lectura2026')
        consulta_user.is_superuser = False
        consulta_user.is_staff = True
        consulta_user.first_name = 'Auditor'
        consulta_user.last_name = 'Consulta y Lectura'
        consulta_user.email = 'consulta@institucion.edu'
        consulta_user.save()

        view_perms = Permission.objects.filter(
            content_type__app_label__in=['capacitaciones', 'personas', 'catalogos', 'costos'],
            codename__startswith='view'
        )
        consulta_user.user_permissions.set(view_perms)
        self.stdout.write(self.style.SUCCESS(f"[OK] Usuario Consulta {'creado' if created_cons else 'actualizado'}: consulta (Solo Lectura)"))

        # 4. Usuario UGB · PIF (Gestor específico del panel UGB · PIF sin ampliar permisos a otros paneles)
        ugb_user, created_ugb = User.objects.get_or_create(username='ugb_pif')
        ugb_user.set_password('ugbpif2026')
        ugb_user.is_superuser = False
        ugb_user.is_staff = True
        ugb_user.first_name = 'Gestor'
        ugb_user.last_name = 'UGB · PIF'
        ugb_user.email = 'ugbpif@institucion.edu'
        ugb_user.save()

        # Permisos estrictos: Edición y gestión en el panel de capacitaciones UGB · PIF únicamente
        ugb_perms = Permission.objects.filter(content_type__app_label='capacitaciones')
        ugb_user.user_permissions.set(ugb_perms)
        self.stdout.write(self.style.SUCCESS(f"[OK] Usuario UGB · PIF {'creado' if created_ugb else 'actualizado'}: ugb_pif (Edición en panel UGB · PIF sin acceso de edición a otros paneles)"))
