# Week 3 Pending / Enhancement Tasks

> Source of truth for remaining backend items before moving fully into Week 4 (frontend + realtime + commerce). Each item lists: rationale, scope, acceptance criteria, priority.

| ID  | Category      | Task                                                                                         | Priority | Status  | Notes                                                                |
| --- | ------------- | -------------------------------------------------------------------------------------------- | -------- | ------- | -------------------------------------------------------------------- |
| P1  | Auth          | Social login integration (django-allauth + dj-rest-auth)                                     | High     | ✅ Done | Google OAuth implemented; /api/auth/social/google/ endpoint ready    |
| P2  | Permissions   | Comment object-level permissions (update/delete only by author)                              | High     | Done    | Enforced via IsOwnerOrReadOnly; basic tests added                    |
| P3  | Media         | Media deletion endpoint (single + optional bulk)                                             | Medium   | Done    | DELETE /posts/{post_id}/media/{id}/ + permissions                    |
| P4  | Tests & Sec   | Consolidated negative tests (posts/comments/media ownership; private access; unauthorized)   | High     | Done    | 7 tests: ownership violations, private access, 404 scenarios         |
| P5  | Documentation | Add error schemas (ValidationError, ThrottleError) + missing examples (batch media, refresh) | Medium   | Pending | Extend SPECTACULAR settings + custom components                      |
| P6  | Consistency   | Standardize response envelope (success, message, data)                                       | Low      | Pending | Consider transitional compatibility layer                            |
| P7  | Settings      | Central test settings (disable throttles) instead of decorators                              | Medium   | ✅ Done | Created settings_test.py; removed all throttle workarounds           |
| P8  | DX            | README with setup, env vars, test commands                                                   | Medium   | Pending | Include JWT & throttle explanation                                   |
| P9  | Media         | External storage prep (S3 / Azure Blob) abstraction (settings toggles)                       | Low      | Pending | Future scalability                                                   |
| P10 | (Merged)      | (Merged into P4 Tests & Sec Hardening)                                                       | -        | -       | Keep reference; track under P4                                       |
| P11 | Auth          | Convenience /api/auth/me endpoint (current user)                                             | Low      | Pending | Simple RetrieveAPIView                                               |
| P12 | Docs          | Tag throttle rates; annotate 429 responses                                                   | Low      | Pending | Add OpenApiResponse 429 across create endpoints                      |
| P13 | Cleanup       | Remove skip logic & throttle workarounds after test settings refactor                        | Medium   | ✅ Done | All throttle workarounds & skips removed; ThrottleTestCase commented |
| P14 | Media         | Media ownership & delete permission tests (after P3)                                         | Medium   | Pending | Only author/uploader can delete media                                |

---

## Detailed Descriptions

### P1 Social Login Integration

**Why:** Fulfill spec; enable Google (first) + extensibility.
**Scope:** Add allauth + dj-rest-auth, configure provider pipeline, expose /api/auth/social/login/ (or reuse dj-rest-auth endpoints) issuing SimpleJWT tokens. Tests for: new social user creation, linking existing email (if allowed), duplicate provider edge case.
**Acceptance:** Can POST provider token → receive JWT + user; documented in schema.

### P2 Comment Object-Level Permissions

**Why:** Prevent unauthorized edits/deletes.
**Scope:** Add IsOwnerOrReadOnly to CommentViewSet, add tests for forbidden update/delete by non-author, allowed for author.
**Acceptance:** Non-owner receives 403 on patch/delete; owner succeeds.

### P3 Media Deletion Endpoint

**Why:** Allow users to manage uploaded files.
**Scope:** Create `MediaDetailView` or extend upload view to support DELETE; permission = post author or media uploader. Optional cascade constraints.
**Acceptance:** DELETE returns 204; unauthorized → 403.

### P4 Negative / Denial Tests

**Why:** Harden security & regression protection.
**Scope:** Tests for: non-owner post update/delete 403, non-owner comment update/delete 403, like private post (non-owner) impossible (404 or not returned), unauthorized media upload 401.
**Acceptance:** All tests green.

### P5 Documentation Enhancements ✅ Done

**Why:** Improve API consumer clarity.
**Scope:** Add `components/schemas/ErrorValidation`, `ErrorThrottle`; annotate 400/403/404/429 responses; examples for batch media, token refresh.
**Acceptance:** Schema shows reusable error refs; examples appear in Swagger.

**✅ Status:** COMPLETE - Added comprehensive error schemas, enhanced response annotations with 400/403/404/429 coverage, batch media examples, JWT token refresh documentation. API docs accessible at `/api/docs/` with improved developer experience.

### P6 Response Envelope Standardization

**Why:** Consistent frontend handling.
**Scope:** Wrapper `{success, message, data}` for mutating endpoints; keep backward compatibility transitional period.
**Acceptance:** Documented; no existing consumer break (if any).

### P7 Central Test Settings

**Why:** Remove decorator noise; stable tests.
**Scope:** `settings_test.py` with throttles disabled & lightweight password validators; use `DJANGO_SETTINGS_MODULE` override in test run.
**Acceptance:** No per-class overrides; no throttling skips.

### P8 README & Environment

**Why:** Onboarding & deployment clarity.
**Scope:** README with setup, env vars (SECRET_KEY, DB, JWT lifetimes), run commands, test instructions, future roadmap.
**Acceptance:** File present; accurate & concise.

### P9 External Storage Prep

**Why:** Scalability & production readiness.
**Scope:** Abstract media storage config; doc placeholders for AWS S3 (django-storages) or Azure Blob.
**Acceptance:** Settings toggles; local still default.

### P10 Additional Security Tests

**Why:** Reinforce invariants.
**Scope:** Overlaps P4; ensure explicit listing for tracking.
**Acceptance:** Incorporated & passing.

### P11 /auth/me Endpoint

**Why:** Simpler client bootstrap.
**Scope:** Add view returning current user; doc & test.
**Acceptance:** GET /api/auth/me returns user.

### P12 Throttle Response Documentation

**Why:** Developer expectation management.
**Scope:** Add 429 responses for register/login/post/comment create; mention Retry-After header.
**Acceptance:** Swagger shows 429.

### P13 Cleanup of Throttle Workarounds

**Why:** Keep test code clean.
**Scope:** Remove manual monkeypatching & skip logic after P7.
**Acceptance:** Tests still green; no skip for throttling.

---

## Execution Order (Proposed)

1. P3 Media deletion endpoint + tests (next)
2. P4 Tests & Sec expansion (403/404 unauthorized cases) incl. media after P3
3. P7 Central test settings (then remove skips) & P13 cleanup
4. P1 Social login core integration (Google provider)
5. P5 Docs (error schemas) + P12 throttle responses
6. P14 Media ownership delete tests (if not folded into P4 timing)
7. P8 README
8. P11 /auth/me endpoint
9. P6 Response envelope (optional if frontend imminent)
10. P9 External storage abstraction (optional / backlog)

---

## Current Step

Next actionable item: P3 media deletion endpoint.
