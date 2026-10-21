import { test, expect } from '@playwright/test';

test.describe('Flujo 5: Exportación de Documentos y Casos de Error', () => {
  test('Debe permitir exportar a Excel y verificar respuesta del endpoint', async ({ page }) => {
    await page.goto('/capacitaciones/');

    // Verificar que el endpoint de exportación responde con status 200 y archivo .xlsx
    const response = await page.request.get('/capacitaciones/exportar-excel-pif/');
    expect(response.status()).toBe(200);
    expect(response.headers()['content-type']).toContain('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
    expect(response.headers()['content-disposition']).toContain('attachment; filename="Reporte_Registro_Capacitaciones_UGB.xlsx"');
  });

  test('Debe manejar rutas no encontradas (404) adecuadamente', async ({ page }) => {
    const response = await page.goto('/ruta-inexistente-que-no-debe-existir/');
    // En modo DEBUG=True Django muestra página de 404 detallada o 404 handler
    expect(response?.status()).toBe(404);
  });

  test('Debe bloquear solicitudes API sin token CSRF (Protección CSRF 403)', async ({ page }) => {
    // Intentar POST directo sin token CSRF
    const response = await page.request.post('/capacitaciones/api/guardar-pif/', {
      data: {
        nombre_evento: 'Curso sin CSRF',
        tipo: 'Taller',
      },
      headers: {
        'Content-Type': 'application/json'
      }
    });

    // Django debe bloquearlo con 403 Forbidden
    expect(response.status()).toBe(403);
  });

  test('Debe rechazar solicitudes API de guardado con datos inválidos cuando incluye CSRF válido', async ({ page }) => {
    // 1. Obtener token CSRF legítimo de la página
    await page.goto('/capacitaciones/');
    const csrfToken = await page.evaluate(() => {
      const input = document.querySelector('input[name="csrfmiddlewaretoken"]') as HTMLInputElement;
      return input ? input.value : '';
    });
    expect(csrfToken).toBeTruthy();

    // 2. Enviar POST con token CSRF pero con nombre vacío
    const response = await page.request.post('/capacitaciones/api/guardar-pif/', {
      data: {
        nombre_evento: '', // Nombre vacío
        tipo: 'Taller',
      },
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken,
        'Referer': 'http://127.0.0.1:8000/capacitaciones/'
      }
    });

    expect(response.status()).toBe(400);
    const body = await response.json();
    expect(body.status).toBe('error');
    expect(body.message).toContain('El nombre del evento es obligatorio');
  });
});
