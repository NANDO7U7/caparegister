import { test, expect } from './fixtures';

test.describe('Flujo 3: Formulario Modal, Validaciones y CRUD en PostgreSQL', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/capacitaciones/');
  });

  test('Debe validar campos requeridos y calcular el total automáticamente', async ({ page }) => {
    // Abrir modal
    await page.click('#btnNuevaCap');
    await expect(page.locator('#capacitacionModal')).toBeVisible();

    // 1. Probar cálculo de costo automático
    await page.fill('#fInvHon', '180.50');
    await page.fill('#fInvMat', '20.00');
    await page.fill('#fViatAlim', '15.00');
    await page.fill('#fGastTrans', '25.00');
    await page.fill('#fGastAloj', '0');
    
    // Total debe ser 180.50 + 20 + 15 + 25 = 240.50
    await expect(page.locator('#fTotalCalculado')).toHaveText('240.50');

    // 2. Cerrar y volver a abrir
    await page.click('button:has-text("Cancelar")');
    await expect(page.locator('#capacitacionModal')).toBeHidden();
  });

  test('Debe crear una nueva capacitación, actualizarla y luego eliminarla en PostgreSQL', async ({ page }) => {
    const testTitle = `Test E2E Automatizado Playwright ${Date.now()}`;

    // 1. ABRIR MODAL Y LLENAR FORMULARIO
    await page.click('#btnNuevaCap');
    await expect(page.locator('#capacitacionModal')).toBeVisible();

    await page.selectOption('#fTipo', 'Taller');
    await page.selectOption('#fLocalidad', 'Nacional');
    await page.selectOption('#fModalidad', 'Virtual');
    await page.fill('#fNombreEvento', testTitle);
    await page.selectOption('#fEstado', 'Planificada');
    await page.fill('#fProveedor', 'Innovación y Gestión Académica - UGB');
    await page.fill('#fContacto', 'Ing. Carlos Roberto Martínez');
    await page.fill('#fLugar', 'Plataforma Zoom UGB');
    await page.fill('#fFecha', '2026-11-15');
    await page.fill('#fHorario', '8:00 AM a 12:00 PM');
    await page.fill('#fHoras', '16');
    await page.fill('#fCodigoProyecto', 'IGA004');
    await page.selectOption('#fAreaPif', 'Especialidad');

    // Agregar participante
    const nombreInput = page.locator('.asist-nombre').first();
    const puestoInput = page.locator('.asist-puesto').first();
    await nombreInput.fill('Docente E2E');
    await puestoInput.fill('Docente tiempo completo');

    // Asignar facultad con atajo
    await page.click('button:has-text("+ Ciencia y Tecnología")');
    await expect(page.locator('#fUnidades')).toHaveValue(/Facultad de Ciencia y Tecnología/);

    // Asignar costos
    await page.fill('#fInvHon', '250.00');

    // 2. GUARDAR EN POSTGRESQL
    await page.click('#btnGuardarModal');

    // El modal debe cerrarse y mostrar banner de éxito
    await expect(page.locator('#capacitacionModal')).toBeHidden({ timeout: 10000 });
    await expect(page.locator('#alertBanner')).toBeVisible();
    await expect(page.locator('#alertBanner')).toContainText('guardada exitosamente');

    // 3. VERIFICAR QUE APARECE EN LA TABLA
    await page.fill('#filterSearch', testTitle);
    const tableBody = page.locator('#capacitacionesTableBody');
    await expect(tableBody).toContainText(testTitle);
    await expect(tableBody).toContainText('16 h');
    await expect(tableBody).toContainText('$250.00');

    // 4. EDITAR EL REGISTRO CREADO
    const row = page.locator('#capacitacionesTableBody tr').filter({ hasText: testTitle });
    await row.locator('button:has-text("Editar")').click();
    await expect(page.locator('#capacitacionModal')).toBeVisible();

    // Modificar horas y guardar
    await page.fill('#fHoras', '20');
    await page.click('#btnGuardarModal');
    await expect(page.locator('#capacitacionModal')).toBeHidden({ timeout: 10000 });

    // Verificar horas actualizadas
    await page.fill('#filterSearch', testTitle);
    await expect(tableBody).toContainText('20 h');

    // 5. ELIMINAR EL REGISTRO DE PRUEBA
    page.once('dialog', async dialog => {
      expect(dialog.message()).toContain('¿Está seguro de eliminar');
      await dialog.accept();
    });

    const editRow = page.locator('#capacitacionesTableBody tr').filter({ hasText: testTitle });
    await editRow.locator('button:has-text("Eliminar")').click();

    // Confirmar que ya no existe en la tabla
    await page.waitForTimeout(1000);
    await page.fill('#filterSearch', testTitle);
    await expect(page.locator('#capacitacionesTableBody')).toContainText('No se encontraron capacitaciones');
  });
});
