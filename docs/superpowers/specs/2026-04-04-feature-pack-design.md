# NetLedger Feature Pack — Design Spec

## Overview

Bundle of features to bring NetLedger to production-ready state for PH ISP market. Covers: multi-router frontend completion, network scanner, SMTP settings UI, invoice printing, expense tracking, PPPoE password generator, and customizable dashboard.

---

## Feature 1: Multi-Router Frontend (Tasks 7-8 completion)

### Routers Page (`/routers`)

Table with columns: Name, URL, Location, Status badge (green/red), Sessions count, Actions.

Actions per row:
- **Edit** — modal with name, url, username, password, location fields
- **Test Connection** — calls `GET /routers/{id}/status`, shows result toast
- **Import Subscribers** — calls `POST /routers/{id}/import`, shows result count
- **Delete** — Popconfirm → soft-delete (set is_active=false)

"Add Router" button opens same modal for creation.

### Areas Page (`/areas`)

Table: Name, Description, Router (dropdown name), Customer count, Actions (Edit, Delete).

Modal form: name, description, router_id (Select populated from routers list).

### Sidebar Updates

Add after Active Users, before System group:
- Routers (CloudServerOutlined icon)
- Areas (EnvironmentOutlined icon)

### Route Registration

Lazy-load Routers and Areas pages in the router config, matching existing pattern.

### Dashboard — Per-Router Health Cards

Replace single MikroTik card with a row of cards, one per router. Each shows: name, status badge, CPU gauge, memory gauge, active sessions, interface traffic table.

Header subtitle: "{X}/{Y} routers online".

### Active Users — Router Filter

Add Select dropdown above table to filter sessions by router. Pass `?router_id=` to API.

### Network API Type Update

`DashboardData.mikrotik` becomes:
```typescript
{
  total_sessions: number;
  routers: Array<{ id, name, location, connected, identity, uptime, cpu_load, free_memory, total_memory, active_sessions, version, interfaces[] }>;
}
```

---

## Feature 2: MikroTik Network Scanner

### Backend: `POST /api/v1/network/scan`

Scans the local subnet for MikroTik devices using:
1. **Port scan** — try connecting to port 80 (www/REST API) on each IP in a given subnet range
2. For each responding IP, attempt `GET /rest/system/identity` with default credentials (admin/"") and configurable credentials
3. Return list of discovered devices with IP, identity name, version, and whether auth succeeded

Request body:
```json
{
  "subnet": "192.168.40.0/24",
  "username": "admin",
  "password": ""
}
```

Response:
```json
{
  "found": [
    {"ip": "192.168.40.30", "identity": "NetLedger-MT", "version": "7.18.2", "auth_ok": true},
    {"ip": "192.168.40.31", "identity": "MT-Tower2", "version": "7.16.1", "auth_ok": false}
  ],
  "scanned": 254,
  "duration_seconds": 12.3
}
```

Uses `asyncio.gather` with `httpx` to scan in parallel (batch of 20 concurrent). Timeout 2s per IP.

### Frontend

On the Routers page, add "Scan Network" button. Opens a modal:
- Input: subnet (default from MIKROTIK_URL's subnet), username, password
- Click "Scan" → shows spinner → shows results table
- Each found router has an "Add" button that pre-fills the Add Router modal

---

## Feature 3: SMTP Settings in UI

### Database: `settings` table

| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | |
| key | String(100), unique | e.g. "smtp_host", "smtp_port" |
| value | Text | encrypted for passwords |
| created_at | DateTime | |

Settings stored as key-value pairs. Keys:
- `smtp_host`, `smtp_port`, `smtp_user`, `smtp_password`, `smtp_from`, `smtp_from_name`

### Backend

- `GET /api/v1/settings/smtp` — returns current SMTP config (password masked)
- `PUT /api/v1/settings/smtp` — save SMTP config
- `POST /api/v1/settings/smtp/test` — send a test email to a given address

The notification service reads SMTP settings from DB instead of env vars. Falls back to env vars if DB settings not configured.

### Frontend: Settings Page (`/settings`)

Under System menu. Tabs or sections:
- **Email (SMTP)** — host, port, username, password, from email, from name, "Send Test Email" button
- Future tabs: General, Billing defaults, etc.

### Model

```python
class AppSetting(BaseModel):
    __tablename__ = "app_settings"
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False, default="")
```

---

## Feature 4: Invoice Printing

### Approach: Browser Print (`window.print()`)

No server-side printer detection needed. Add a "Print" button on:
- Invoice detail/list page — per invoice
- Invoice PDF download already exists — add a print-friendly view

### Implementation

Add a `PrintInvoice` component that:
1. Fetches invoice data
2. Renders a print-optimized HTML layout (hidden on screen, shown on print)
3. Calls `window.print()`

Or simpler: the existing PDF download already works. Add a "Print" button next to "Download PDF" that:
1. Downloads the PDF into a hidden iframe
2. Calls `iframe.contentWindow.print()`

Simplest approach: just add a Print button that opens the PDF in a new tab — the browser's PDF viewer has a built-in print button.

### Frontend Changes

- `Invoices.tsx`: Add PrinterOutlined button in the actions column, links to `/api/v1/billing/invoices/{id}/pdf` in a new tab
- `PortalInvoices.tsx`: Same for customer portal

---

## Feature 5: Expense Tracking

### Database: `expenses` table

| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | |
| category | Enum | electricity, internet, salary, equipment, maintenance, rent, other |
| description | String(255) | |
| amount | Numeric(10,2) | |
| date | Date | when expense occurred |
| receipt_number | String(100), nullable | |
| recorded_by | UUID (FK → users), nullable | |
| created_at | DateTime | |

### Backend

- `POST /api/v1/expenses/` — create expense
- `GET /api/v1/expenses/` — list with date range filter, category filter, pagination
- `PUT /api/v1/expenses/{id}` — update
- `DELETE /api/v1/expenses/{id}` — delete
- `GET /api/v1/expenses/summary` — totals by category for date range

### Frontend: Expenses Page (`/expenses`)

Under Billing menu group:
- Table: date, category (colored tag), description, amount, receipt #, actions
- "Add Expense" button → modal with form
- Summary cards at top: total expenses this month, by category breakdown
- Date range filter

### Dashboard Integration

Add to dashboard:
- "Expenses This Month" stat card
- "Net Profit" = collected revenue - expenses
- Revenue vs Expenses in the trend chart

### Sidebar

Add "Expenses" under Billing group (after Payments).

---

## Feature 6: PPPoE Password Generator

### Frontend Only

On the Customer create/edit form, add a "Generate" button next to the PPPoE password field.

Clicking it generates a random password:
- 8 characters
- Mix of lowercase, uppercase, digits
- No ambiguous characters (0/O, 1/l/I)
- Sets the password field value

Implementation: a simple utility function, no backend needed.

```typescript
function generatePassword(length = 8): string {
  const chars = 'abcdefghjkmnpqrstuvwxyzABCDEFGHJKMNPQRSTUVWXYZ23456789';
  return Array.from({ length }, () => chars[Math.floor(Math.random() * chars.length)]).join('');
}
```

Add a Button with KeyOutlined icon next to the password Input in the customer form.

---

## Feature 7: Customizable Dashboard

### Approach: Widget Preferences Stored in localStorage

No backend needed for v1. The admin can show/hide dashboard widgets.

Available widgets:
1. Subscriber counts (always shown)
2. Revenue stats (always shown)
3. Router health cards
4. Revenue trend chart
5. Recent payments
6. Overdue accounts
7. Expense summary

### Implementation

- Add a "Customize" button (SettingOutlined) on dashboard header
- Opens a drawer/modal with checkbox list of widgets
- Preferences saved to `localStorage('dashboard_widgets')`
- Dashboard reads preferences and conditionally renders widgets
- Default: all widgets visible

---

## What Stays the Same

- Billing engine logic
- Customer portal (all pages)
- Celery tasks
- Auth system
- All existing API endpoints

## File Summary

### New Files
| File | Purpose |
|------|---------|
| `frontend/src/api/routers.ts` | Router + Area API client |
| `frontend/src/pages/Routers.tsx` | Router management page |
| `frontend/src/pages/Areas.tsx` | Area management page |
| `frontend/src/pages/Expenses.tsx` | Expense tracking page |
| `frontend/src/pages/Settings.tsx` | SMTP settings page |
| `backend/app/models/expense.py` | Expense model |
| `backend/app/models/app_setting.py` | AppSetting model |
| `backend/app/schemas/expense.py` | Expense schemas |
| `backend/app/api/admin/expenses.py` | Expense CRUD API |
| `backend/app/api/admin/settings.py` | Settings API |
| `backend/alembic/versions/005_expenses_settings.py` | Migration |

### Modified Files
| File | Change |
|------|--------|
| `frontend/src/components/Layout/SideMenu.tsx` | Add Routers, Areas, Expenses, Settings |
| `frontend/src/pages/Dashboard.tsx` | Multi-router cards, expense stat, net profit, customizable widgets |
| `frontend/src/pages/ActiveUsers.tsx` | Router filter dropdown |
| `frontend/src/api/network.ts` | Multi-router dashboard types |
| `frontend/src/pages/billing/Invoices.tsx` | Print button |
| `frontend/src/pages/portal/PortalInvoices.tsx` | Print button |
| `backend/app/api/admin/network.py` | Scan endpoint, multi-router dashboard |
| `backend/app/models/__init__.py` | Register new models |
| `backend/app/main.py` | Register new routers |
| `backend/app/services/notification.py` | Read SMTP from DB |
| Route definitions file | Add new page routes |
