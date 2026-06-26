# Scalable Architecture Conversion Plan

## Plain-language summary

This plan is about reorganizing the project so each major business area can grow on its own. Today, several parts of the site are stored together even though they do different jobs: public website pages, shipment tracking, admin screens, database work, scripts, tests, and deployment files. The target structure separates those areas into independent modules with clear shared libraries, so the team can later deploy or scale the busiest parts separately if needed.

In simple terms, the final project should feel like a well-organized office:

- Website pages go in the website area.
- Shipment tracking goes in the tracking area.
- Admin tools go in the admin area.
- Shared setup, security, health checks, and error handling go in a platform area.
- Database, storage, cache, and outside-service connections go in reusable infrastructure packages.
- Each major area gets its own tests and API contracts, while operations scripts, deployment files, and documentation each get predictable folders.

The plan also recommends doing the work in small safe steps, starting with internal cleanup that should not change what customers or admins see. After each step, the existing tests should be run so the team can confirm the site still behaves the same.

## 1. Current Repository Position

This repository is a Flask web application for Gram SCS IT Department with public marketing pages, shipment tracking, admin workflows, database models, static assets, tests, deployment configuration, and operational scripts.

### 1.1 Current top-level responsibilities

| Current path | Current responsibility | Scalability concern |
| --- | --- | --- |
| `app/` | Flask application package containing app factory, models, admin routes, frontend routes, services, templates, and static assets. | Multiple architectural layers are mixed inside one package. Application bootstrap, infrastructure configuration, models, HTTP routes, and business logic are not clearly separated. |
| `app/__init__.py` | App factory, environment loading, database setup, cache/rate limiter setup, security headers, health routes, error handlers, development seeding, blueprint registration. | Too many reasons to change. Should be split into extensions, config, bootstrap, health, errors, security, and seed modules. |
| `app/models.py` | SQLAlchemy models for consignments, leads, and newsletter subscribers. | All domain models live in one file and are coupled to Flask-SQLAlchemy. Domain areas should own their persistence models. |
| `app/admin/` | Admin blueprint, auth helpers, auth routes, consignment controller, admin dashboard/lead routes. | Admin routes contain persistence queries, serialization, file/POD handling, and response formatting in controller files. |
| `app/frontend/routes/` | Public route blueprints for main pages, dynamic static pages, and shipment tracking. | The route structure is partially modular, but business rules and persistence access still live in handlers. |
| `app/templates/` | Shared/admin/error/layout/partial templates. | Some public templates also exist under blueprint-local template folders, causing duplicate template locations. |
| `app/frontend/routes/*/templates/` | Blueprint-local templates for main, marketing pages, and track. | Template ownership is split between global and blueprint-local structures without a single convention. |
| `app/static/` | Images, fonts, JavaScript, legacy CSS, newer `assets/css` hierarchy. | Assets are split between legacy and newer conventions. CSS has duplicate page naming such as `about` and `about-us`, plus both global and page-specific roots. |
| `app/services/` | Logistics helper and POD reingest reporting. | Services are not organized by domain/use case. |
| `track/` | Standalone tracking prototype/static contract/backend adapter examples. | Duplicates the in-app tracking feature and should become reference documentation, contract fixtures, or be removed after migration. |
| `tests/` | Pytest tests, contract tests, and Playwright UI tests. | Tests are mostly feature-oriented but not aligned with future package boundaries. |
| `scripts/` | Maintenance, migration, reingest, and local browser-test helper scripts. | Scripts are useful but should be grouped by operational category and reuse application services. |
| `specs/` | JSON Schemas for consignment API contracts. | Good contract location, but should be integrated into API versioning and tests. |
| Root Python files | `run.py`, DB init/seed/backup/migration helper scripts, `gunicorn.conf.py`, local compatibility file `jsonschema.py`. | Operational scripts and runtime entrypoints are mixed at root. Root should stay small. |
| Root JS/config files | Playwright package files and config. | Fine at root, but UI test assets should live under test tooling structure. |
| Runtime/local artifacts | `test.db`, `server.log`, `local_gunicorn.log`, `website structure diagrams`. | Runtime artifacts should not be source-controlled architecture inputs. |

## 2. Current architectural observations

1. **The app factory is overloaded.** It currently owns environment-file loading, database URI validation, SQLAlchemy options, rate-limit setup, security headers, development data seeding, health endpoints, and error handlers.
2. **Routes directly perform business and persistence work.** Contact submission, newsletter subscription, consignment lookup, backup generation, and admin operations are implemented inside route handlers instead of use-case services.
3. **Models are centralized instead of domain-owned.** Consignment, lead, and newsletter persistence concerns all live in `app/models.py`.
4. **Template and asset organization is inconsistent.** The project has both global templates and blueprint-local templates; CSS is split between `app/static/css` and `app/static/assets/css`.
5. **Admin, public website, and tracking are distinct bounded contexts.** They should become separate feature modules with clear APIs and shared infrastructure.
6. **Standalone `track/` appears to be a previous or parallel tracking implementation.** It should be preserved as migration reference first, then converted into docs/contracts or retired.
7. **Tests already provide a safety net.** Existing unit/integration/contract/UI tests should be retained and reorganized after the production code is modularized.

## 3. Target architecture principles

The conversion should move toward a modular, service-ready architecture instead of a monolithic tree. The first step can still run as one Flask deployment for safety, but the folder boundaries should be shaped as if website, tracking, admin, and API capabilities may later become independently deployed services.

Core principles:

- **Service-ready feature boundaries:** group code by independently scalable business capability, not by technical type only.
- **Thin controllers:** Flask routes validate HTTP input/output and delegate to application services.
- **Domain/application separation:** business decisions live outside Flask request handlers.
- **Reusable infrastructure packages:** database, cache, rate limiting, file storage, config, and external HTTP clients are behind shared adapters that services can reuse.
- **Single template convention:** either global templates by feature or blueprint-owned templates, but not an accidental mix.
- **Versioned APIs and contracts:** website, tracking, and admin APIs should expose versioned contracts so they can evolve independently.
- **Operational code separated from app code:** migrations, maintenance jobs, and one-off scripts should live under predictable operations folders.
- **Test mirrors source boundaries:** tests should map to unit, integration, contract, and E2E layers.

## 4. Final folder architecture

The proposed final structure is below. It is designed as a modular, service-ready path tree: each business capability has its own application boundary, while shared packages hold reusable platform and infrastructure code.

```text
.
├── apps/
│   ├── web/
│   │   ├── __init__.py
│   │   ├── factory.py
│   │   ├── routes.py
│   │   ├── templates/
│   │   │   ├── layouts/
│   │   │   ├── pages/
│   │   │   ├── partials/
│   │   │   └── website/
│   │   └── static/
│   │       ├── assets/
│   │       │   ├── fonts/
│   │       │   ├── images/
│   │       │   └── vendor/
│   │       ├── css/
│   │       │   ├── base/
│   │       │   ├── components/
│   │       │   ├── layouts/
│   │       │   ├── pages/
│   │       │   ├── themes/
│   │       │   └── utilities/
│   │       └── js/
│   │           ├── components/
│   │           ├── pages/
│   │           └── shared/
│   ├── admin/
│   │   ├── __init__.py
│   │   ├── factory.py
│   │   ├── routes.py
│   │   ├── templates/
│   │   │   └── admin/
│   │   └── static/
│   │       ├── css/
│   │       └── js/
│   ├── tracking/
│   │   ├── __init__.py
│   │   ├── factory.py
│   │   ├── routes.py
│   │   ├── api.py
│   │   ├── templates/
│   │   │   └── tracking/
│   │   └── static/
│   │       ├── css/
│   │       └── js/
│   └── api_gateway/
│       ├── __init__.py
│       ├── factory.py
│       ├── routes.py
│       └── v1/
│           ├── __init__.py
│           ├── admin.py
│           ├── consignments.py
│           ├── tracking.py
│           └── website.py
├── services/
│   ├── admin/
│   │   ├── __init__.py
│   │   ├── auth/
│   │   │   ├── __init__.py
│   │   │   ├── policies.py
│   │   │   └── service.py
│   │   ├── backups/
│   │   │   ├── __init__.py
│   │   │   └── service.py
│   │   ├── consignments/
│   │   │   ├── __init__.py
│   │   │   ├── models.py
│   │   │   ├── repository.py
│   │   │   ├── schemas.py
│   │   │   └── service.py
│   │   └── leads/
│   │       ├── __init__.py
│   │       ├── repository.py
│   │       └── service.py
│   ├── tracking/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── pod_service.py
│   │   ├── repository.py
│   │   ├── schemas.py
│   │   └── service.py
│   ├── website/
│   │   ├── __init__.py
│   │   ├── contact/
│   │   │   ├── __init__.py
│   │   │   ├── models.py
│   │   │   ├── repository.py
│   │   │   ├── schemas.py
│   │   │   └── service.py
│   │   ├── newsletter/
│   │   │   ├── __init__.py
│   │   │   ├── models.py
│   │   │   ├── repository.py
│   │   │   ├── schemas.py
│   │   │   └── service.py
│   │   └── pages/
│   │       ├── __init__.py
│   │       └── registry.py
│   └── logistics/
│       ├── __init__.py
│       ├── eta.py
│       └── routing.py
├── packages/
│   ├── platform/
│   │   ├── __init__.py
│   │   ├── app_factory.py
│   │   ├── config/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── database.py
│   │   │   ├── development.py
│   │   │   ├── production.py
│   │   │   └── testing.py
│   │   ├── errors.py
│   │   ├── health.py
│   │   ├── logging.py
│   │   ├── rate_limits.py
│   │   ├── security_headers.py
│   │   └── startup.py
│   ├── infrastructure/
│   │   ├── __init__.py
│   │   ├── cache/
│   │   │   ├── __init__.py
│   │   │   └── filesystem_cache.py
│   │   ├── database/
│   │   │   ├── __init__.py
│   │   │   ├── extensions.py
│   │   │   ├── maintenance.py
│   │   │   └── migrations.py
│   │   ├── http/
│   │   │   ├── __init__.py
│   │   │   └── client.py
│   │   └── storage/
│   │       ├── __init__.py
│   │       ├── local_storage.py
│   │       └── pod_storage.py
│   └── common/
│       ├── __init__.py
│       ├── constants.py
│       ├── datetime.py
│       ├── pagination.py
│       ├── responses.py
│       ├── serialization.py
│       └── validation.py
├── migrations/
│   ├── versions/
│   └── README.md
├── operations/
│   ├── scripts/
│   │   ├── database/
│   │   ├── maintenance/
│   │   ├── reingest/
│   │   └── testing/
│   ├── sql/
│   └── seeds/
├── contracts/
│   ├── admin/
│   ├── openapi/
│   ├── tracking/
│   └── website/
├── docs/
│   ├── architecture/
│   ├── decisions/
│   ├── deployment/
│   └── runbooks/
├── tests/
│   ├── admin/
│   │   ├── unit/
│   │   └── integration/
│   ├── tracking/
│   │   ├── unit/
│   │   ├── integration/
│   │   └── contract/
│   ├── website/
│   │   ├── unit/
│   │   └── integration/
│   ├── e2e/
│   └── fixtures/
├── deploy/
│   ├── admin/
│   ├── api_gateway/
│   ├── render.yaml
│   ├── tracking/
│   ├── web/
│   └── worker/
├── tools/
│   ├── local-dev/
│   └── playwright/
├── instance/
├── run.py
├── requirements.txt
├── requirements-dev.txt
├── package.json
├── package-lock.json
├── playwright.config.js
├── pytest.ini
└── README.md
```

## 5. File-by-file migration map

### 5.1 Application bootstrap and configuration

| Current file | Final location | Final purpose |
| --- | --- | --- |
| `app/__init__.py` | `run.py` + `apps/web/factory.py` initially, with optional `apps/admin/factory.py`, `apps/tracking/factory.py`, and `apps/api_gateway/factory.py` later | Keep `create_app` compatibility through `run.py` first; move app creation into app-specific factories so web, admin, tracking, and API can later run separately. |
| `app/config.py` | `packages/platform/config/base.py`, `development.py`, `production.py`, and `testing.py` | Split environment-specific configuration into reusable platform config. |
| Database URI helpers in `app/__init__.py` | `packages/platform/config/database.py` | Own database URL normalization, production validation, SQLite fallback, and SQLAlchemy engine options. |
| `CacheShim` in `app/__init__.py` | `packages/infrastructure/cache/filesystem_cache.py` | Keep cache implementation isolated. |
| `db`, `limiter`, `cache` globals | `packages/infrastructure/database/extensions.py` | Shared extension registry that each app boundary can import without depending on one global application package. |
| Security header functions in `app/__init__.py` | `packages/platform/security_headers.py` | Register security headers through a dedicated bootstrap function. |
| Health routes in `app/__init__.py` | `packages/platform/health.py` | Reusable health blueprint for each deployable app boundary. |
| Error handlers in `app/__init__.py` | `packages/platform/errors.py` | Dedicated error registration module. |
| Development seed function in `app/__init__.py` | `operations/seeds/development_consignments.py` or `packages/platform/startup.py` | Make seeding explicit and reusable. |
| `app/db_maintenance.py` | `packages/infrastructure/database/maintenance.py` | Database schema repair/maintenance utilities. |

### 5.2 Domain models and persistence

| Current file | Final location | Final purpose |
| --- | --- | --- |
| `app/models.py` | `packages/infrastructure/database/models.py` initially | Temporary compatibility aggregate only during transition; final model ownership belongs to service packages. |
| `Consignment` model | `services/tracking/models.py` or `services/admin/consignments/models.py` | Consignment persistence model owned by tracking/admin consignment services, not by route packages. |
| `Lead` model | `services/website/contact/models.py` | Contact lead persistence. |
| `NewsletterSubscriber` model | `services/website/newsletter/models.py` | Newsletter persistence. |
| `app/frontend/routes/track/models.py` | Merge into `services/tracking/models.py` | Remove separate track model wrapper if it duplicates `Consignment`. |

### 5.3 Admin module

| Current file | Final location | Final purpose |
| --- | --- | --- |
| `app/admin/__init__.py` | `apps/admin/__init__.py` + `services/admin/__init__.py` | Admin application boundary and admin service package registration. |
| `app/admin/auth.py` | `apps/admin/auth/decorators.py` + `services/admin/auth/service.py` | Split request decorators from authentication decisions. |
| `app/admin/auth_routes.py` | `apps/admin/routes.py` or `apps/admin/auth/routes.py` | Admin login/logout routes. |
| `app/admin/routes.py` | `apps/admin/routes.py`, with business logic in `services/admin/leads/` and `services/admin/backups/` | Split dashboard, leads, and backup endpoints. |
| `app/admin/consignment_controller.py` | `apps/admin/routes.py`, `services/admin/consignments/service.py`, `repository.py`, and `schemas.py` | Move persistence, validation, serialization, import/export, archive, and POD logic out of one controller. |
| `app/templates/admin/*` | `apps/admin/templates/admin/*` | Keep admin templates grouped under the admin app boundary. |
| `app/static/js/admin/*` | `apps/admin/static/js/*` | Keep admin JavaScript grouped by admin feature. |

### 5.4 Public website module

| Current file | Final location | Final purpose |
| --- | --- | --- |
| `app/frontend/routes/main/routes.py` | `apps/web/routes.py`, with business logic in `services/website/contact/` and `services/website/newsletter/` | Split website endpoints from contact/newsletter business services. |
| `app/frontend/routes/pages/routes.py` | `services/website/pages/registry.py` plus `apps/web/routes.py` | Dynamic marketing page renderer with allowlist or page registry. |
| `app/frontend/routes/main/templates/main/index.html` | `apps/web/templates/website/index.html` | Home page. |
| `app/frontend/routes/main/templates/main/leads.html` | Review and move to `apps/admin/templates/admin/leads.html` or remove if duplicate | Lead display should be admin-owned, not public website-owned. |
| `app/frontend/routes/main/templates/main/consignments.html` | Review and move to `apps/admin/templates/admin/consignments.html` or remove if duplicate | Consignment management should be admin-owned. |
| `app/frontend/routes/pages/templates/pages/*` | `apps/web/templates/pages/*` | Marketing service pages. |
| `app/templates/main/*` | Consolidate into `apps/web/templates/website/*` or remove duplicates | Avoid two competing `main/index.html` and `about.html` locations. |
| `app/templates/partials/*` | `apps/web/templates/partials/*` | Shared website partials move with the web app boundary. |
| `app/templates/layouts/*` | `apps/web/templates/layouts/*` | Shared website layouts move with the web app boundary. |

### 5.5 Tracking module

| Current file | Final location | Final purpose |
| --- | --- | --- |
| `app/frontend/routes/track/routes.py` | `apps/tracking/routes.py`, `apps/tracking/api.py`, `services/tracking/service.py`, `repository.py`, and `schemas.py` | Split page route, JSON API, POD response, validation, and DB access. |
| `app/frontend/routes/track/templates/track/track.html` | `apps/tracking/templates/tracking/track.html` | Tracking page template. |
| `track/index.html`, `track/track.css`, `track/track.js` | `docs/architecture/tracking-prototype/` during migration, then remove or merge into app templates/static assets | Preserve as reference only while migrating. |
| `track/api-contract.json` | `contracts/jsonschema/tracking-api-contract.json` or `contracts/openapi/tracking.yaml` | Tracking API contract. |
| `track/backend/*` | `docs/architecture/tracking-prototype/backend-examples/` or remove after migration | Example adapters should not remain production source. |
| `app/static/js/track*.js` | `apps/tracking/static/js/` | Tracking JavaScript owned by the tracking app boundary. |
| `app/static/assets/css/pages/main/track.css` | `apps/tracking/static/css/track.css` | Tracking CSS owned by the tracking app boundary. |

### 5.6 Services and infrastructure

| Current file | Final location | Final purpose |
| --- | --- | --- |
| `app/services/logistics.py` | `services/tracking/service.py` or `services/admin/consignments/service.py` | Move logistics calculations to a reusable logistics service so tracking and admin can share them without coupling. |
| `app/services/pod_reingest_reporting.py` | `services/admin/consignments/pod_reingest.py` or `operations/scripts/reingest/` | POD reingest reporting is an admin/ops concern. |
| External `requests` usage in routes | `packages/infrastructure/http/client.py` and module services | Keep external HTTP concerns outside controllers. |
| Local POD filesystem logic | `packages/infrastructure/storage/pod_storage.py` | One storage abstraction reusable by admin and tracking, with local files now and object storage later. |

### 5.7 Static assets

| Current path | Final location | Final purpose |
| --- | --- | --- |
| `app/static/images/*` | `apps/web/static/assets/images/*` | Centralized images. |
| `app/static/fonts/*` | `apps/web/static/assets/fonts/*` | Centralized fonts. |
| `app/static/css/*` | `apps/web/static/css/base`, `components`, `layouts`, `utilities`, `themes` | Normalize legacy global CSS. |
| `app/static/css/components/variables.css` and `app/static/css/variables.css` | `apps/web/static/css/themes/variables.css` | Single CSS variables source. |
| `app/static/assets/css/*` | Merge into `apps/web/static/css/*` | Avoid two CSS roots. |
| `app/static/assets/css/pages/*` | `apps/web/static/css/pages/<page>/<page>.css` | Page-level CSS grouped consistently. |
| `app/static/js/index.js`, `main.js`, `forms.js`, `newsletter.js` | `apps/web/static/js/pages/` and `apps/web/static/js/shared/` | Separate page-specific and shared behaviors. |
| `app/static/js/consignments.js` | `apps/admin/static/js/consignments.js` | Admin consignment behavior. |
| `app/static/js/performance.js`, `animations.js`, `menu.js` | `apps/web/static/js/shared/` or `apps/web/static/js/components/` | Shared UI scripts. |

### 5.8 Tests, contracts, and tooling

| Current path | Final location | Final purpose |
| --- | --- | --- |
| `tests/test_*.py` | `tests/integration/` or `tests/unit/` | Reclassify by whether Flask app/DB is involved. |
| `tests/contract/*` | `tests/contract/*` | Keep contract tests, update contract paths. |
| `tests/ui/*` | `tests/e2e/*` | UI tests should be under E2E. |
| `specs/*.json` | `contracts/jsonschema/*.json` | Contract schemas grouped under contracts. |
| `playwright.config.js` | `playwright.config.js` | Keep at root unless tooling requires otherwise. |
| `scripts/playwright_test_modal*.js` | `tools/playwright/` or `tests/e2e/helpers/` | Browser tooling/helpers. |

### 5.9 Operations, deployment, and root cleanup

| Current file | Final location | Final purpose |
| --- | --- | --- |
| `scripts/ensure_consignment_columns.py` | `operations/scripts/database/ensure_consignment_columns.py` | DB maintenance script. |
| `scripts/consignment_add_columns.sql` | `operations/sql/consignment_add_columns.sql` | SQL migration/repair script. |
| `scripts/reingest_pod_urls.py` | `operations/scripts/reingest/reingest_pod_urls.py` | Operational reingest job. |
| `scripts/test_save_api.py` | `tests/integration/` or `tools/local-dev/` | Convert to automated test or local dev utility. |
| `init_db.py`, `migrate_legacy_columns.py`, `backup_database.py`, `seed_data.py`, `add_dummy_data.py` | `operations/scripts/database/` and `operations/seeds/` | DB/admin scripts. |
| `render.yaml` | `deploy/render.yaml` | Deployment config. |
| `Procfile` | `deploy/Procfile` if platform supports path, otherwise root copy with source in `deploy/` | Deployment process declaration. |
| `gunicorn.conf.py` | `deploy/gunicorn.conf.py` if platform supports path, otherwise root shim importing deploy config | Gunicorn config. |
| `test.db` | `instance/` or ignored | Local runtime DB artifact. |
| `server.log`, `local_gunicorn.log` | ignored runtime logs | Do not keep in source architecture. |
| `website structure diagrams` | `docs/architecture/website-structure-diagrams.md` or remove if obsolete | Documentation artifact with a file extension. |
| `.env.example`, `.env.render.example` | keep root or move copies to `docs/deployment/` | Keep root examples for developer convenience. |

## 6. Migration phases

### Phase 0: Stabilize and document

- Add this architecture plan.
- Confirm current tests pass before refactoring.
- Add `.gitignore` coverage for logs, local DB files, virtualenvs, and runtime artifacts if missing.
- Decide whether `track/` is prototype, contract source, or production input.

### Phase 1: Extract app bootstrap without behavior changes

- Create shared extension modules under `packages/infrastructure/` for database, rate limiting, and cache.
- Create `apps/web/factory.py` first and keep `run.py`/legacy imports compatible; add `apps/admin/factory.py`, `apps/tracking/factory.py`, and `apps/api_gateway/factory.py` when ready.
- Move health routes, error handlers, and security headers to `packages/platform/`.
- Move database URL logic to `packages/platform/config/database.py`.
- Run the full pytest suite after each small extraction.

### Phase 2: Introduce feature modules while preserving routes

- Create app boundaries in `apps/admin`, `apps/web`, and `apps/tracking`, with reusable business logic in matching `services/*` packages.
- Move routes into app boundaries, keeping existing URL paths stable during the first migration.
- Add service/repository layers behind existing handlers.
- Keep compatibility imports from old paths until tests and imports are updated.

### Phase 3: Split models and persistence boundaries

- Move model classes into feature-owned modules.
- Keep a temporary `app/models.py` re-export layer for backward compatibility.
- Introduce repositories for consignment, lead, and newsletter queries.
- Remove direct `Model.query` usage from route handlers.

### Phase 4: Consolidate templates and static assets

- Choose app-specific template roots under `apps/web/templates`, `apps/admin/templates`, and `apps/tracking/templates`.
- Move blueprint-local templates into the owning app: website pages under `apps/web/templates`, admin pages under `apps/admin/templates`, and tracking pages under `apps/tracking/templates`.
- Update `render_template` calls.
- Merge legacy and new CSS into each owning app static tree, starting with `apps/web/static/css`.
- Validate pages visually and with Playwright smoke tests.

### Phase 5: Formalize APIs, contracts, and tests

- Move schemas from `specs/` and `track/api-contract.json` into `contracts/`.
- Introduce `apps/api_gateway/v1` for versioned JSON endpoints.
- Reorganize tests into `unit`, `integration`, `contract`, and `e2e`.
- Add focused unit tests for services and repositories.

### Phase 6: Operations and deployment cleanup

- Move scripts into `operations/` by category.
- Move SQL files into `operations/sql/`.
- Move deployment configuration into `deploy/` where supported.
- Remove or ignore runtime artifacts such as local logs and DB files.
- Document runbooks for backup, POD reingest, schema repair, and deployment.

## 7. Recommended final module ownership

| Business capability | Owning module | Owns |
| --- | --- | --- |
| Public website pages | `apps/web` + `services/website` | Home, service pages, contact form, newsletter signup. |
| Tracking | `apps/tracking` + `services/tracking` | Tracking page, tracking API, POD download, consignment read model. |
| Admin | `apps/admin` + `services/admin` | Login/logout, dashboard, consignment management, lead management, backups. |
| API contracts | `apps/api_gateway/v1` + `contracts/` | Stable JSON endpoints and schemas. |
| Infrastructure | `packages/infrastructure` | Database maintenance, cache, storage, HTTP clients. |
| Core platform | `packages/platform` | Health, errors, logging, rate limits, security headers, startup hooks. |

## 8. Acceptance criteria for the conversion

- `create_app()` remains backward-compatible while app-specific factories are introduced for web, admin, tracking, and API boundaries.
- Existing public URLs continue to work unless intentionally redirected.
- Existing admin URLs continue to work unless intentionally versioned or renamed.
- Route handlers no longer contain large business workflows or direct serialization logic.
- Tests are organized by layer and pass in CI/local development.
- Templates live with the app boundary that renders them.
- CSS is organized by app boundary, with the public website using `apps/web/static/css` as the first canonical convention.
- Runtime artifacts are ignored and no longer treated as source structure.
- Operational scripts are grouped and documented.
- API schemas/contracts are versioned and tested.

## 9. Suggested first implementation slice after this plan

The safest first code slice is the bootstrap extraction:

1. Add shared extension modules under `packages/infrastructure/`.
2. Move cache shim into `packages/infrastructure/cache/filesystem_cache.py`.
3. Move security header registration into `packages/platform/security_headers.py`.
4. Move health routes into `packages/platform/health.py`.
5. Move error handlers into `packages/platform/errors.py`.
6. Keep all imports backward-compatible.
7. Run the current pytest suite.

This slice reduces risk because it creates service-ready boundaries without changing public templates, routes, database schema, or user-facing behavior.
