import { test, expect } from './fixtures';

test.describe('Flujo 4: Control de Acceso y Roles (RBAC) y Privacidad de Credenciales', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/capacitaciones/');
  });

  test('Credenciales no deben mostrarse en ningún panel ni interfaz', async ({ page }) => {
    // 1. Verificar que no haya contraseñas en texto plano expuestas en el DOM visible
    await expect(page.locator('body')).not.toContainText(process.env.SIGECAP_E2E_ADMIN_PASSWORD!);
    await expect(page.locator('body')).not.toContainText(process.env.SIGECAP_E2E_COORD_PASSWORD!);
    await expect(page.locator('body')).not.toContainText(process.env.SIGECAP_E2E_CONSULTA_PASSWORD!);
    await expect(page.locator('body')).not.toContainText(process.env.SIGECAP_E2E_PIF_PASSWORD!);

    // 2. Abrir modal de autenticación y verificar que campos estén vacíos y sin tarjetas de ayuda con claves
    await page.click('button:has-text("Cambiar Rol")');
    await expect(page.locator('#loginModal')).toBeVisible();
    await expect(page.locator('#loginModal')).not.toContainText(process.env.SIGECAP_E2E_ADMIN_PASSWORD!);
    await expect(page.locator('#loginModal')).not.toContainText(process.env.SIGECAP_E2E_COORD_PASSWORD!);
    await expect(page.locator('#loginUser')).toHaveValue('');
    await expect(page.locator('#loginPass')).toHaveValue('');
  });

  test('Rol Coordinador: Edición deshabilitada en el panel de capacitaciones', async ({ page }) => {
    // 1. Iniciar sesión como Coordinador
    await page.click('button:has-text("Cambiar Rol")');
    await page.fill('#loginUser', 'coordinador');
    await page.fill('#loginPass', process.env.SIGECAP_E2E_COORD_PASSWORD!);
    await page.click('#loginModal button[type="submit"]');

    // 2. Verificar que se cierra el modal y el rol muestra "Solo Lectura"
    await expect(page.locator('#loginModal')).toBeHidden();
    await expect(page.locator('#currentUserRoleBadge')).toHaveText('Solo Lectura');

    // 3. Los botones de modificación deben estar ocultos
    await expect(page.locator('#btnNuevaCap')).toBeHidden();
    await expect(page.locator('#btnImportarExcel')).toBeHidden();

    // 4. Las filas de la tabla deben mostrar "Solo lectura" en lugar de botones de editar/eliminar
    await expect(page.locator('#capacitacionesTableBody')).toContainText('Solo lectura');

    // 5. Intento directo de guardar vía API debe ser rechazado con 403 Forbidden
    const saveResponse = await page.request.post('/capacitaciones/api/guardar-pif/', {
      headers: {
        'X-User-Role': 'COORDINADOR'
      },
      data: {
        nombre_evento: 'Evento no permitido por coordinador'
      }
    });
    expect(saveResponse.status()).toBe(403);
  });

  test('Rol UGB · PIF: Edición habilitada en el panel de capacitaciones', async ({ page }) => {
    // 1. Iniciar sesión como usuario gestor UGB · PIF
    await page.click('button:has-text("Cambiar Rol")');
    await page.fill('#loginUser', 'ugb_pif');
    await page.fill('#loginPass', process.env.SIGECAP_E2E_PIF_PASSWORD!);
    await page.click('#loginModal button[type="submit"]');

    // 2. Verificar que se cierra el modal y el rol muestra edición de UGB · PIF
    await expect(page.locator('#loginModal')).toBeHidden();
    await expect(page.locator('#currentUserRoleBadge')).toHaveText('Edición UGB · PIF');

    // 3. Botones de gestión deben estar visibles
    await expect(page.locator('#btnNuevaCap')).toBeVisible();
    await expect(page.locator('#btnImportarExcel')).toBeVisible();

    // 4. Botones de acción en la tabla deben mostrar "Editar"
    await expect(page.locator('#capacitacionesTableBody')).toContainText('Editar');

    // 5. Debe permitir abrir el modal de nueva capacitación
    await page.click('#btnNuevaCap');
    await expect(page.locator('#capacitacionModal')).toBeVisible();
    await expect(page.locator('#modalTitle')).toHaveText('Registrar Nueva Capacitación');
    await page.click('#capacitacionModal button[type="button"]:has-text("Cancelar")');
    await expect(page.locator('#capacitacionModal')).toBeHidden();
  });

  test('Rol Administrador: Control Total y Edición completa', async ({ page }) => {
    // 1. Iniciar sesión como Administrador
    await page.click('button:has-text("Cambiar Rol")');
    await page.fill('#loginUser', 'admin');
    await page.fill('#loginPass', process.env.SIGECAP_E2E_ADMIN_PASSWORD!);
    await page.click('#loginModal button[type="submit"]');

    // 2. Verificar estado
    await expect(page.locator('#loginModal')).toBeHidden();
    await expect(page.locator('#currentUserRoleBadge')).toHaveText('Edición Total');
    await expect(page.locator('#btnNuevaCap')).toBeVisible();
    await expect(page.locator('#btnImportarExcel')).toBeVisible();
  });
});
