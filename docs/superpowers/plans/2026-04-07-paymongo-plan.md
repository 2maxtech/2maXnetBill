# PayMongo Integration — Implementation Plan

**Spec:** docs/superpowers/specs/2026-04-07-paymongo-design.md

---

## Task 1: Database Changes
**Files:** `backend/app/models/invoice.py`, `backend/app/models/payment.py`
- Add `payment_token: UUID | None` to Invoice model (unique, nullable, default uuid4 on creation)
- Add `paymongo_checkout_id: str | None` to Payment model
- Add `convenience_fee: Decimal | None` to Payment model
- Update Invoice creation logic to auto-generate payment_token

## Task 2: PayMongo Service
**Files:** `backend/app/services/paymongo.py` (new)
- `PayMongoClient` class: init with secret_key
- `create_checkout_session(amount_cents, description, reference, payment_methods, success_url, cancel_url)` → returns checkout URL + session ID
- `verify_webhook_signature(payload, signature, secret)` → bool
- `test_connection(secret_key)` → bool (call GET /payment_methods or similar)
- Uses `httpx.AsyncClient` for HTTP calls
- PayMongo Basic auth: base64(secret_key + ":")

## Task 3: Settings Backend (Payments Tab)
**Files:** `backend/app/api/admin/settings.py`
- Add PAYMENT_KEYS constant: paymongo_secret_key, paymongo_public_key, paymongo_webhook_secret, paymongo_fee_mode, paymongo_fee_percent, paymongo_fee_flat
- `GET /settings/payments` — returns payment config for tenant
- `PUT /settings/payments` — saves payment config
- `POST /settings/payments/test` — calls PayMongo API to verify keys

## Task 4: Public Payment Endpoints
**Files:** `backend/app/api/payment.py` (new)
- `GET /pay/{token}` — public, returns invoice details (customer name, plan, amount, fee, tenant branding)
- `POST /pay/{token}/checkout` — creates PayMongo checkout session, returns redirect URL
- `POST /api/v1/webhooks/paymongo` — webhook receiver (verify signature, record payment, mark invoice paid)
- Register in main.py as public routes (no auth prefix)

## Task 5: Fee Calculation
**In:** `backend/app/services/paymongo.py`
- `calculate_fee(amount, fee_percent, fee_flat)` → convenience fee
- `calculate_total(amount, fee_mode, fee_percent, fee_flat)` → total for checkout
- Fee only applies when fee_mode = "pass_to_customer"

## Task 6: Payment Link in Notifications
**Files:** `backend/app/services/billing.py`, `backend/app/services/template_renderer.py`
- Add `{payment_url}` variable to notification templates
- When generating invoice notification: include payment link if tenant has PayMongo configured
- Payment URL = `{base_url}/pay/{invoice.payment_token}`

## Task 7: Settings Frontend (Payments Tab)
**Files:** `frontend/src/pages/Settings.vue`
- Add "Payments" tab
- Fields: Secret Key (masked), Public Key, Webhook Secret (masked)
- Fee mode radio: "Customer pays fee" / "We absorb fee"
- Fee percent + flat amount inputs
- Test Connection button
- Help link to paymongo.com

## Task 8: Payment Page Frontend
**Files:** `frontend/src/pages/Pay.vue` (new), `frontend/src/router/index.ts`
- Public route: `/pay/:token`
- Standalone page (no app layout, no sidebar)
- Fetches invoice details from API
- Shows: tenant branding, invoice summary, fee breakdown, Pay Now button
- On click: calls checkout API, redirects to PayMongo
- Success/cancel pages (can be same component with different state)
- Mobile responsive (most users will pay from phone)
- Add to router as public route

## Task 9: Portal Pay Now Button
**Files:** `frontend/src/pages/portal/PortalDashboard.vue`, `frontend/src/pages/portal/PortalInvoices.vue`
- Add "Pay Now" button on unpaid invoices (only if payment_token exists)
- On click: calls same checkout API, redirects to PayMongo
- Button hidden if no payment_token (tenant hasn't configured PayMongo)

## Execution Order

**Phase 1 (backend, parallel):**
- Task 1: DB changes
- Task 2: PayMongo service
- Task 3: Settings backend
- Task 5: Fee calculation (part of Task 2)

**Phase 2 (backend, depends on Phase 1):**
- Task 4: Public payment endpoints
- Task 6: Payment link in notifications

**Phase 3 (frontend, parallel):**
- Task 7: Settings Payments tab
- Task 8: Payment page
- Task 9: Portal Pay Now button

**Phase 4: Deploy + test with PayMongo test keys**
