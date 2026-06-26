# Scalable Architecture Conversion Plan

## Plain-language summary

The new target is to split the project into two clear products:

- **Frontend**: all browser UI, pages, styling, scripts, and the `/track` widget UI.
- **Backend**: server routes, admin APIs, tracking lookup route, validation, security, and Supabase access.

The frontend and backend should communicate through HTTP APIs with CORS enabled. The admin panel and tracking widget should both read/write the same Supabase database instead of using an internal admin-to-tracking API bridge. The tracking experience remains the same for users, but `/track` becomes a server-side endpoint that supports the widget behavior instead of a separate full page experience.

This plan intentionally removes cache modules, compatibility shims, and legacy-style forwarding layers. The goal is clean separation of concerns with direct, understandable ownership.

## 1. Updated target decisions

1. **No `app/` or `apps/` folder in the final architecture.** The final source tree uses `backend/`, `frontend/`, `shared/`, `database/`, `contracts/`, `operations/`, `tests/`, `deploy/`, and `docs/`.
2. **Frontend is its own concern.** Templates, CSS, JavaScript, images, fonts, admin UI assets, website pages, and the tracking widget UI move under `frontend/`.
3. **Backend is its own concern.** Flask server bootstrapping, routes, admin APIs, tracking endpoints, auth, validation, security, and Supabase access move under `backend/`.
4. **CORS connects frontend and backend.** The backend exposes API endpoints and explicitly allows configured frontend origins.
5. **Supabase is the shared source of truth.** Admin management and shipment tracking both connect to the same Supabase PostgreSQL database through backend data-access modules.
6. **No admin-to-tracking API bridge.** Admin and tracking are separate server concerns that share Supabase-backed repositories, not direct feature-to-feature HTTP calls.
7. **`/track` is widget-oriented.** The server keeps a `/track` route/API surface for the widget. Client-side UI and behavior should stay visually and functionally unchanged.
8. **No cache module.** Remove cache abstractions and route caching from the target structure.
9. **No shims.** Do not keep long-lived compatibility wrapper files. During migration, move imports directly and delete old modules in the same slice when safe.
10. **Clean, current code only.** Avoid legacy proxy folders, duplicate static trees, and temporary adapters unless they are short-lived inside one refactor PR.

## 2. Current repository position

| Current path | Current responsibility | Updated concern |
| --- | --- | --- |
| `app/__init__.py` | Flask factory, config loading, database setup, rate limiting, cache setup, security headers, health routes, error handlers, seeding, blueprint registration. | Must be split into backend server bootstrap, backend config, backend extensions, backend platform routes, and backend security modules. Cache code should be removed. |
| `app/models.py` | SQLAlchemy models for consignments, leads, and newsletter subscribers. | Move to Supabase-backed backend data models/repositories. Keep the database source centralized around Supabase. |
| `app/admin/` | Admin auth, admin routes, consignment controller, backups, leads. | Move to backend admin routes/services/repositories. Admin UI assets move to frontend. |
| `app/frontend/routes/` | Server-rendered public pages, dynamic pages, and tracking page/routes. | Split browser UI into `frontend/`; backend route/API behavior into `backend/`. |
| `app/templates/` and blueprint templates | Admin, layouts, errors, partials, public pages, tracking template. | Move UI templates/views into `frontend/` by concern. Backend should only own API/server responses where required. |
| `app/static/` | Images, fonts, JavaScript, CSS, admin scripts, tracking scripts. | Move to `frontend/assets/` and `frontend/src/` with feature folders. |
| `app/services/` | Logistics and POD reingest reporting helpers. | Move business logic to backend domain services; operational reingest scripts move to operations. |
| `track/` | Standalone tracking prototype, static files, API contract, Supabase examples. | Preserve only useful Supabase contract/reference material, then fold widget UI into frontend and backend route into backend. |
| `scripts/` and root DB scripts | DB maintenance, migration, seeding, backup, reingest, local test helpers. | Move to `operations/`, grouped by database, Supabase, reingest, backup, and local testing. |
| `specs/` | JSON schemas for consignment contracts. | Move to `contracts/`, versioned by backend API/domain area. |
| `tests/` | Pytest, contract tests, UI tests. | Reorganize by backend, frontend, contract, and end-to-end concerns. |
| Runtime artifacts | `test.db`, logs, local database files. | Ignore/remove from source tree. Supabase becomes the real database target. |

## 3. Target architecture principles

- **Frontend/backend separation:** browser code and server code live in separate top-level folders.
- **API-first connection:** frontend calls backend through HTTP APIs; backend enables CORS for approved frontend origins.
- **Supabase-centered data access:** admin and tracking use the same Supabase database through shared backend repositories.
- **No cache layer:** remove cache decorators/modules until there is a measured need for caching.
- **No shims:** do clean moves and direct imports instead of long-lived compatibility wrappers.
- **Widget-first tracking:** `/track` supports the existing tracking widget outcome without changing client-side behavior or UI.
- **Clear ownership:** admin, tracking, website/contact/newsletter, Supabase, security, and operations each have explicit folders.
- **Small safe slices:** each implementation step should be independently testable and preserve current user-visible behavior unless explicitly changed.

## 4. Final folder architecture

```text
.
├── backend/
│   ├── __init__.py
│   ├── server.py
│   ├── config/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── cors.py
│   │   ├── database.py
│   │   ├── development.py
│   │   ├── production.py
│   │   └── testing.py
│   ├── extensions/
│   │   ├── __init__.py
│   │   ├── database.py
│   │   ├── limiter.py
│   │   └── supabase.py
│   ├── platform/
│   │   ├── __init__.py
│   │   ├── errors.py
│   │   ├── health.py
│   │   ├── logging.py
│   │   ├── security_headers.py
│   │   └── startup.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── admin.py
│   │       ├── consignments.py
│   │       ├── leads.py
│   │       ├── newsletter.py
│   │       └── tracking.py
│   ├── admin/
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   ├── auth/
│   │   │   ├── __init__.py
│   │   │   ├── decorators.py
│   │   │   ├── policies.py
│   │   │   └── service.py
│   │   ├── backups/
│   │   │   ├── __init__.py
│   │   │   └── service.py
│   │   ├── consignments/
│   │   │   ├── __init__.py
│   │   │   ├── repository.py
│   │   │   ├── schemas.py
│   │   │   └── service.py
│   │   └── leads/
│   │       ├── __init__.py
│   │       ├── repository.py
│   │       └── service.py
│   ├── tracking/
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   ├── repository.py
│   │   ├── schemas.py
│   │   ├── service.py
│   │   └── pod_service.py
│   ├── website/
│   │   ├── __init__.py
│   │   ├── contact/
│   │   │   ├── __init__.py
│   │   │   ├── repository.py
│   │   │   ├── schemas.py
│   │   │   └── service.py
│   │   └── newsletter/
│   │       ├── __init__.py
│   │       ├── repository.py
│   │       ├── schemas.py
│   │       └── service.py
│   └── supabase/
│       ├── __init__.py
│       ├── client.py
│       ├── consignments.py
│       ├── leads.py
│       ├── newsletter.py
│       └── storage.py
├── frontend/
│   ├── package.json
│   ├── src/
│   │   ├── admin/
│   │   │   ├── api.js
│   │   │   ├── consignments.js
│   │   │   ├── state.js
│   │   │   └── validation.js
│   │   ├── website/
│   │   │   ├── contact.js
│   │   │   ├── forms.js
│   │   │   ├── index-page.js
│   │   │   ├── newsletter.js
│   │   │   └── pages/
│   │   ├── tracking-widget/
│   │   │   ├── index.js
│   │   │   ├── track-widget.js
│   │   │   └── tooltip.js
│   │   └── shared/
│   │       ├── animations.js
│   │       ├── menu.js
│   │       └── performance.js
│   ├── styles/
│   │   ├── base/
│   │   ├── components/
│   │   ├── layouts/
│   │   ├── pages/
│   │   ├── themes/
│   │   └── utilities/
│   ├── templates/
│   │   ├── admin/
│   │   ├── errors/
│   │   ├── layouts/
│   │   ├── pages/
│   │   ├── partials/
│   │   ├── tracking-widget/
│   │   └── website/
│   └── assets/
│       ├── fonts/
│       ├── images/
│       └── vendor/
├── shared/
│   ├── __init__.py
│   ├── constants.py
│   ├── datetime.py
│   ├── pagination.py
│   ├── responses.py
│   ├── serialization.py
│   └── validation.py
├── database/
│   ├── supabase/
│   │   ├── migrations/
│   │   ├── policies/
│   │   ├── seed/
│   │   └── schema.sql
│   └── legacy/
│       └── README.md
├── contracts/
│   ├── admin/
│   ├── openapi/
│   ├── tracking/
│   └── website/
├── operations/
│   ├── scripts/
│   │   ├── backup/
│   │   ├── database/
│   │   ├── reingest/
│   │   ├── supabase/
│   │   └── testing/
│   └── sql/
├── tests/
│   ├── backend/
│   │   ├── admin/
│   │   ├── tracking/
│   │   ├── website/
│   │   └── supabase/
│   ├── frontend/
│   ├── contract/
│   ├── e2e/
│   └── fixtures/
├── deploy/
│   ├── backend/
│   ├── frontend/
│   ├── render.yaml
│   └── worker/
├── docs/
│   ├── architecture/
│   ├── decisions/
│   ├── deployment/
│   └── runbooks/
├── tools/
│   ├── local-dev/
│   └── playwright/
├── run.py
├── requirements.txt
├── requirements-dev.txt
├── playwright.config.js
├── pytest.ini
└── README.md
```

## 5. File migration map

### 5.1 Backend bootstrap, platform, and configuration

| Current file/code | Final location | Plan |
| --- | --- | --- |
| `app/__init__.py` app factory | `backend/server.py` | Move Flask creation, route registration, security setup, CORS setup, health/error registration, and extension initialization here. Do not keep a shim. |
| Environment helpers in `app/__init__.py` | `backend/config/*.py` | Split by base/development/production/testing and move database/CORS config into dedicated files. |
| Rate limiter setup | `backend/extensions/limiter.py` | Keep rate limiting if still required; remove cache dependency. |
| Cache shim and `cache.cached(...)` usage | Delete | Remove cache code and route cache decorators from target architecture. |
| Security headers | `backend/platform/security_headers.py` | Keep as backend platform setup. |
| Health routes | `backend/platform/health.py` | Keep backend health routes. |
| Error handlers | `backend/platform/errors.py` | Keep backend error handlers. |
| `run.py` | `run.py` importing `backend.server:create_app` | Update entrypoint directly; no compatibility shim. |

### 5.2 Supabase and database access

| Current file/code | Final location | Plan |
| --- | --- | --- |
| `app/models.py` | `backend/supabase/*.py` and domain repositories | Move data access to Supabase-backed repositories. Keep schema definitions/migrations under `database/supabase/`. |
| `Consignment` access | `backend/supabase/consignments.py`, `backend/admin/consignments/repository.py`, `backend/tracking/repository.py` | Admin and tracking both use the same Supabase consignment table through backend repositories. |
| `Lead` access | `backend/supabase/leads.py`, `backend/website/contact/repository.py`, `backend/admin/leads/repository.py` | Contact submission and admin lead management share Supabase. |
| `NewsletterSubscriber` access | `backend/supabase/newsletter.py`, `backend/website/newsletter/repository.py` | Newsletter writes go to Supabase. |
| SQLite/local DB helpers | `database/legacy/` during migration, then delete | Preserve only if needed for one-time migration; do not keep as runtime source of truth. |
| `scripts/consignment_add_columns.sql` | `database/supabase/migrations/` or `operations/sql/` | Convert to Supabase migration SQL. |

### 5.3 Frontend separation

| Current file/code | Final location | Plan |
| --- | --- | --- |
| `app/templates/admin/*` | `frontend/templates/admin/*` | Admin UI templates become frontend-owned. |
| `app/templates/layouts/*` | `frontend/templates/layouts/*` | Shared layouts become frontend-owned. |
| `app/templates/partials/*` | `frontend/templates/partials/*` | Shared partials become frontend-owned. |
| `app/frontend/routes/pages/templates/pages/*` | `frontend/templates/pages/*` | Public marketing pages become frontend-owned. |
| `app/frontend/routes/main/templates/main/*` | `frontend/templates/website/*` or `frontend/templates/admin/*` | Move each template to the feature that owns it. |
| `app/frontend/routes/track/templates/track/track.html` | `frontend/templates/tracking-widget/*` | Keep UI outcome the same, but treat tracking as widget UI. |
| `app/static/js/admin/*` | `frontend/src/admin/*` | Admin browser behavior. |
| `app/static/js/track-widget.js`, `track.js`, `track-tooltip.js` | `frontend/src/tracking-widget/*` | Tracking widget browser behavior; do not alter UI/functionality. |
| `app/static/js/*.js` shared/page scripts | `frontend/src/shared/*` or `frontend/src/website/*` | Move by feature ownership. |
| `app/static/css/*`, `app/static/assets/css/*` | `frontend/styles/*` | Consolidate into one frontend style system. |
| `app/static/images/*`, `app/static/fonts/*` | `frontend/assets/images/*`, `frontend/assets/fonts/*` | Static assets become frontend-owned. |

### 5.4 Admin backend

| Current file/code | Final location | Plan |
| --- | --- | --- |
| `app/admin/auth.py` | `backend/admin/auth/decorators.py`, `policies.py`, `service.py` | Split request protection, policy checks, and auth decisions. |
| `app/admin/auth_routes.py` | `backend/admin/routes.py` or `backend/api/v1/admin.py` | Keep login/logout endpoints on backend. |
| `app/admin/routes.py` | `backend/admin/routes.py`, `backend/admin/leads/service.py`, `backend/admin/backups/service.py` | Move backend admin behavior out of UI templates. |
| `app/admin/consignment_controller.py` | `backend/admin/consignments/service.py`, `repository.py`, `schemas.py`, plus routes | Keep consignment management backend-owned and Supabase-backed. |
| Admin backup generation | `backend/admin/backups/service.py` | Export data from Supabase. |

### 5.5 Tracking widget and `/track`

| Current file/code | Final location | Plan |
| --- | --- | --- |
| `app/frontend/routes/track/routes.py` | `backend/tracking/routes.py` and `backend/api/v1/tracking.py` | Keep a server-side `/track` route/API surface for the widget. |
| Tracking DB lookup | `backend/tracking/repository.py` via `backend/supabase/consignments.py` | Tracking reads the same Supabase consignment table as admin. |
| POD lookup/serving | `backend/tracking/pod_service.py` and `backend/supabase/storage.py` | Serve PODs from configured Supabase/local storage strategy. |
| `track/index.html`, `track/track.css`, `track/track.js` | Fold into `frontend/templates/tracking-widget`, `frontend/styles`, `frontend/src/tracking-widget` if still needed | Do not keep a separate standalone track app. |
| `track/api-contract.json` | `contracts/tracking/` | Preserve contract details for tracking widget backend responses. |
| `track/backend/*` Supabase examples | `docs/architecture/` or delete after extracting useful Supabase notes | Do not keep prototype backend code in runtime source. |

### 5.6 Website/contact/newsletter backend

| Current file/code | Final location | Plan |
| --- | --- | --- |
| Contact form backend code in `app/frontend/routes/main/routes.py` | `backend/website/contact/service.py`, `repository.py`, `schemas.py`, and API route | Backend validates and writes contact leads to Supabase. |
| Newsletter backend code in `app/frontend/routes/main/routes.py` | `backend/website/newsletter/service.py`, `repository.py`, `schemas.py`, and API route | Backend validates and writes newsletter subscribers to Supabase. |
| Marketing page route rendering | Frontend-owned route/static rendering strategy | Keep browser output the same while separating UI from backend APIs. |

### 5.7 Operations, contracts, and tests

| Current file/code | Final location | Plan |
| --- | --- | --- |
| `specs/*.json` | `contracts/` | Version contracts by area. |
| `scripts/*` | `operations/scripts/*` | Group scripts by backup, database, reingest, Supabase, and testing. |
| Root DB scripts | `operations/scripts/database/` or `database/supabase/` | Convert ongoing DB changes to Supabase migration flow. |
| `tests/test_*.py` | `tests/backend/*` | Backend tests by feature. |
| `tests/contract/*` | `tests/contract/*` | Contract tests for API/widget responses. |
| `tests/ui/*` | `tests/e2e/*` and `tests/frontend/*` | UI and browser tests. |

## 6. Plan of action

### Phase 0: Confirm behavior and Supabase contract

- Capture the current admin, contact/newsletter, and tracking-widget behavior before moving code.
- Confirm Supabase table names, columns, indexes, storage bucket names, and row-level security expectations.
- Decide the exact allowed CORS origins for local development, staging, and production.
- Identify every `cache.cached(...)` usage and mark it for deletion.

### Phase 1: Remove cache and prepare backend boundaries

- Delete the cache shim/module and remove route cache decorators.
- Add `backend/` skeleton with `server.py`, `config/`, `extensions/`, and `platform/`.
- Move security headers, health routes, error handlers, limiter setup, and database/CORS config into backend modules.
- Update `run.py` to call the new backend server factory directly.
- Do not leave a shim in the old location.

### Phase 2: Add Supabase data access

- Add `backend/supabase/client.py` for Supabase configuration and client creation.
- Add Supabase data modules for consignments, leads, newsletter, and storage.
- Move schema SQL and migration files into `database/supabase/`.
- Update admin and tracking repositories to use the same Supabase consignment source.

### Phase 3: Split backend feature concerns

- Move admin auth/routes/controllers into `backend/admin/`.
- Move tracking route/API/POD behavior into `backend/tracking/` and `backend/api/v1/tracking.py`.
- Move contact/newsletter server behavior into `backend/website/`.
- Keep URL behavior stable, especially `/track` for the widget.

### Phase 4: Split frontend concern

- Create `frontend/` structure for templates, scripts, styles, and assets.
- Move admin UI, website pages, partials/layouts, and tracking widget UI into frontend folders.
- Connect frontend calls to backend APIs using configured CORS.
- Keep tracking widget UI and client-side behavior unchanged.

### Phase 5: Contracts and tests

- Move schemas/contracts into `contracts/` by feature.
- Add/adjust backend tests for Supabase repositories and route behavior.
- Add/adjust contract tests for tracking widget responses.
- Add/adjust frontend/e2e tests for admin flows and `/track` widget behavior.

### Phase 6: Cleanup

- Remove old `app/`, standalone `track/`, duplicate CSS/static roots, SQLite runtime artifacts, local logs, and obsolete scripts after their contents are migrated.
- Remove any temporary migration-only files in the same PR that makes them unnecessary.
- Update README and deployment docs for separate frontend/backend setup and CORS/Supabase configuration.

## 7. Final ownership model

| Concern | Final owner |
| --- | --- |
| Browser UI, templates, CSS, JS, images, fonts | `frontend/` |
| Flask backend server, routes, CORS, security, health, errors | `backend/` |
| Admin backend behavior | `backend/admin/` |
| Tracking widget backend route and lookup behavior | `backend/tracking/` and `backend/api/v1/tracking.py` |
| Contact/newsletter backend behavior | `backend/website/` |
| Supabase client and table/storage access | `backend/supabase/` |
| Shared pure utilities | `shared/` |
| Supabase schema/migrations/policies/seeds | `database/supabase/` |
| API and widget contracts | `contracts/` |
| Operational scripts | `operations/` |
| Tests | `tests/` grouped by backend/frontend/contract/e2e |

## 8. Acceptance criteria

- Final architecture does not contain `app/` or `apps/` as source folders.
- Frontend and backend concerns are separated at the top level.
- Backend CORS is explicitly configured for approved frontend origins.
- Admin and tracking use the same Supabase database tables through backend repositories.
- No admin-to-tracking API bridge is introduced.
- `/track` remains available as a server-side route/API surface for the tracking widget.
- Tracking widget UI and client-side behavior remain unchanged.
- Cache code, cache decorators, and cache modules are removed.
- No long-lived shims or compatibility wrapper modules remain.
- Supabase schema, policies, seeds, and migrations are documented under `database/supabase/`.
- Existing public/admin behavior is preserved unless explicitly changed.
- Tests cover backend APIs, Supabase repositories, contracts, and end-to-end widget/admin behavior.

## 9. Recommended first implementation slice

The safest first code slice is:

1. Remove the cache shim and route cache decorators.
2. Create `backend/server.py`, `backend/config/`, `backend/extensions/`, and `backend/platform/`.
3. Move health, errors, security headers, limiter setup, database config, and CORS config into backend modules.
4. Update `run.py` to import the backend server factory directly.
5. Add tests that prove existing health, security headers, rate limiting, and core route registration still work.

This first slice creates the clean backend boundary without changing frontend UI, Supabase behavior, admin workflows, or the tracking widget outcome.
