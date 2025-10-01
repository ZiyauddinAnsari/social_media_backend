# Week 3 & Week 4 Master Plan

> Living roadmap for the Social Media + Realtime + E‑commerce Integration project. Week 3 focuses on building a robust REST API. Week 4 layers on a React frontend, realtime features (chat + live interactions), and e‑commerce integration into a unified platform. This document will be updated as implementation progresses and governs development order.

---

## 0. High-Level Vision

Build a modular, secure, scalable social platform that supports:

- Core social interactions (posts, comments, likes, media)
- User identity (custom user, profiles, optional social login)
- Realtime communication (chat, notifications)
- E‑commerce capabilities (products, cart, orders, payment)
- Modern frontend integration (React + state management)
- Observability, rate limiting, and production readiness

Stretch (post Week 4, if time permits): federated notifications, activity feeds, background processing (Celery), AI-assisted recommendations.

---

## 1. Current Implementation Snapshot (End of Partial Week 3)

| Domain                          | Status          | Notes                                                      |
| ------------------------------- | --------------- | ---------------------------------------------------------- |
| Custom User (email login)       | ✅ Done         | Username optional, email unique                            |
| Profile (avatar, bio)           | ✅ Done         | Auto-created on registration                               |
| JWT Auth (rotation + blacklist) | ✅ Done         | SimpleJWT configured                                       |
| Rate Limiting                   | ✅ Done         | Global + scoped throttles                                  |
| Posts CRUD + Tags               | ✅ Done         | Privacy field present (filter not enforced yet)            |
| Comments (threaded)             | ✅ Done         | Parent for nesting; limited depth enforcement TBD          |
| Likes                           | ✅ Done         | Toggle endpoint                                            |
| Media Upload (single)           | ✅ Done (basic) | No validation yet; single upload endpoint                  |
| API Docs (OpenAPI)              | ✅ Baseline     | drf-spectacular basic schema only                          |
| Tests                           | 🟡 Partial      | Auth, post flow, throttling; need negative & privacy tests |
| Social Login                    | ❌ Pending      | Planned with django-allauth + dj-rest-auth                 |
| Permission Hardening            | ❌ Pending      | Comments + private posts filtering                         |
| Media Validation & Batch Upload | ❌ Pending      | Size/type & multi-file                                     |
| Documentation Enrichment        | ❌ Pending      | Tags, examples, error schema                               |
| Cleanup / Developer Ergonomics  | ❌ Pending      | README, .env.example, scripts                              |

---

## 2. Week 3 Remaining Gap Analysis

| Area         | Gap                                    | Planned Action                        | Priority |
| ------------ | -------------------------------------- | ------------------------------------- | -------- |
| Media        | No validation, single upload only      | Add validator, batch endpoint         | High     |
| Privacy      | Private posts not filtered             | Filter queryset, tests                | High     |
| Social Login | Not integrated                         | Add allauth + provider scaffolding    | Medium   |
| Permissions  | Comment modify/delete security minimal | IsOwnerOrReadOnly variant             | High     |
| Docs         | No grouping/examples                   | Add tags, summaries, examples         | Medium   |
| Tests        | No negative + privacy tests            | Add coverage                          | High     |
| Config       | Hardcoded limits                       | Add .env.example & settings constants | Medium   |

---

## 3. Week 3 Detailed Execution Plan (Ordered)

1. Media Validation & Batch Upload
   - Add settings: `MEDIA_MAX_SIZE`, `MEDIA_ALLOWED_CONTENT_TYPES`
   - Add `users/validators.py` with `validate_media_file(uploaded_file)`
   - Update `MediaSerializer.create` to validate & extract metadata (width/height for images if Pillow present)
   - New endpoint: `POST /api/posts/{id}/media/batch/` (`files[]` multipart list)
   - Return list of created media objects
   - Tests: oversize, disallowed mime, empty list, multi success
2. Privacy Enforcement
   - Filter `PostViewSet.queryset` to only include: public OR owned by requesting user
   - Add tests: other user cannot see private post; owner can
3. Comment & Object Permissions Hardening
   - Custom permission to restrict update/delete to author
   - Tests: Non-owner edit/delete -> 403
4. Social Login (Feature Flagged)
   - Install `django-allauth`, `dj-rest-auth[with_social]`
   - Add `ENABLE_SOCIAL_LOGIN` (False by default)
   - Configure Google provider placeholder; add endpoints
   - Docs section + conditional tests (skip if disabled)
5. API Documentation Enrichment
   - Tag endpoints: Auth, Users, Posts, Comments, Media, Likes
   - Add summaries & example request/response bodies
   - Provide error response component (validation errors)
6. Extended Tests & Edge Cases
   - Tag dedupe on create/update
   - Like idempotency explicit test
   - Threaded comments depth (optional constraint, e.g. 3) – skip if scope limited
7. Cleanup & Developer Ergonomics
   - `.env.example`, README updated
   - Add `scripts/` or `Makefile` (platform-neutral notes)
   - OpenAPI snapshot export (`openapi.json`)

Deliverables will be grouped with commit labels:

- `feat(media-validation)`
- `feat(privacy-filter)`
- `feat(comment-permissions)`
- `feat(social-login)`
- `docs(api-schema-enhancements)`
- `test(additional-coverage)`
- `chore(env-readme)`

---

## 4. Week 3 Acceptance Criteria

- All endpoints authenticated unless explicitly public (registration, token) ✅
- Media uploads reject invalid files & respect max size
- Batch upload returns array of media objects
- Private posts invisible to non-authors
- Social login endpoint available when flag enabled (returns documented error or redirect if not configured)
- OpenAPI schema includes tags, examples, proper error model
- Test suite covers: privacy, permissions, invalid media, throttling (already), negative auth cases, comment ownership
- No critical Pylint/flake/static errors (if added later)

---

## 5. Week 4 Objectives

Layer a production-ready frontend + realtime & commerce features:

1. React Frontend Integration (Component-based + routing + auth flows)
2. State Management (Zustand for local session + React Query for server cache OR Redux Toolkit if complex cross-slice orchestration emerges)
3. Realtime Chat (Django Channels + Redis) with online presence, typing indicators
4. Notifications (WebSocket or polling fallback) – likes, comments, new messages
5. E‑commerce Integration: product catalog browsing, cart, checkout (Stripe)
6. Unified Auth Flow: registration → login → social login → protected resources → purchase → order history
7. Admin Dashboard (basic analytics: active users, posts/day, revenue summary)
8. Testing: Unit (frontend + backend), integration (API + UI flows), End-to-end (Cypress), performance smoke
9. Deployment & Monitoring: containerization, logging, metrics, error tracking (Sentry), uptime (health endpoint already present)

---

## 6. Week 4 Backend Enhancements

| Feature                    | Description                                                   | Implementation Notes                                       |
| -------------------------- | ------------------------------------------------------------- | ---------------------------------------------------------- |
| WebSocket Layer            | Real-time transport                                           | Django Channels + ASGI (Redis channel layer)               |
| Chat Models                | Conversation, Message, Participant                            | Index on (conversation, created_at)                        |
| Presence                   | Track online users                                            | Redis set keyed by user ID with TTL heartbeat              |
| Notifications              | Generic model + fan-out                                       | Possibly use simple table then promote to Celery if needed |
| E‑commerce Models          | Product, Inventory, CartItem, Order, OrderItem, PaymentIntent | Stripe integration via webhook                             |
| Activity Stream (Optional) | User actions feed                                             | Denormalized table or Redis stream                         |
| API Versioning             | `/api/v1/` base path                                          | Future-proofing                                            |

### Chat Model Sketch

```text
Conversation(id, is_group, created_at)
ConversationParticipant(id, conversation_id, user_id, joined_at)
Message(id, conversation_id, sender_id, content_type=text|image, body, created_at, read_at)
MessageIndex: (conversation_id, created_at)
```

### WebSocket Events

| Event                 | Direction               | Payload                    |
| --------------------- | ----------------------- | -------------------------- |
| `chat.message.new`    | Server → Clients        | message object             |
| `chat.message.sent`   | Client → Server         | {conversation_id, body}    |
| `chat.message.read`   | Client → Server         | {message_ids[]}            |
| `presence.user.join`  | Server broadcast        | {user_id}                  |
| `presence.user.leave` | Server broadcast        | {user_id}                  |
| `chat.typing`         | Client → Server → Peers | {conversation_id, user_id} |

---

## 7. Frontend Architecture (React)

| Layer                    | Role                    | Tools                                                                         |
| ------------------------ | ----------------------- | ----------------------------------------------------------------------------- |
| Routing                  | Page & nested routes    | React Router v7 (or Next.js if SSR needed)                                    |
| Auth                     | Token storage + refresh | HttpOnly cookie for refresh (future), in-memory access token + silent refresh |
| Data Fetching            | Query/mutation cache    | React Query (TanStack Query)                                                  |
| State (global ephemeral) | UI + user session       | Zustand (lightweight)                                                         |
| Forms                    | Validation              | React Hook Form + Zod schemas                                                 |
| Styling                  | Design system           | Tailwind CSS + component library (Headless UI / Radix)                        |
| Realtime                 | WebSocket client        | Native WS or socket abstraction service                                       |
| Testing                  | Unit + integration      | Vitest + Testing Library; Cypress e2e                                         |

Decision Matrix (Zustand vs Redux Toolkit):

- Chosen: Zustand + React Query (less boilerplate, server state externalized). If chat & e-commerce cross-cutting complexity escalates, introduce RTK slices selectively.

---

## 8. Unified Auth & Session Flow

1. User registers (email/password OR social OAuth) → receives tokens
2. Access token retained in memory; refresh token stored (initially) in local storage (Week 3) then moved to secure cookie (Week 4 hardening)
3. Frontend `authGuard` route wrapper checks token freshness; triggers silent refresh when < 2 min left
4. WebSocket connection established post-auth (JWT in query param or subprotocol) – rotates if access token refreshed
5. Logout revokes refresh token (blacklist) and closes WS connection

---

## 9. E‑commerce Integration (Week 4)

| Module           | Description            | Key Endpoints (Planned)                                                      |
| ---------------- | ---------------------- | ---------------------------------------------------------------------------- |
| Products         | Browse + detail        | GET /api/v1/products/, GET /api/v1/products/{id}/                            |
| Cart             | Add/remove/view        | POST /api/v1/cart/items/, DELETE /api/v1/cart/items/{id}/, GET /api/v1/cart/ |
| Checkout         | Create payment intent  | POST /api/v1/checkout/session/                                               |
| Orders           | List/history           | GET /api/v1/orders/, GET /api/v1/orders/{id}/                                |
| Payment Webhooks | Stripe event ingestion | POST /api/v1/payments/webhook/                                               |

Security: Validate pricing server-side, never trust client-submitted totals.

---

## 10. Testing Strategy

| Layer                | Tooling                   | Scope                                                                   |
| -------------------- | ------------------------- | ----------------------------------------------------------------------- |
| Backend Unit         | pytest + Django           | Models, utilities (validators)                                          |
| Backend API          | pytest + DRF client       | Endpoint contracts, permissions                                         |
| WebSocket            | pytest + Channels testing | Event flows, auth handshake                                             |
| Frontend Unit        | Vitest + RTL              | Components, hooks                                                       |
| Frontend Integration | Vitest + MSW              | Auth flow, data fetching integration                                    |
| E2E                  | Cypress                   | Critical paths: login, create post, chat message, add to cart, checkout |
| Performance (Smoke)  | Locust / k6 (optional)    | Message send latency, post list under load                              |
| Security (Basic)     | Bandit, dependency checks | CI automated                                                            |

Coverage Targets:

- Week 3 backend: ≥80% for core apps
- Week 4 full stack: Critical paths fully exercised via Cypress

---

## 11. Observability & Deployment

| Aspect         | Plan                                                                                          |
| -------------- | --------------------------------------------------------------------------------------------- |
| Logging        | Structured JSON logs (later) via DRF middleware/LOGGING config                                |
| Error Tracking | Sentry (Django + React)                                                                       |
| Metrics        | Health endpoint (exists), add simple `/metrics` (Prometheus exposition optional)              |
| Deployment     | Docker images: backend (ASGI: uvicorn/gunicorn), frontend (static build), nginx reverse proxy |
| Env Management | `.env` → pip-tools/pipenv possible future; 12-factor adherence                                |
| Scaling        | Horizontal for ASGI workers + Redis for channels layer                                        |

---

## 12. Security & Hardening Checklist

| Item                                 | Week | Status  |
| ------------------------------------ | ---- | ------- |
| Enforce HTTPS (prod)                 | 4    | Planned |
| CSRF strategy for cookie refresh     | 4    | Planned |
| Rate limit login/register (done)     | 3    | ✅      |
| Validate media types                 | 3    | Pending |
| Restrict private post access         | 3    | Pending |
| Secure WebSocket auth token rotation | 4    | Planned |
| Payment webhook signature validation | 4    | Planned |
| Dependency scanning                  | 4    | Planned |

---

## 13. Milestone Timeline (Indicative)

| Day     | Focus                                                           |
| ------- | --------------------------------------------------------------- |
| W3 D1-2 | Auth, users, base models (Done)                                 |
| W3 D3   | Posts/comments/likes (Done)                                     |
| W3 D4   | Media + throttling (Done)                                       |
| W3 D5   | Validation, privacy, permissions, docs enrichment (In progress) |
| W3 D6   | Social login + extended tests                                   |
| W3 D7   | Cleanup & freeze backend v1                                     |
| W4 D1   | Frontend scaffold + auth integration                            |
| W4 D2   | Post feed, create flow, media display                           |
| W4 D3   | Chat backend (Channels) + WS client basics                      |
| W4 D4   | Chat UI polish + notifications                                  |
| W4 D5   | E‑commerce models + product listing UI                          |
| W4 D6   | Checkout + orders + payment webhook                             |
| W4 D7   | Admin dashboard + analytics + hardening                         |
| W4 D8   | E2E tests + performance smoke                                   |
| W4 D9   | Deployment pipeline setup                                       |
| W4 D10  | Buffer / polish / documentation                                 |

---

## 14. Risk Register

| Risk                 | Impact                     | Mitigation                               |
| -------------------- | -------------------------- | ---------------------------------------- |
| Feature Creep        | Delays week 4 deliverables | Strict scope & deferral list             |
| Media storage bloat  | Disk exhaustion            | Enforce size limit, optional pruning job |
| WebSocket auth drift | Security issue             | Centralize token validation helper       |
| Stripe complexity    | Payment delays             | Implement sandbox early & stub tests     |
| Test flakiness (WS)  | Slow CI                    | Deterministic factories + timeouts       |

---

## 15. Tooling & Conventions

- Commit prefixes: `feat:`, `fix:`, `docs:`, `test:`, `chore:`, `refactor:`
- Branch naming: `feature/<scope>`, `chore/<scope>`, `hotfix/<issue>`
- OpenAPI regeneration: automatic via management command (optional upcoming)
- Linting (future add): `ruff` + `black` for Python, `eslint` + `prettier` for JS

---

## 16. Immediate Next Action (Week 3)

Proceed with Section 3 Step 1: Media Validation & Batch Upload (branch: `feat/media-validation`).

Implementation includes:

- Add settings constants
- Create `users/validators.py`
- Update `MediaSerializer` and create batch upload view/action
- Add tests for validation scenarios
- Update docs (later grouping) to reflect new endpoint

---

## 17. Deferred / Parking Lot

| Idea                        | Reason for Deferral                     |
| --------------------------- | --------------------------------------- |
| Celery task queue           | Not required yet; adds infra complexity |
| Full text search (posts)    | Out of core scope Week 3/4              |
| GraphQL endpoint            | REST sufficient for now                 |
| Push notifications (mobile) | Requires device token infra             |

---

## 18. Success Criteria Summary

- Week 3: Stable, validated, documented API (v1) with ≥80% coverage for critical logic
- Week 4: Integrated React client with realtime chat + basic commerce + deployable stack
- Clear separation of concerns & maintainable modular code

---

## 19. Tracking Table (Live Updates)

| Task               | Status  | Notes              |
| ------------------ | ------- | ------------------ |
| Media validation   | Pending | Next action        |
| Batch upload       | Pending | Same batch         |
| Privacy filter     | Pending | After media        |
| Comment permission | Pending | After privacy      |
| Social login       | Pending | Post-permission    |
| Docs enrichment    | Pending | After social login |
| Extended tests     | Pending | Parallel with docs |
| Cleanup / README   | Pending | Finalize week 3    |

---

This file will be updated as tasks complete. End of current version.
