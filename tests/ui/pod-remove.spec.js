const { test, expect } = require('@playwright/test');

test('admin can upload then remove POD via information modal', async ({ page }) => {
  const adminUsername = process.env.ADMIN_USERNAME || 'admin';
  const adminPassword = process.env.ADMIN_E2E_PASSWORD;

  if (!adminPassword) {
    test.skip(true, 'ADMIN_E2E_PASSWORD is required for admin UI tests');
  }

  const consignmentNumber = `UIPOD${Date.now()}`;

  await page.goto('/admin/login');
  await page.locator('#username').fill(adminUsername);
  await page.locator('#password').fill(adminPassword);
  await page.getByRole('button', { name: /sign in/i }).click();

  await expect(page).toHaveURL(/\/admin\/dashboard/);

  await page.goto('/admin/consignments');
  await page.getByRole('button', { name: /add row/i }).click();

  const row = page.locator('#sheet-body tr').last();
  await row.locator('input.consignment_number').fill(consignmentNumber);
  await row.locator('select.status').selectOption('In Transit');
  await row.locator('input.drop_pincode').fill('400001');

  await page.getByRole('button', { name: /save all/i }).click();
  await expect(page.locator('#status-msg')).toContainText(/saved successfully/i, { timeout: 120000 });
  await page.waitForLoadState('networkidle');

  // Find the inserted row and open edit modal
  const insertedRow = page.locator('#sheet-body tr', {
    has: page.locator(`input.consignment_number[value="${consignmentNumber}"]`),
  }).first();

  await insertedRow.locator('.edit-row').click();

  // Attach a file to the modal file input
  const fileBuffer = Buffer.from('fake-pod-bytes');
  await page.setInputFiles('#modal-pod-file', { name: 'pod.jpg', mimeType: 'image/jpeg', buffer: fileBuffer });

  // Save modal and then save sheet so the POD is persisted
  await page.locator('#modal-save-btn').click();
  await page.getByRole('button', { name: /save all/i }).click();
  await expect(page.locator('#status-msg')).toContainText(/saved successfully/i, { timeout: 120000 });
  await page.waitForLoadState('networkidle');

  // Re-open edit modal and confirm POD preview shows uploaded state
  await insertedRow.locator('.edit-row').click();
  await expect(page.locator('#modal-pod-preview-container')).toContainText(/pod uploaded|pod ready/i, { timeout: 10000 });

  // Accept confirmation dialog and click Remove POD
  page.once('dialog', async (dialog) => { await dialog.accept(); });
  await page.locator('#modal-pod-remove').click();

  // Expect UI to show POD removed
  await expect(page.locator('#status-msg')).toContainText(/pod removed/i, { timeout: 10000 });
  await expect(page.locator('#modal-pod-preview-container')).toContainText(/no pod uploaded/i, { timeout: 10000 });
});
