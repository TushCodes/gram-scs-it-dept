# Scalable Architecture Conversion Plan

## Plain-language summary

The target structure keeps the project easy to understand without creating a giant monolith or over-splitting it into unnecessary folders.

- **Frontend** stays separate because it owns what users see: pages, templates, styling, scripts, images, fonts, admin UI, and the tracking widget UI.
- **Everything outside `frontend/` is server-side by default.** We do not need a `backend/` folder because folders such as `admin/`, `config/`, `database/`, `services/`, and `common/` are already clearly server-side.
- **No `routes/` folder for the marketing site.** Public HTTP behavior should stay easy for a third party to find in simple top-level modules like `pages.py`, `contact.py`, and `track.py`, while admin can retain deeper structure.
- **Tracking is part of the main project.** There is no separate tracking app/folder. The `/track` server route stays available for the widget, while the widget UI remains unchanged.
- **Supabase is part of normal database access.** There is no separate Supabase source folder. Supabase client setup, migrations, and repositories are mixed into the main `database/` and feature repositories.
- **Admin and tracking use the same Supabase database.** Admin management and tracking lookup both read/write the same Supabase-backed consignment data.
- **No cache and no shims.** Cache modules, cache decorators, compatibility wrappers, and forwarding layers should be removed instead of preserved.

In simple terms: keep the browser-facing work in `frontend/`, keep the public marketing server code simple at the project root, and allow only the admin area to keep heavier backend structure because it may be split into its own deployment later.

## 1. Updated target decisions

1. **No `app/`, `apps/`, or `backend/` folder in the final architecture.** Server-side folders are top-level and named by responsibility.
2. **Frontend remains separate.** Templates, CSS, JavaScript, images, fonts, admin UI assets, website pages, and the tracking widget UI move under `frontend/`.
3. **No separate `api/` or `routes/` folder.** Public page serving, contact handling, health checks, errors, and the `/track` widget route are simple top-level server modules.
4. **No separate tracking folder.** Tracking route behavior is mixed into the main project through `track.py`, services, and database modules.
5. **No separate website folder.** Website/contact behavior is mixed into the main project through `pages.py`, `contact.py`, services, and database modules.
6. **No separate Supabase source folder.** Supabase access is part of `database/` and feature repositories, not a standalone runtime folder.
7. **Newsletter is removed from the target project.** Do not create newsletter routes, services, database modules, UI flows, contracts, or tests in the final architecture.
8. **`shared/` is renamed to `common/`.** Pure reusable helpers live in `common/`.
9. **`operations/` is eliminated.** Maintenance, backup, reingest, database, and local helper scripts live under `services/` or `tools/`, depending on whether they are runtime/business services or developer utilities.
10. **CORS connects frontend and server behavior.** The server explicitly allows configured frontend origins without introducing a routes layer.
11. **Supabase is the shared source of truth.** Admin management and shipment tracking both use the same Supabase PostgreSQL database.
12. **`/track` is widget-oriented.** The server keeps `/track` in `track.py` for the widget. Client-side UI and behavior stay visually and functionally unchanged.
13. **No cache module.** Remove cache abstractions and route caching from the target structure.
14. **No shims.** Move imports directly and delete old modules in the same slice when safe.

## 2. Current repository position

| Current path | Current responsibility | Updated concern |
| --- | --- | --- |
| `app/__init__.py` | Flask factory, config loading, database setup, rate limiting, cache setup, security headers, health routes, error handlers, seeding, blueprint registration. | Split into top-level server bootstrap, configuration, extension setup, simple public module registration, admin registration, and security modules. Cache code should be removed. |
| `app/models.py` | SQLAlchemy models for consignments and leads. | Replace runtime database access with Supabase-backed repositories under `database/` and feature services. |
| `app/admin/` | Admin auth, admin routes, consignment controller, backups, leads. | Move server-side admin behavior into `admin/`; admin UI assets move to `frontend/`. |
| `app/frontend/routes/` | Server-rendered public pages, dynamic pages, and tracking page/routes. | Move browser UI into `frontend/`; move public server behavior into simple top-level modules such as `pages.py`, `contact.py`, and `track.py`. |
| `app/templates/` and blueprint templates | Admin, layouts, errors, partials, public pages, tracking template. | Move UI templates/views into `frontend/`. Server modules should render or return responses using frontend-owned templates where needed. |
| `app/static/` | Images, fonts, JavaScript, CSS, admin scripts, tracking scripts. | Move to `frontend/assets/`, `frontend/src/`, and `frontend/styles/`. |
| `app/services/` | Logistics and POD reingest reporting helpers. | Move runtime business logic and operational service logic into top-level `services/`. |
| `track/` | Standalone tracking prototype, static files, API contract, Supabase examples. | Fold useful widget UI into `frontend/`, useful route/data rules into `track.py`, `services/`, and `database/`, then delete the standalone folder. |
| `scripts/` and root DB scripts | DB maintenance, migration, seeding, backup, reingest, local test helpers. | Move runtime/service scripts into `services/`; move developer helpers into `tools/`; move schema/migrations into `database/`. |
| `specs/` | JSON schemas for consignment contracts. | Move to `contracts/`, versioned by public/admin/widget area. |
| `tests/` | Pytest, contract tests, UI tests. | Reorganize by public server behavior, admin, services, database, frontend, contract, and end-to-end concerns. |
| Runtime artifacts | `test.db`, logs, local database files. | Ignore/remove from source tree. Supabase becomes the real database target. |

## 3. Target architecture principles

- **Frontend separation:** browser code lives in `frontend/`.
- **Server-side by responsibility:** server code lives in clear top-level folders such as `admin/`, `config/`, `database/`, `services/`, and `common/`, plus simple root modules for marketing-site behavior.
- **Marketing-first simplicity:** public HTTP behavior is not hidden in a backend-heavy `routes/` tree. It lives in approachable root modules: `pages.py`, `contact.py`, `track.py`, `health.py`, and `errors.py`.
- **Supabase-centered data access:** admin and tracking use the same Supabase database through `database/` repositories and service modules.
- **No cache layer:** remove cache decorators/modules until there is a measured need for caching.
- **No shims:** do clean moves and direct imports instead of long-lived compatibility wrappers.
- **Widget-first tracking:** `/track` supports the existing tracking widget outcome without changing client-side behavior or UI.
- **Small safe slices:** each implementation step should be independently testable and preserve current user-visible behavior unless explicitly changed.

## 4. Final folder architecture

```text
.
├── server.py
├── run.py
├── config/
│   ├── __init__.py
│   ├── base.py
│   ├── cors.py
│   ├── database.py
│   ├── development.py
│   ├── production.py
│   └── testing.py
├── extensions/
│   ├── __init__.py
│   ├── database.py
│   └── limiter.py
├── pages.py
├── contact.py
├── track.py
├── health.py
├── errors.py
├── admin/
│   ├── __init__.py
│   ├── auth.py
│   ├── policies.py
│   ├── backups.py
│   ├── consignments.py
│   └── leads.py
├── services/
│   ├── __init__.py
│   ├── consignment_service.py
│   ├── contact_service.py
│   ├── pod_service.py
│   ├── backup_service.py
│   ├── reingest_service.py
│   └── maintenance/
│       ├── backup.py
│       ├── database.py
│       ├── reingest.py
│       └── testing.py
├── database/
│   ├── __init__.py
│   ├── client.py
│   ├── consignments.py
│   ├── leads.py
│   ├── storage.py
│   ├── migrations/
│   ├── policies/
│   ├── seed/
│   ├── schema.sql
│   └── legacy/
│       └── README.md
├── common/
│   ├── __init__.py
│   ├── constants.py
│   ├── datetime.py
│   ├── pagination.py
│   ├── responses.py
│   ├── serialization.py
│   └── validation.py
├── frontend/
│   ├── package.json
│   ├── src/
│   │   ├── admin/
│   │   ├── tracking-widget/
│   │   ├── pages/
│   │   └── common/
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
│   │   └── tracking-widget/
│   └── assets/
│       ├── fonts/
│       ├── images/
│       └── vendor/
├── contracts/
│   ├── admin/
│   ├── public/
│   └── tracking-widget/
├── tests/
│   ├── public/
│   ├── admin/
│   ├── services/
│   ├── database/
│   ├── frontend/
│   ├── contract/
│   ├── e2e/
│   └── fixtures/
├── deploy/
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
├── requirements.txt
├── requirements-dev.txt
├── playwright.config.js
├── pytest.ini
└── README.md
```

## 5. File migration map

### 5.1 Server bootstrap, platform, and configuration

| Current file/code | Final location | Plan |
| --- | --- | --- |
| `app/__init__.py` app factory | `server.py` | Move Flask creation, route registration, security setup, CORS setup, health/error registration, and extension initialization here. Do not keep a shim. |
| Environment helpers in `app/__init__.py` | `config/*.py` | Split by base/development/production/testing and move database/CORS config into dedicated files. |
| Rate limiter setup | `extensions/limiter.py` | Keep rate limiting if still required; remove cache dependency. |
| Cache shim and `cache.cached(...)` usage | Delete | Remove cache code and route cache decorators from target architecture. |
| Security headers | `server.py` or a small `common/security_headers.py` helper | Keep security setup server-side without creating an extra platform folder. |
| Health routes | `health.py` | Keep health checks as a simple top-level module. |
| Error handlers | `errors.py` | Keep error handlers as a simple top-level module. |
| `run.py` | `run.py` importing `server:create_app` | Update entrypoint directly; no compatibility shim. |

### 5.2 Supabase and database access

| Current file/code | Final location | Plan |
| --- | --- | --- |
| `app/models.py` | `database/*.py` and feature services | Move data access to Supabase-backed repositories. Keep schema definitions/migrations under `database/`. |
| Supabase client creation | `database/client.py` | Create and configure the Supabase client as normal database infrastructure. |
| `Consignment` access | `database/consignments.py`, `admin/consignments.py`, `services/consignment_service.py`, `track.py` | Admin and tracking both use the same Supabase consignment table. |
| `Lead` access | `database/leads.py`, `admin/leads.py`, `services/contact_service.py` | Contact submission and admin lead management share Supabase. |
| POD/storage access | `database/storage.py`, `services/pod_service.py` | Keep storage access near database infrastructure and POD rules in services. |
| SQLite/local DB helpers | `database/legacy/` during migration, then delete | Preserve only if needed for one-time migration; do not keep as runtime source of truth. |
| `scripts/consignment_add_columns.sql` | `database/migrations/` | Convert to Supabase migration SQL. |

### 5.3 Frontend separation

| Current file/code | Final location | Plan |
| --- | --- | --- |
| `app/templates/admin/*` | `frontend/templates/admin/*` | Admin UI templates become frontend-owned. |
| `app/templates/layouts/*` | `frontend/templates/layouts/*` | Shared layouts become frontend-owned. |
| `app/templates/partials/*` | `frontend/templates/partials/*` | Shared partials become frontend-owned. |
| `app/frontend/routes/pages/templates/pages/*` | `frontend/templates/pages/*` | Public marketing pages become frontend-owned. |
| `app/frontend/routes/main/templates/main/*` | `frontend/templates/pages/*` or `frontend/templates/admin/*` | Move each template to the UI area that owns it; do not create a separate website folder. |
| `app/frontend/routes/track/templates/track/track.html` | `frontend/templates/tracking-widget/*` | Keep UI outcome the same, but treat tracking as widget UI. |
| `app/static/js/admin/*` | `frontend/src/admin/*` | Admin browser behavior. |
| `app/static/js/track-widget.js`, `track.js`, `track-tooltip.js` | `frontend/src/tracking-widget/*` | Tracking widget browser behavior; do not alter UI/functionality. |
| `app/static/js/*.js` shared/page scripts | `frontend/src/common/*` or `frontend/src/pages/*` | Move by browser-side ownership. |
| `app/static/css/*`, `app/static/assets/css/*` | `frontend/styles/*` | Consolidate into one frontend style system. |
| `app/static/images/*`, `app/static/fonts/*` | `frontend/assets/images/*`, `frontend/assets/fonts/*` | Static assets become frontend-owned. |

### 5.4 Admin server behavior

| Current file/code | Final location | Plan |
| --- | --- | --- |
| `app/admin/auth.py` | `admin/auth.py`, `admin/policies.py` | Split request protection and policy checks without over-nesting. |
| `app/admin/auth_routes.py` | `admin/routes.py` or `admin/auth.py` | Keep admin HTTP behavior inside the admin area because admin may be deployed separately later. |
| `app/admin/routes.py` | `admin/routes.py`, `admin/leads.py`, `admin/backups.py` | Keep admin endpoints and admin-specific rules together under `admin/` so future extraction is easier. |
| `app/admin/consignment_controller.py` | `admin/consignments.py`, `services/consignment_service.py`, `database/consignments.py` | Keep consignment management server-owned and Supabase-backed. |
| Admin backup generation | `admin/backups.py`, `services/backup_service.py` | Export data from Supabase. |

### 5.5 Tracking widget and `/track`

| Current file/code | Final location | Plan |
| --- | --- | --- |
| `app/frontend/routes/track/routes.py` | `track.py` | Keep a server-side `/track` route for the widget. Do not create a separate tracking or routes folder. |
| Tracking DB lookup | `database/consignments.py` through `services/consignment_service.py` | Tracking reads the same Supabase consignment table as admin. |
| POD lookup/serving | `services/pod_service.py` and `database/storage.py` | Serve PODs from configured Supabase/local storage strategy. |
| `track/index.html`, `track/track.css`, `track/track.js` | Fold into `frontend/templates/tracking-widget`, `frontend/styles`, `frontend/src/tracking-widget` if still needed | Do not keep a separate standalone track app. |
| `track/api-contract.json` | `contracts/tracking-widget/` | Preserve contract details for tracking widget route responses. |
| Supabase examples inside standalone `track/` prototype | Extract useful notes into `docs/architecture/` or delete | Do not keep prototype server code in runtime source. |

### 5.6 Website/contact behavior

| Current file/code | Final location | Plan |
| --- | --- | --- |
| Contact form server code in `app/frontend/routes/main/routes.py` | `contact.py`, `services/contact_service.py`, `database/leads.py` | Server validates and writes contact leads to Supabase. |
| Marketing page route rendering | `pages.py` rendering frontend-owned templates | Keep browser output the same without creating a separate website or routes folder. |

### 5.7 Services, contracts, and tests

| Current file/code | Final location | Plan |
| --- | --- | --- |
| `specs/*.json` | `contracts/` | Version contracts by public/admin/widget area. |
| `scripts/*` | `services/maintenance/*` or `tools/local-dev/*` | Runtime maintenance logic goes to services; developer-only helpers go to tools. |
| Root DB scripts | `database/migrations/` or `services/maintenance/database.py` | Convert ongoing DB changes to Supabase migration flow. |
| `tests/test_*.py` | `tests/public/*`, `tests/services/*`, `tests/database/*`, or `tests/admin/*` | Server tests by concern without a routes folder. |
| `tests/contract/*` | `tests/contract/*` | Contract tests for public, admin, and widget responses. |
| `tests/ui/*` | `tests/e2e/*` and `tests/frontend/*` | UI and browser tests. |

## 6. Plan of action

### Phase 0: Confirm behavior and Supabase contract

- Capture the current admin, contact, and tracking-widget behavior before moving code.
- Confirm Supabase table names, columns, indexes, storage bucket names, and row-level security expectations.
- Decide the exact allowed CORS origins for local development, staging, and production.
- Identify every `cache.cached(...)` usage and mark it for deletion.

### Phase 1: Remove cache and prepare server boundaries

- Delete the cache shim/module and remove route cache decorators.
- Add top-level `server.py`, `pages.py`, `contact.py`, `track.py`, `health.py`, `errors.py`, `config/`, `extensions/`, `common/`, `database/`, and `services/` skeletons.
- Move health checks, error handlers, limiter setup, database config, CORS config, and security setup into these server-side modules/folders.
- Update `run.py` to call the new server factory directly.
- Do not leave a shim in the old location.

### Phase 2: Add Supabase data access inside `database/`

- Add `database/client.py` for Supabase configuration and client creation.
- Add database modules for consignments, leads, and storage.
- Move schema SQL, policies, seeds, and migrations into `database/`.
- Update admin and tracking services to use the same Supabase consignment source.

### Phase 3: Split server-side concerns without over-separating

- Move admin auth, policies, and admin business rules into `admin/`.
- Move public HTTP behavior into root modules: `pages.py`, `contact.py`, `track.py`, `health.py`, and `errors.py`.
- Keep admin HTTP behavior inside `admin/` so the admin folder can later be removed from this project and deployed separately.
- Move reusable business rules into `services/`.
- Keep URL behavior stable, especially `/track` for the widget.

### Phase 4: Split frontend concern

- Create `frontend/` structure for templates, scripts, styles, and assets.
- Move admin UI, public pages, partials/layouts, and tracking widget UI into frontend folders.
- Connect frontend calls to server behavior using configured CORS.
- Keep tracking widget UI and client-side behavior unchanged.

### Phase 5: Contracts and tests

- Move schemas/contracts into `contracts/` by public/admin/widget area.
- Add/adjust public server tests for `/track`, contact, health, page rendering, and error behavior; keep admin tests under `tests/admin/`.
- Add/adjust database tests for Supabase repositories.
- Add/adjust contract tests for tracking widget responses.
- Add/adjust frontend/e2e tests for admin flows and `/track` widget behavior.

### Phase 6: Cleanup

- Remove old `app/`, standalone `track/`, duplicate CSS/static roots, SQLite runtime artifacts, local logs, and obsolete scripts after their contents are migrated.
- Remove any temporary migration-only files in the same PR that makes them unnecessary.
- Update README and deployment docs for the separated frontend, simple marketing-site server structure, admin extraction path, CORS configuration, and Supabase configuration.

## 7. Final ownership model

| Concern | Final owner |
| --- | --- |
| Browser UI, templates, CSS, JS, images, fonts | `frontend/` |
| Flask app factory and route registration | `server.py` |
| Public page/contact/track behavior, health, and errors | `pages.py`, `contact.py`, `track.py`, `health.py`, `errors.py` |
| Admin auth, policies, consignment management rules, lead management rules, backup rules | `admin/` |
| Shared runtime business logic | `services/` |
| Supabase client, table repositories, storage access, migrations, policies, seeds | `database/` |
| Shared pure utilities | `common/` |
| Public, admin, and widget contracts | `contracts/` |
| Developer-only helpers | `tools/` |
| Tests | `tests/` grouped by public/admin/services/database/frontend/contract/e2e |

## 8. Acceptance criteria

- Final architecture does not contain `app/`, `apps/`, or `backend/` as source folders.
- Frontend is separated at the top level under `frontend/`.
- Server-side code is organized by concern using simple root modules for public marketing behavior plus top-level folders such as `admin/`, `services/`, `database/`, `config/`, `extensions/`, and `common/`.
- No separate `api/`, `routes`, `tracking`, `website`, `supabase`, `shared`, or `operations` source folder is introduced.
- Newsletter route, service, database module, UI flow, contract, and tests are not introduced in the target project.
- CORS is explicitly configured for approved frontend origins.
- Admin and tracking use the same Supabase database tables through `database/` repositories and services.
- No admin-to-tracking API bridge is introduced.
- `/track` remains available from `track.py` as a server-side route for the tracking widget.
- Tracking widget UI and client-side behavior remain unchanged.
- Cache code, cache decorators, and cache modules are removed.
- No long-lived shims or compatibility wrapper modules remain.
- Supabase schema, policies, seeds, and migrations are documented under `database/`.
- Existing public/admin behavior is preserved unless explicitly changed.
- Tests cover public server behavior, Supabase database access, services, contracts, and end-to-end widget/admin behavior.

## 9. Recommended first implementation slice

The safest first code slice is:

1. Remove the cache shim and route cache decorators.
2. Create `server.py`, `pages.py`, `contact.py`, `track.py`, `health.py`, `errors.py`, `config/`, `extensions/`, `common/`, `database/`, and `services/` skeletons.
3. Move health checks, error handlers, security setup, limiter setup, database config, and CORS config into those locations.
4. Update `run.py` to import the server factory directly.
5. Add tests that prove existing health, security headers, rate limiting, and core public/admin registration still work.

This first slice creates clean server-side boundaries without creating a `backend/` folder, without changing frontend UI, without changing Supabase behavior, and without changing the tracking widget outcome.
