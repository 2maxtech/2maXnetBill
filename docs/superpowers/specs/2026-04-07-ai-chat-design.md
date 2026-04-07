# AI Support Chat — Design Spec

**Date:** 2026-04-07
**Goal:** In-app AI support chatbot powered by Claude API. Two modes: public (landing page FAQ) and tenant (data-aware support). Bug reports with image attachments.

## Chat Widget

- Floating button (bottom-right corner), expands to chat panel
- Appears on: Landing page (public mode), Admin app (tenant mode)
- Hidden for: super admin, demo users, portal
- Styling: matches NetLedger theme (orange accent, dark header)

## Two Modes

### Public Mode (Landing Page)
- No authentication required
- System prompt: NetLedger features, pricing (free beta), supported hardware, deployment options, how to sign up
- Goal: answer pre-sales questions, convert visitors

### Tenant Mode (Admin App)
- Authenticated — reads tenant's actual data
- System prompt includes live tenant context:
  - Customer count by status (active/suspended/disconnected)
  - Router count and connection status
  - Overdue invoice count and total amount
  - Billing config state (configured or not)
  - SMS/SMTP config state
  - PayMongo config state
  - Recent audit log entries (last 10)
- Can answer: "How many overdue?", "Is my router connected?", "How to set up SMS?"
- Scoped: only answers NetLedger-related questions, politely declines off-topic
- Bug reports: user can describe a bug and attach screenshot images

## Image Attachments

- Upload button in chat input area (camera/paperclip icon)
- Images uploaded to backend, stored in /uploads/chat/
- Image URL passed to Claude API as part of the message (Claude supports vision)
- Max 3 images per message, max 5MB each
- Accepted formats: PNG, JPG, WEBP

## Backend

### POST /api/v1/chat (public + authenticated)
Request:
```json
{
  "message": "How do I add a router?",
  "history": [
    {"role": "user", "content": "Hi"},
    {"role": "assistant", "content": "Hello! How can I help?"}
  ],
  "images": ["uuid-of-uploaded-image"]
}
```

Response (streaming not needed for v1):
```json
{
  "response": "To add a router, go to Routers page..."
}
```

Logic:
1. If authenticated: load tenant context, use tenant system prompt
2. If public: use public system prompt
3. Build messages array: system prompt + history + current message (with images if any)
4. Call Claude API (Haiku model for speed + cost)
5. Return response

### POST /api/v1/chat/upload (authenticated only)
- Multipart file upload
- Saves to /uploads/chat/{uuid}.{ext}
- Returns { id, url }
- Max 5MB, PNG/JPG/WEBP only

## Claude API Integration

- Model: claude-haiku-4-5-20251001 (fast, cheap, supports vision)
- API key: ANTHROPIC_API_KEY env var (2max.tech's key, not per-tenant)
- Max tokens response: 1024
- Temperature: 0.3 (factual, not creative)
- No message persistence — history sent from frontend each request
- Rate limit: 20 messages per minute per user (prevent abuse)

## System Prompt (Tenant Mode)

```
You are NetLedger Support, an AI assistant for ISP billing software.
You help ISP operators use NetLedger to manage their subscribers, billing, and MikroTik routers.

RULES:
- Only answer questions about NetLedger, ISP billing, and MikroTik
- If asked about anything else, politely say "I can only help with NetLedger-related questions"
- Be concise and helpful
- If the user reports a bug, acknowledge it and say the team has been notified
- Use the tenant's data below to give specific answers

TENANT DATA:
{tenant_context}

FEATURES:
- Dashboard with real-time router stats
- Customer management with MikroTik PPPoE sync
- Plans with bandwidth profiles
- Automated billing (invoice generation, reminders, enforcement)
- Customer portal with online payments (GCash/Maya via PayMongo)
- Hotspot with voucher system
- SMS notifications (Semaphore)
- Email notifications (SMTP)
- CSV/PDF export
- Settings: Billing, SMTP, SMS, Payments, Branding, Notifications
```

## System Prompt (Public Mode)

```
You are NetLedger Support, an AI assistant for NetLedger ISP billing software by 2max Tech.
You help answer questions about NetLedger features, pricing, and how to get started.

RULES:
- Only answer questions about NetLedger
- If asked about anything else, politely decline
- Be concise and friendly
- Encourage visitors to sign up (free during beta) or try the demo

KEY INFO:
- NetLedger is free during beta — no restrictions, unlimited subscribers
- Two deployment options: Cloud (SaaS) at netl.2max.tech, or Self-Hosted (Docker)
- Supports MikroTik routers (PPPoE, Hotspot)
- Works on ARM64/Raspberry Pi
- Features: billing, customer portal, SMS/email notifications, PayMongo payments, CSV/PDF export
- Sign up at netl.2max.tech/register
- Try the demo: click "Try Demo" on the landing page
```

## Frontend

### ChatWidget.vue (reusable component)
- Props: `mode` ("public" | "tenant")
- Floating button: orange circle with chat icon, bottom-right
- Expanded panel: 400px wide, 500px tall, fixed position
- Header: "NetLedger Support" with AI badge + close button
- Message area: scrollable, user messages right (orange), AI messages left (gray)
- Input area: text input + image upload button + send button
- Image preview: thumbnails of attached images before sending
- Typing indicator: animated dots while waiting for response
- Persists chat history in component state (cleared on page refresh)

### Integration
- Landing.vue: `<ChatWidget mode="public" />`
- AppLayout.vue: `<ChatWidget mode="tenant" />` (only for non-demo, non-super-admin users)

## Landing Page Feature Highlight

- Add "AI-Powered Support" to the features section on the landing page
- Description: "Built-in AI assistant that knows your data. Ask questions, report bugs with screenshots, get instant answers."

## Environment

- `ANTHROPIC_API_KEY` — added to .env / docker-compose
- Not required for app to function — if missing, chat widget doesn't appear

## Non-Goals

- Message persistence / chat history in DB (future)
- Streaming responses (future)
- Auto-fix bugs (Claude can diagnose but not take action)
- Chat for portal customers (only for ISP operators and landing page visitors)
