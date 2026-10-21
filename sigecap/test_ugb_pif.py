import os
import json
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sigecap.settings')
django.setup()

from django.test import RequestFactory
from apps.capacitaciones.views import (
    sistema_gestion_view,
    guardar_capacitacion_pif_api,
    exportar_excel_pif,
    eliminar_capacitacion_pif_api
)
from apps.capacitaciones.models import Capacitacion

rf = RequestFactory()

print("--- 1. Probando renderizado de la Consola UGB · PIF ---")
req = rf.get('/capacitaciones/sistema-gestion/')
resp = sistema_gestion_view(req)
assert resp.status_code == 200, f"Error status: {resp.status_code}"
content = resp.content.decode('utf-8')
assert "UGB · PIF" in content, "Falta distintivo UGB · PIF"
assert "Sistema de Gestión de Registro de Capacitaciones" in content, "Falta título"
print("[OK] Vista sistema_gestion_view renderiza exitosamente con codigo 200 y contenido institucional.")

print("\n--- 2. Probando API guardar_capacitacion_pif_api en PostgreSQL ---")
new_data = {
    "tipo": "Curso",
    "modalidad": "Virtual",
    "localidad": "Nacional",
    "nombre_evento": "Curso de Inteligencia Artificial para la Docencia Universitaria",
    "proveedor": "Innovación y Gestión Académica - UGB",
    "contacto": "Ing. Carlos Roberto Martínez",
    "lugar": "Canvas UGB",
    "fecha_inicio": "2026-11-01",
    "horario": "Sábados 8:00 AM a 12:00 PM",
    "horas_totales": 30,
    "codigo_proyecto": "IGA004",
    "area_pif": "Pedagogía",
    "estado": "Planificada",
    "unidades": ["Facultad de Ciencia y Tecnología", "Facultad de Ingeniería y Arquitectura"],
    "asistentes": [
        {"nombre": "Docente 1", "puesto": "Docente Tiempo Completo"},
        {"nombre": "Docente 2", "puesto": "Coordinador de Cátedra"}
    ],
    "costo_publicado": 350.00,
    "inv_honorarios": 300.00,
    "inv_materiales": 50.00,
    "viaticos_alimentacion": 0.0,
    "gastos_transporte": 0.0,
    "gastos_alojamiento": 0.0,
    "comentarios": "Curso piloto para docentes UGB"
}
req_save = rf.post(
    '/capacitaciones/api/guardar-pif/',
    data=json.dumps(new_data),
    content_type='application/json'
)
resp_save = guardar_capacitacion_pif_api(req_save)
assert resp_save.status_code == 200, f"Error en guardar: {resp_save.status_code}"
data_saved = json.loads(resp_save.content)
assert data_saved.get('status') == 'success', f"Respuesta fallida: {data_saved}"
new_id = data_saved['data']['id']
print(f"[OK] Capacitacion guardada en PostgreSQL con ID: {new_id}")

print("\n--- 3. Probando exportacion a Excel oficial con 2 hojas ---")
req_export = rf.get('/capacitaciones/exportar-excel-pif/')
resp_export = exportar_excel_pif(req_export)
assert resp_export.status_code == 200, f"Error en exportar Excel: {resp_export.status_code}"
assert resp_export['Content-Type'] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
print(f"[OK] Archivo Excel generado correctamente (tamano: {len(resp_export.content)} bytes).")

print("\n--- 4. Probando API eliminar_capacitacion_pif_api en PostgreSQL ---")
req_del = rf.post(f'/capacitaciones/api/eliminar-pif/{new_id}/')
resp_del = eliminar_capacitacion_pif_api(req_del, pk=new_id)
assert resp_del.status_code == 200
assert not Capacitacion.objects.filter(id=new_id).exists(), "El registro deberia haber sido eliminado"
print("[OK] Capacitacion eliminada correctamente de PostgreSQL.")

print("\n=======================================================")
print("TODAS LAS PRUEBAS DE INTEGRACION PASARON EXITOSAMENTE!")
print("=======================================================")
