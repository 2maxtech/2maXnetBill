/**
 * E2E: Full customer lifecycle — create, invoice, print, disconnect,
 * reconnect, change plan, delete.
 *
 * Runs against the live app with real auth. Uses a unique PPPoE username
 * per run so tests are idempotent.
 */
import { test, expect, Page } from '@playwright/test'
import { fileURLToPath } from 'url'
import { dirname, join } from 'path'
import { readFileSync } from 'fs'

const __dirname = dirname(fileURLToPath(import.meta.url))
const AUTH_FILE = join(__dirname, '../.auth/user.json')

test.use({ storageState: AUTH_FILE })

const suffix = Date.now().toString(36)
const TEST_CUSTOMER = {
  full_name: `E2E Test ${suffix}`,
  email: `e2e-${suffix}@test.local`,
  pppoe_username: `e2e_${suffix}`,
  pppoe_password: 'testpass123',
}

let customerId: string

// Read token from saved auth state
function getToken(): string {
  const state = JSON.parse(readFileSync(AUTH_FILE, 'utf8'))
  const origin = state.origins?.find((o: any) => o.localStorage?.length > 0)
  const entry = origin?.localStorage?.find((e: any) => e.name === 'access_token')
  return entry?.value || ''
}

function authHeaders() {
  return { Authorization: `Bearer ${getToken()}` }
}

async function apiGet(page: Page, path: string) {
  return page.request.get(`/api/v1${path}`, { headers: authHeaders() })
}

async function apiPost(page: Page, path: string, data?: any) {
  return page.request.post(`/api/v1${path}`, { headers: authHeaders(), data })
}

// ---------------------------------------------------------------------------
// Tests run in order — each depends on the previous
// ---------------------------------------------------------------------------

test.describe.serial('Customer lifecycle', () => {

  test('1. Login and reach dashboard', async ({ page }) => {
    await page.goto('/dashboard')
    await expect(page).toHaveURL(/\/dashboard/)
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible()
  })

  test('2. Navigate to customers page', async ({ page }) => {
    await page.goto('/customers')
    await page.waitForLoadState('networkidle')
    await expect(page.getByRole('button', { name: /Add Customer/i })).toBeVisible({ timeout: 10_000 })
  })

  test('3. Create a new customer', async ({ page }) => {
    await page.goto('/customers')
    await page.waitForLoadState('networkidle')

    // Open add modal
    await page.getByRole('button', { name: /Add Customer/i }).click()
    await page.waitForTimeout(500)

    // Fill form fields by placeholder
    await page.locator('input[placeholder="Juan Dela Cruz"]').fill(TEST_CUSTOMER.full_name)
    await page.locator('input[placeholder="juan@example.com"]').fill(TEST_CUSTOMER.email)
    await page.locator('input[placeholder="juan.delacruz"]').fill(TEST_CUSTOMER.pppoe_username)

    // PPPoE password — clear auto-generated and fill ours
    const pwInputs = page.locator('input[placeholder="juan.delacruz"]').locator('..').locator('..').locator('input').nth(1)
    // Simpler: find all text inputs in the modal and fill the password one
    // The password field is right after the username field
    const modalInputs = page.locator('.fixed input[type="text"], .fixed input:not([type])')
    const inputCount = await modalInputs.count()
    // Find password input by iterating
    for (let i = 0; i < inputCount; i++) {
      const placeholder = await modalInputs.nth(i).getAttribute('placeholder')
      if (!placeholder) {
        // This might be the auto-generated password field
        await modalInputs.nth(i).fill(TEST_CUSTOMER.pppoe_password)
        break
      }
    }

    // Select first plan
    const planSelect = page.locator('.fixed select').first()
    const options = await planSelect.locator('option').all()
    if (options.length > 1) {
      await planSelect.selectOption({ index: 1 })
    }

    // Submit — find the button with "Create Customer" text inside the modal
    await page.locator('.fixed button:has-text("Create Customer")').click()

    // Wait for modal to close
    await page.waitForTimeout(2000)

    // Search for the created customer
    const searchInput = page.locator('input[placeholder*="Search"]').first()
    await searchInput.fill(TEST_CUSTOMER.pppoe_username)
    await page.waitForTimeout(1500)

    // Verify customer appears
    await expect(page.locator(`text=${TEST_CUSTOMER.full_name}`).first()).toBeVisible({ timeout: 10_000 })
  })

  test('4. Customer has MikroTik secret synced', async ({ page }) => {
    // Find customer ID via API
    const searchResp = await apiGet(page, `/customers/?search=${TEST_CUSTOMER.pppoe_username}`)
    const searchData = await searchResp.json()

    // Handle both { items: [...] } and direct array response
    const items = searchData.items || searchData
    expect(Array.isArray(items) ? items.length : 0).toBeGreaterThan(0)

    const customer = Array.isArray(items) ? items[0] : items
    customerId = customer.id
    expect(customer.pppoe_username).toBe(TEST_CUSTOMER.pppoe_username)
    expect(customer.status).toBe('active')
    expect(customer.mikrotik_secret_id).toBeTruthy()
  })

  test('5. Generate invoice for customer', async ({ page }) => {
    test.skip(!customerId, 'No customer created')

    await page.goto('/billing/invoices')
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(1000)

    // Click "Generate for Customer"
    await page.getByRole('button', { name: /Generate for Customer/i }).click()
    await page.waitForTimeout(500)

    // Type customer name in the search input inside the modal
    const modalSearch = page.locator('.fixed input').first()
    await modalSearch.fill(TEST_CUSTOMER.full_name)
    await page.waitForTimeout(1500)

    // Click the customer in dropdown results
    await page.locator(`.fixed [class*="cursor-pointer"]:has-text("${TEST_CUSTOMER.full_name}")`).or(
      page.locator(`.fixed li:has-text("${TEST_CUSTOMER.full_name}")`)
    ).or(
      page.locator(`.fixed div:has-text("${TEST_CUSTOMER.full_name}")`).last()
    ).click()
    await page.waitForTimeout(500)

    // Click Generate button
    await page.locator('.fixed button:has-text("Generate")').last().click()
    await page.waitForTimeout(2000)

    // Verify invoice exists via API
    const resp = await apiGet(page, `/billing/invoices?search=${TEST_CUSTOMER.full_name}`)
    const data = await resp.json()
    expect(data.items.length).toBeGreaterThan(0)
  })

  test('6. Invoice PDF endpoint returns PDF (not auth error)', async ({ page }) => {
    test.skip(!customerId, 'No customer created')

    // Get invoice ID via API
    const listResp = await apiGet(page, `/billing/invoices?search=${TEST_CUSTOMER.full_name}`)
    const listData = await listResp.json()
    const invoices = listData.items || listData
    expect(invoices.length).toBeGreaterThan(0)
    const invoiceId = invoices[0].id

    // Fetch PDF with auth — this is what the print button does now (blob fetch)
    const pdfResp = await page.request.get(`/api/v1/billing/invoices/${invoiceId}/pdf`, {
      headers: authHeaders(),
    })

    // Must return 200 with PDF content, NOT 401/403
    expect(pdfResp.status()).toBe(200)
    const contentType = pdfResp.headers()['content-type']
    expect(contentType).toContain('application/pdf')

    // Verify it's actual PDF data (starts with %PDF)
    const body = await pdfResp.body()
    expect(body.length).toBeGreaterThan(100)
    expect(body.toString('utf8', 0, 5)).toBe('%PDF-')
  })

  test('7. Download invoice PDF works', async ({ page }) => {
    test.skip(!customerId, 'No customer created')

    await page.goto('/billing/invoices')
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(1000)

    const row = page.locator('tr', { hasText: TEST_CUSTOMER.full_name }).first()

    // Click download — triggers file download
    const downloadPromise = page.waitForEvent('download', { timeout: 15_000 })
    await row.locator('button[title="Download PDF"]').click()
    const download = await downloadPromise
    expect(download.suggestedFilename()).toMatch(/invoice.*\.pdf/i)
  })

  test('8. Disconnect customer via API', async ({ page }) => {
    test.skip(!customerId, 'No customer created')

    // Use API directly — UI disconnect button location may vary
    const resp = await apiPost(page, `/customers/${customerId}/disconnect`)
    expect(resp.status()).toBe(200)
    const data = await resp.json()
    expect(data.status).toBe('disconnected')

    // Verify in DB
    const check = await apiGet(page, `/customers/${customerId}`)
    const customer = await check.json()
    expect(customer.status).toBe('disconnected')
  })

  test('9. Reconnect customer via API', async ({ page }) => {
    test.skip(!customerId, 'No customer created')

    const resp = await apiPost(page, `/customers/${customerId}/reconnect`)
    expect(resp.status()).toBe(200)
    const data = await resp.json()
    expect(data.status).toBe('reconnected')

    // Verify status is active and MT secret restored
    const check = await apiGet(page, `/customers/${customerId}`)
    const customer = await check.json()
    expect(customer.status).toBe('active')
    expect(customer.mikrotik_secret_id).toBeTruthy()
  })

  test('10. Delete customer (cleanup)', async ({ page }) => {
    test.skip(!customerId, 'No customer created')

    const resp = await apiPost(page, `/customers/${customerId}/delete`, {
      password: process.env.E2E_PASSWORD || '',
    })
    expect(resp.status()).toBe(200)
    const data = await resp.json()
    expect(data.status).toBe('deleted')
  })
})
