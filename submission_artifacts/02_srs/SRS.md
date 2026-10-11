---
title: "Software Requirements Specification: QuakeWatch"
subtitle: "Version 1 (as implemented in the working copy)"
date: "Draft for review (source-derived, 2026-10-10)"
---

**Status of this document:** DRAFT. Requirements are taken from `docs/PRD.md` (FR-01 to FR-15, section 9). Each requirement is mapped to the code that implements it in the working copy `D:\quakewatch`. *Implemented* means the code path exists and was inspected. It does **not** mean the behaviour has been demonstrated: runtime verification against a development database is pending for every item (see section 9).

# 1. Introduction

## 1.1 Purpose

This document specifies what QuakeWatch does, for whom, and under which constraints, so that the implementation can be checked against it.

## 1.2 Scope

QuakeWatch ingests earthquake data from the U.S. Geological Survey (USGS), stores it in ArangoDB as revision-aware event documents linked through a graph, and serves it through Django pages and a JSON API: dashboard, map, explorer, event detail, analytics, alerts, research exports, and operations. It does not predict earthquakes and does not issue official warnings.

## 1.3 Definitions

| Term | Meaning |
|---|------------------|
| Event | One earthquake record from a source, stored in the `events` collection |
| Revision | An immutable record of a meaningful change to an event (`event_revisions`) |
| Edge collection | An ArangoDB collection whose documents connect two other documents (`_from`, `_to`) |
| AQL | ArangoDB Query Language |
| Snapshot | A frozen research dataset with a manifest and checksum (`research_snapshots`) |

# 2. Overall description

## 2.1 User roles

| Role | Access (as enforced in code) | Evidence |
|---------|--------------------|------------|
| Visitor (anonymous) | Dashboard, map, explorer, event detail, analytics, status, about; public read APIs | `apps/web/views.py` (no login decorator on these views) |
| Registered user | Everything a visitor can do, plus alerts, research, saved searches | `@login_required` (`apps/web/views.py:60,66`); `IsAuthenticated` in `apps/alerts/api.py`, `apps/earthquakes/api.py`, `apps/research/api.py` |
| Staff (administrator) | Operations data and actions: sync, backfill, dead-letter retry, diagnostics, audit log | `IsAdminUser` in `apps/operations/api.py` (lines 72, 91, 102, 136, 171, 260) |

The Operations *page* requires login (`apps/web/views.py:84`); its data endpoints require staff status.

## 2.2 Operating environment

- Python 3.12 or newer (`pyproject.toml`), Django 6.0, Django REST Framework 3.18.
- ArangoDB 3.12.5 as the only database and stateful service (`docker-compose.yml`; `DATABASES = {}` in `config/settings.py:84`).
- A modern browser. The frontend uses server-rendered HTML, Bootstrap 5.3.8, and plain JavaScript; no frontend build step.

## 2.3 Constraints

1. ArangoDB is the only database. Accounts, sessions, the job queue, cache, metrics, and circuit-breaker state are all stored in ArangoDB (ADR-014, ADR-015).
2. AQL statements use bind variables; sort fields come from allow-lists (`CLAUDE.md` boundary rules).
3. Source values are never overwritten by derived values (ADR-010).
4. Only `apps/ingestion/adapters/` performs outbound HTTP.

# 3. Functional requirements

| ID | Requirement (PRD) | Implementing code | Status |
|----|--------------------|----------------------|---------|
| FR-01 | Scheduled USGS feed ingestion | `apps/ingestion/tasks.py:69` (`sync_feed`, task `ingestion.sync_feed`); scheduler in `apps/jobs/` | Implemented |
| FR-02 | Bounded historical backfill through the Catalog API | `apps/operations/api.py:225` (`BackfillView`); `backfill_jobs` collection | Implemented |
| FR-03 | Idempotent upserts by source and event ID | Unique index `qw_events_source_identity` (`apps/core/arango/schema.py:326`) | Implemented |
| FR-04 | Meaningful revision tracking | `event_revisions` collection; `GET /api/v1/events/{id}/revisions` | Implemented |
| FR-05 | Provenance for every sourced event | `raw_payloads` collection; `GET /api/v1/events/{id}/provenance` | Implemented |
| FR-06 | Filters: time, magnitude, depth, geography, alert, tsunami, status, network, location text | Explorer (`templates/pages/explorer.html`); text search on view `events_search` (`apps/earthquakes/repository.py:35-55`) | Implemented |
| FR-07 | Map with clustering and viewport-aware loading | `GET /api/v1/events/map`; `map_clusters` (`apps/earthquakes/services.py:213`) | Implemented |
| FR-08 | Event detail: record, revisions, provenance, relationships, products | `templates/pages/event_detail.html`; detail, revisions, provenance, relationships endpoints (`config/api_urls.py:19-22`) | Implemented |
| FR-09 | Analytics: magnitude, depth, time, region, revisions, ingestion latency | `config/api_urls.py:35-40` (summary, timeseries, distributions, breakdowns, revisions, latency) | Implemented |
| FR-10 | CRUD for user alert rules | `apps/alerts/api.py:27-50` (POST, GET, PATCH, DELETE) | Implemented |
| FR-11 | Explainable alert matches | `apps/alerts/matcher.py`; explanation stored per match (`apps/alerts/observer.py:93`) | Implemented |
| FR-12 | Saved searches | `apps/earthquakes/api.py:81-110` (create, read, update, delete, run) | Implemented |
| FR-13 | Research exports with metadata manifests | `apps/research/api.py`; SHA-256 of rows (`apps/research/manifest.py:78`) | Implemented |
| FR-14 | Admin ingestion and health dashboard | `templates/pages/operations.html`; operations endpoints (`config/api_urls.py:63-76`) | Implemented |
| FR-15 | Audit trail for administrative actions | `audit_log` collection; `_AdminAction` records before and after each action (`apps/operations/api.py:166`) | Implemented |

# 4. Non-functional requirements

| Area | Requirement (PRD section 9) | Implementation | Verification |
|---------|--------------------|--------------------|-----------|
| Reliability | No duplicate canonical records | Unique index on source identity; concurrent-ingest tests (`tests/integration/test_pipeline.py:258`) | Pending |
| Reliability | Retryable, idempotent ingestion | Exponential backoff honouring `Retry-After` (`apps/ingestion/adapters/http.py`) | Pending |
| Reliability | Enrichment failure does not block ingestion | `tests/integration/test_ingestion_services.py:296` | Pending |
| Performance | p95 of a common filtered API query under 500 ms; dashboard under 800 ms | Covering indexes (ADR-012) | **Pending.** Earlier figures were measured on synthetic data and an older source tree |
| Security | Authentication, CSRF, secure cookies, admin authorisation, validation, rate limits, secrets outside Git | See section 6 | Static inspection only |
| Observability | Structured logs, ingestion metrics, latency, error rate, query timings, freshness | `structlog`; `metric_counters`, `metric_series` collections; `/api/v1/system/freshness` | Pending |
| Reproducibility | Exports include source, query, timestamp, schema version, app version, checksum | `apps/research/manifest.py` | Pending |

# 5. External interfaces

| Interface | Description | Evidence |
|----------|--------------------|------------|
| USGS feeds (inbound) | GeoJSON summary feed, Catalog API, event detail feed, over HTTPS with timeouts and retries | `apps/ingestion/adapters/` |
| Web pages | 10 page routes and 2 account pages, server-rendered by Django templates | `apps/web/urls.py`, `apps/accounts/urls.py` |
| JSON API | Versioned under `/api/v1/`; JSON only; session authentication | `config/api_urls.py`; `config/settings.py:169-175` |
| Database | ArangoDB through `python-arango`; only repository modules and `apps/core/arango/` import it | `apps/*/repository.py` |
| Health probes | `/health/live`, `/health/ready` | `config/urls.py:6-7` |

# 6. Security requirements and implementation

- **Authentication:** Django authentication backed by ArangoDB accounts and sessions (`SESSION_ENGINE = "apps.accounts.sessions"`, `config/settings.py:97`).
- **CSRF:** session-authenticated API writes are CSRF-checked by DRF `SessionAuthentication`; forms use Django's CSRF token.
- **Authorisation:** per-view `IsAuthenticated` for user data; `IsAdminUser` for operations (section 2.1).
- **Headers:** Content Security Policy with nonces (`config/settings.py:155-163`), `X-Frame-Options: DENY`, `nosniff`, strict referrer policy.
- **Cookies:** HttpOnly and SameSite=Lax always; Secure, HSTS, and SSL redirect in production (`config/settings.py:140-152`).
- **Rate limiting:** default throttle (anonymous 120 requests/minute) plus a scoped throttle for admin actions.
- **Secrets:** read from the environment; `.env` is git-ignored; `.env.example` holds key names only.

# 7. Error handling

- API errors use one JSON envelope (`apps/core/api.py:38`).
- Error pages exist for 400, 403, 404, 500, and 503 (`templates/`).
- Ingestion records that fail are written to `dead_letters` without aborting the batch.
- Upstream failures open a circuit breaker whose state is stored in `circuit_breakers`.

# 8. Data requirements

The data model is specified in the Schema Design document (`4_Schema_Design.pdf`) and the Data Dictionary (`QuakeWatch_Data_Dictionary.xlsx`): 27 document collections, 4 edge collections, 6 JSON-schema validators, 32 named indexes, one ArangoSearch view, and one named graph.

# 9. Acceptance criteria

Each criterion is testable. The test case IDs refer to `7_TestCases.xlsx`. **None has been executed against the current working copy.**

| # | Criterion | Test case |
|----|--------------------|--------|
| AC-01 | A failed transaction leaves no partial writes | TC-02 |
| AC-02 | A committed transaction writes every collection it touched | TC-01 |
| AC-03 | Concurrent writers do not lose updates | TC-03 |
| AC-04 | An invalid ingest record is dead-lettered and the rest of the batch persists | TC-04 |
| AC-05 | A logged-in user can create, read, update, and delete an alert rule | TC-06 |
| AC-06 | A logged-in user can save, list, run, and delete a search | TC-07 |
| AC-07 | Invalid events are rejected by the database validator | TC-15 |
| AC-08 | A duplicate source identity is rejected | TC-16 |
| AC-09 | Non-staff users cannot call operations endpoints | TC-17 |
| AC-10 | Public pages show no console or CSP errors | TC-10 |

# 10. Assumptions and open items

- The USGS feeds remain available and keep their published GeoJSON schema.
- At least 500 records must be shown in the demonstration database. The current count has **not** been verified.
- Whether relational terms in the college guidelines (SQL dump, triggers, stored procedures, 3NF) accept ArangoDB equivalents is a faculty decision; see the Database Requirements and Equivalence Matrix.
