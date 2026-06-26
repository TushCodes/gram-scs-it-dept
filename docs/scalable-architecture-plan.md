# Scalable Architecture Conversion Plan

## Plain-language summary

This plan is about tidying the project so it can grow without becoming harder to maintain. Today, several parts of the site are stored together even though they do different jobs: public website pages, shipment tracking, admin screens, database work, scripts, tests, and deployment files. The plan keeps the same application, but gives every major area its own clearly labeled place.

In simple terms, the final project should feel like a well-organized office:

- Website pages go in the website area.
- Shipment tracking goes in the tracking area.
- Admin tools go in the admin area.
- Shared setup, security, health checks, and error handling go in a common platform area.
- Database, storage, cache, and outside-service connections go in an infrastructure area.
- Tests, contracts, operations scripts, deployment files, and documentation each get their own predictable folders.

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

The conversion should move toward a modular monolith first. This is the safest scalable architecture for the current repository because it preserves one deployable Flask application while separating responsibilities enough to support future services if needed.

Core principles:

- **Feature-first modules:** group code by business capability, not by technical type only.
- **Thin controllers:** Flask routes validate HTTP input/output and delegate to application services.
- **Domain/application separation:** business decisions live outside Flask request handlers.
- **Infrastructure isolation:** database, cache, rate limiting, file storage, config, and external HTTP clients are behind dedicated modules.
- **Single template convention:** either global templates by feature or blueprint-owned templates, but not an accidental mix.
- **Versioned APIs and contracts:** public/admin JSON endpoints should be structured under versioned API modules.
- **Operational code separated from app code:** migrations, maintenance jobs, and one-off scripts should live under predictable operations folders.
- **Test mirrors source boundaries:** tests should map to unit, integration, contract, and E2E layers.

## 4. Final folder architecture

The proposed final structure is below. It is intentionally designed as a modular Flask monolith with clear boundaries.

```text
.
├── app/
│   ├── __init__.py
│   ├── factory.py
│   ├── extensions.py
│   ├── config/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── development.py
│   │   ├── production.py
│   │   ├── testing.py
│   │   └── database.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── errors.py
│   │   ├── health.py
│   │   ├── logging.py
│   │   ├── rate_limits.py
│   │   ├── security_headers.py
│   │   └── startup.py
│   ├── common/
│   │   ├── __init__.py
│   │   ├── constants.py
│   │   ├── datetime.py
│   │   ├── pagination.py
│   │   ├── responses.py
│   │   ├── validation.py
│   │   └── serialization.py
│   ├── infrastructure/
│   │   ├── __init__.py
│   │   ├── database/
│   │   │   ├── __init__.py
│   │   │   ├── models.py
│   │   │   ├── migrations.py
│   │   │   └── maintenance.py
│   │   ├── cache/
│   │   │   ├── __init__.py
│   │   │   └── filesystem_cache.py
│   │   ├── storage/
│   │   │   ├── __init__.py
│   │   │   ├── pod_storage.py
│   │   │   └── local_storage.py
│   │   └── http/
│   │       ├── __init__.py
│   │       └── client.py
│   ├── modules/
│   │   ├── __init__.py
│   │   ├── admin/
│   │   │   ├── __init__.py
│   │   │   ├── routes.py
│   │   │   ├── auth/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── decorators.py
│   │   │   │   ├── routes.py
│   │   │   │   └── service.py
│   │   │   ├── consignments/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── routes.py
│   │   │   │   ├── schemas.py
│   │   │   │   ├── service.py
│   │   │   │   └── repository.py
│   │   │   ├── leads/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── routes.py
│   │   │   │   ├── service.py
│   │   │   │   └── repository.py
│   │   │   └── backups/
│   │   │       ├── __init__.py
│   │   │       ├── routes.py
│   │   │       └── service.py
│   │   ├── tracking/
│   │   │   ├── __init__.py
│   │   │   ├── routes.py
│   │   │   ├── api.py
│   │   │   ├── schemas.py
│   │   │   ├── service.py
│   │   │   ├── repository.py
│   │   │   └── models.py
│   │   ├── website/
│   │   │   ├── __init__.py
│   │   │   ├── routes.py
│   │   │   ├── pages.py
│   │   │   ├── contact/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── routes.py
│   │   │   │   ├── service.py
│   │   │   │   ├── repository.py
│   │   │   │   └── schemas.py
│   │   │   └── newsletter/
│   │   │       ├── __init__.py
│   │   │       ├── routes.py
│   │   │       ├── service.py
│   │   │       ├── repository.py
│   │   │       └── schemas.py
│   │   └── api/
│   │       ├── __init__.py
│   │       └── v1/
│   │           ├── __init__.py
│   │           ├── routes.py
│   │           ├── consignments.py
│   │           └── tracking.py
│   ├── templates/
│   │   ├── admin/
│   │   ├── errors/
│   │   ├── layouts/
│   │   ├── pages/
│   │   ├── partials/
│   │   ├── tracking/
│   │   └── website/
│   └── static/
│       ├── assets/
│       │   ├── images/
│       │   ├── fonts/
│       │   └── vendor/
│       ├── css/
│       │   ├── base/
│       │   ├── components/
│       │   ├── layouts/
│       │   ├── pages/
│       │   ├── themes/
│       │   └── utilities/
│       └── js/
│           ├── admin/
│           ├── components/
│           ├── pages/
│           ├── tracking/
│           └── shared/
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
│   ├── openapi/
│   └── jsonschema/
├── docs/
│   ├── architecture/
│   ├── deployment/
│   ├── runbooks/
│   └── decisions/
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── contract/
│   ├── e2e/
│   └── fixtures/
├── deploy/
│   ├── render.yaml
│   ├── Procfile
│   └── gunicorn.conf.py
├── tools/
│   ├── playwright/
│   └── local-dev/
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
| `app/__init__.py` | `app/__init__.py` + `app/factory.py` | Keep `create_app` import-compatible in `app/__init__.py`; move app creation and blueprint registration to `factory.py`. |
| `app/config.py` | `app/config/base.py`, `app/config/development.py`, `app/config/production.py`, `app/config/testing.py` | Split environment-specific configuration. |
| Database URI helpers in `app/__init__.py` | `app/config/database.py` | Own database URL normalization, production validation, SQLite fallback, and SQLAlchemy engine options. |
| `CacheShim` in `app/__init__.py` | `app/infrastructure/cache/filesystem_cache.py` | Keep cache implementation isolated. |
| `db`, `limiter`, `cache` globals | `app/extensions.py` | Central extension registry for Flask-SQLAlchemy, Flask-Limiter, and cache. |
| Security header functions in `app/__init__.py` | `app/core/security_headers.py` | Register security headers through a dedicated bootstrap function. |
| Health routes in `app/__init__.py` | `app/core/health.py` | Dedicated health blueprint. |
| Error handlers in `app/__init__.py` | `app/core/errors.py` | Dedicated error registration module. |
| Development seed function in `app/__init__.py` | `operations/seeds/development_consignments.py` or `app/core/startup.py` | Make seeding explicit and reusable. |
| `app/db_maintenance.py` | `app/infrastructure/database/maintenance.py` | Database schema repair/maintenance utilities. |

### 5.2 Domain models and persistence

| Current file | Final location | Final purpose |
| --- | --- | --- |
| `app/models.py` | `app/infrastructure/database/models.py` initially | Temporary compatibility aggregate that imports domain models during transition. |
| `Consignment` model | `app/modules/tracking/models.py` or `app/modules/admin/consignments/models.py` | Consignment persistence model owned by the shipping/tracking domain. |
| `Lead` model | `app/modules/website/contact/models.py` | Contact lead persistence. |
| `NewsletterSubscriber` model | `app/modules/website/newsletter/models.py` | Newsletter persistence. |
| `app/frontend/routes/track/models.py` | Merge into `app/modules/tracking/models.py` | Remove separate track model wrapper if it duplicates `Consignment`. |

### 5.3 Admin module

| Current file | Final location | Final purpose |
| --- | --- | --- |
| `app/admin/__init__.py` | `app/modules/admin/__init__.py` | Admin blueprint/module registration. |
| `app/admin/auth.py` | `app/modules/admin/auth/decorators.py` + `app/modules/admin/auth/service.py` | Split request decorators from authentication decisions. |
| `app/admin/auth_routes.py` | `app/modules/admin/auth/routes.py` | Admin login/logout routes. |
| `app/admin/routes.py` | `app/modules/admin/routes.py`, `app/modules/admin/leads/routes.py`, `app/modules/admin/backups/routes.py` | Split dashboard, leads, and backup endpoints. |
| `app/admin/consignment_controller.py` | `app/modules/admin/consignments/routes.py`, `service.py`, `repository.py`, `schemas.py` | Move persistence, validation, serialization, import/export, archive, and POD logic out of one controller. |
| `app/templates/admin/*` | `app/templates/admin/*` | Keep admin templates grouped under final global template structure. |
| `app/static/js/admin/*` | `app/static/js/admin/*` | Keep admin JavaScript grouped by admin feature. |

### 5.4 Public website module

| Current file | Final location | Final purpose |
| --- | --- | --- |
| `app/frontend/routes/main/routes.py` | `app/modules/website/routes.py`, `app/modules/website/contact/routes.py`, `app/modules/website/newsletter/routes.py` | Split home/contact/newsletter endpoints. |
| `app/frontend/routes/pages/routes.py` | `app/modules/website/pages.py` | Dynamic marketing page renderer with allowlist or page registry. |
| `app/frontend/routes/main/templates/main/index.html` | `app/templates/website/index.html` | Home page. |
| `app/frontend/routes/main/templates/main/leads.html` | Review and move to `app/templates/admin/leads.html` or remove if duplicate | Lead display should be admin-owned, not public website-owned. |
| `app/frontend/routes/main/templates/main/consignments.html` | Review and move to `app/templates/admin/consignments.html` or remove if duplicate | Consignment management should be admin-owned. |
| `app/frontend/routes/pages/templates/pages/*` | `app/templates/pages/*` | Marketing service pages. |
| `app/templates/main/*` | Consolidate into `app/templates/website/*` or remove duplicates | Avoid two competing `main/index.html` and `about.html` locations. |
| `app/templates/partials/*` | `app/templates/partials/*` | Shared partials stay global. |
| `app/templates/layouts/*` | `app/templates/layouts/*` | Shared layouts stay global. |

### 5.5 Tracking module

| Current file | Final location | Final purpose |
| --- | --- | --- |
| `app/frontend/routes/track/routes.py` | `app/modules/tracking/routes.py`, `app/modules/tracking/api.py`, `service.py`, `repository.py`, `schemas.py` | Split page route, JSON API, POD response, validation, and DB access. |
| `app/frontend/routes/track/templates/track/track.html` | `app/templates/tracking/track.html` | Tracking page template. |
| `track/index.html`, `track/track.css`, `track/track.js` | `docs/architecture/tracking-prototype/` during migration, then remove or merge into app templates/static assets | Preserve as reference only while migrating. |
| `track/api-contract.json` | `contracts/jsonschema/tracking-api-contract.json` or `contracts/openapi/tracking.yaml` | Tracking API contract. |
| `track/backend/*` | `docs/architecture/tracking-prototype/backend-examples/` or remove after migration | Example adapters should not remain production source. |
| `app/static/js/track*.js` | `app/static/js/tracking/` | Tracking JavaScript grouped by feature. |
| `app/static/assets/css/pages/main/track.css` | `app/static/css/pages/tracking/track.css` | Tracking CSS grouped by page. |

### 5.6 Services and infrastructure

| Current file | Final location | Final purpose |
| --- | --- | --- |
| `app/services/logistics.py` | `app/modules/tracking/service.py` or `app/modules/admin/consignments/service.py` | Move logistics calculations to the module that owns them; keep pure functions testable. |
| `app/services/pod_reingest_reporting.py` | `app/modules/admin/consignments/pod_reingest.py` or `operations/scripts/reingest/` | POD reingest reporting is an admin/ops concern. |
| External `requests` usage in routes | `app/infrastructure/http/client.py` and module services | Keep external HTTP concerns outside controllers. |
| Local POD filesystem logic | `app/infrastructure/storage/pod_storage.py` | One storage abstraction for local files now and object storage later. |

### 5.7 Static assets

| Current path | Final location | Final purpose |
| --- | --- | --- |
| `app/static/images/*` | `app/static/assets/images/*` | Centralized images. |
| `app/static/fonts/*` | `app/static/assets/fonts/*` | Centralized fonts. |
| `app/static/css/*` | `app/static/css/base`, `components`, `layouts`, `utilities`, `themes` | Normalize legacy global CSS. |
| `app/static/css/components/variables.css` and `app/static/css/variables.css` | `app/static/css/themes/variables.css` | Single CSS variables source. |
| `app/static/assets/css/*` | Merge into `app/static/css/*` | Avoid two CSS roots. |
| `app/static/assets/css/pages/*` | `app/static/css/pages/<page>/<page>.css` | Page-level CSS grouped consistently. |
| `app/static/js/index.js`, `main.js`, `forms.js`, `newsletter.js` | `app/static/js/pages/website/` and `app/static/js/shared/` | Separate page-specific and shared behaviors. |
| `app/static/js/consignments.js` | `app/static/js/admin/consignments.js` | Admin consignment behavior. |
| `app/static/js/performance.js`, `animations.js`, `menu.js` | `app/static/js/shared/` or `app/static/js/components/` | Shared UI scripts. |

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

- Create `app/extensions.py` for `db`, `limiter`, and cache.
- Create `app/factory.py` and keep `app/__init__.py` as a compatibility import.
- Move health routes, error handlers, and security headers to `app/core/`.
- Move database URL logic to `app/config/database.py`.
- Run the full pytest suite after each small extraction.

### Phase 2: Introduce feature modules while preserving routes

- Create `app/modules/admin`, `app/modules/website`, and `app/modules/tracking`.
- Move blueprints into modules, keeping existing URL paths stable.
- Add service/repository layers behind existing handlers.
- Keep compatibility imports from old paths until tests and imports are updated.

### Phase 3: Split models and persistence boundaries

- Move model classes into feature-owned modules.
- Keep a temporary `app/models.py` re-export layer for backward compatibility.
- Introduce repositories for consignment, lead, and newsletter queries.
- Remove direct `Model.query` usage from route handlers.

### Phase 4: Consolidate templates and static assets

- Choose global template structure under `app/templates/`.
- Move blueprint-local templates into `app/templates/website`, `app/templates/pages`, and `app/templates/tracking`.
- Update `render_template` calls.
- Merge `app/static/assets/css` and `app/static/css` into one convention.
- Validate pages visually and with Playwright smoke tests.

### Phase 5: Formalize APIs, contracts, and tests

- Move schemas from `specs/` and `track/api-contract.json` into `contracts/`.
- Introduce `app/modules/api/v1` for versioned JSON endpoints.
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
| Public website pages | `app/modules/website` | Home, service pages, contact form, newsletter signup. |
| Tracking | `app/modules/tracking` | Tracking page, tracking API, POD download, consignment read model. |
| Admin | `app/modules/admin` | Login/logout, dashboard, consignment management, lead management, backups. |
| API contracts | `app/modules/api/v1` + `contracts/` | Stable JSON endpoints and schemas. |
| Infrastructure | `app/infrastructure` | Database maintenance, cache, storage, HTTP clients. |
| Core platform | `app/core` | Health, errors, logging, rate limits, security headers, startup hooks. |

## 8. Acceptance criteria for the conversion

- `create_app()` remains the single application factory entrypoint.
- Existing public URLs continue to work unless intentionally redirected.
- Existing admin URLs continue to work unless intentionally versioned or renamed.
- Route handlers no longer contain large business workflows or direct serialization logic.
- Tests are organized by layer and pass in CI/local development.
- There is one canonical location for templates.
- There is one canonical CSS architecture under `app/static/css`.
- Runtime artifacts are ignored and no longer treated as source structure.
- Operational scripts are grouped and documented.
- API schemas/contracts are versioned and tested.

## 9. Suggested first implementation slice after this plan

The safest first code slice is the bootstrap extraction:

1. Add `app/extensions.py`.
2. Move cache shim into `app/infrastructure/cache/filesystem_cache.py`.
3. Move security header registration into `app/core/security_headers.py`.
4. Move health routes into `app/core/health.py`.
5. Move error handlers into `app/core/errors.py`.
6. Keep all imports backward-compatible.
7. Run the current pytest suite.

This slice reduces risk because it does not change public templates, routes, database schema, or user-facing behavior.
