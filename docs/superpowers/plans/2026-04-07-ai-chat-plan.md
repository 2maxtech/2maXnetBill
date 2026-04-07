# AI Support Chat — Implementation Plan

**Spec:** docs/superpowers/specs/2026-04-07-ai-chat-design.md

## Task 1: Backend — Chat endpoint + Claude API integration
**Files:** `backend/app/api/chat.py` (new), `backend/app/main.py`, `backend/requirements.txt`
- Add `anthropic` to requirements.txt
- Create chat router with POST /chat endpoint
- If authenticated: load tenant context (customer counts, router status, overdue, settings state)
- If public: use general knowledge prompt
- Build messages array with history + current message + images
- Call Claude API (Haiku) with anthropic SDK
- POST /chat/upload for image uploads (save to /uploads/chat/)
- Rate limit: 20 msg/min per IP
- Register router in main.py
- ANTHROPIC_API_KEY env var check — endpoint returns 404 if not configured

## Task 2: Backend — Tenant context builder
**Files:** `backend/app/services/chat_context.py` (new)
- async function `build_tenant_context(db, tenant_id)` → string
- Queries: customer count by status, router count + active status, overdue invoice count/amount, billing/smtp/sms/paymongo config state, last 10 audit log entries
- Returns formatted text block for system prompt injection

## Task 3: Frontend — ChatWidget component
**Files:** `frontend/src/components/ChatWidget.vue` (new)
- Props: mode ("public" | "tenant")
- Floating button: orange circle, bottom-right, chat icon
- Expanded panel: fixed, 400px wide, 500px tall (mobile: full width)
- Header with title + close button
- Scrollable message area (user right/orange, AI left/gray)
- Input area with text field + image upload button + send button
- Image preview thumbnails before sending
- Typing indicator (animated dots)
- Chat history in component state
- Calls POST /api/v1/chat with message + history + image IDs
- Image upload: POST /api/v1/chat/upload, stores returned ID

## Task 4: Frontend — Integration + Landing page feature
**Files:** `frontend/src/components/layout/AppLayout.vue`, `frontend/src/pages/Landing.vue`
- Add ChatWidget to AppLayout (mode="tenant", only for non-demo non-super-admin)
- Add ChatWidget to Landing.vue (mode="public")
- Add "AI-Powered Support" feature card to landing page features section
- Hide widget if ANTHROPIC_API_KEY not configured (check via GET /api/v1/chat/status)

## Execution: All 4 tasks in parallel
- Tasks 1+2 are backend (chat.py imports from chat_context.py)
- Tasks 3+4 are frontend
- No blocking dependencies between backend and frontend
