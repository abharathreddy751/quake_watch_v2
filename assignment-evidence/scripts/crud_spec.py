"""Single source of truth for the 15-request CRUD demonstration.

Used by run_crud_demo.py (executes it for real) and build_postman.py (emits the collection).
Every request hits the running QuakeWatch backend; nothing is mocked.
"""

from __future__ import annotations

BASE = "http://localhost:8000"

SAVED_SEARCH_CREATE = {
    "name": "Strong quakes M4.5+ (demo)",
    "filters": {"min_magnitude": 4.5, "sort": "magnitude", "direction": "desc"},
}
SAVED_SEARCH_PATCH = {"name": "Strong quakes M4.5+ (renamed)"}

RULE_CREATE = {
    "name": "Alaska M2.5+ watch (demo)",
    "enabled": True,
    "cooldown_minutes": 30,
    "conditions": {
        "minimum_magnitude": 2.5,
        "center": [-149.9, 61.2],
        "radius_km": 500,
    },
}
RULE_PATCH = {
    "name": "Alaska M3.0+ watch (updated)",
    "cooldown_minutes": 15,
    "conditions": {"minimum_magnitude": 3.0, "center": [-149.9, 61.2], "radius_km": 500},
}

SNAPSHOT_CREATE = {
    "title": "M4.5+ research snapshot (demo)",
    "notes": "Frozen selection created from the CRUD demonstration.",
    "filters": {"min_magnitude": 4.5, "sort": "magnitude", "direction": "desc"},
}

# `save` = {variable: dotted path into the JSON response}. `{{var}}` is substituted in path/body.
REQUESTS: list[dict] = [
    {
        "name": "Open login page (obtain CSRF cookie)",
        "op": "AUTH",
        "method": "GET",
        "path": "/accounts/login/",
        "expect": 200,
        "db": "Session middleware issues the csrftoken cookie; no DB write.",
    },
    {
        "name": "Log in (create session)",
        "op": "AUTH / CREATE session",
        "method": "POST",
        "path": "/accounts/login/",
        "form": True,
        "body": {"username": "{{username}}", "password": "{{password}}"},
        "expect": 302,
        "db": "Credentials checked against `users`; session document written to `sessions`.",
    },
    {
        "name": "System health (backend + DB connectivity)",
        "op": "READ",
        "method": "GET",
        "path": "/api/v1/system/health",
        "expect": 200,
        "db": "Pings ArangoDB and cache; reads freshness from `ingestion_runs`.",
    },
    {
        "name": "List and filter earthquake events",
        "op": "READ (filter / sort / paginate)",
        "method": "GET",
        "path": "/api/v1/events",
        "query": {
            "min_magnitude": "4.5",
            "sort": "magnitude",
            "direction": "desc",
            "page_size": "3",
        },
        "expect": 200,
        "db": "AQL over `events` with bind variables; total = full match count.",
    },
    {
        "name": "Create saved search",
        "op": "CREATE",
        "method": "POST",
        "path": "/api/v1/saved-searches",
        "body": SAVED_SEARCH_CREATE,
        "expect": 201,
        "save": {"saved_search_id": "id"},
        "db": "INSERT into `saved_searches` (per-user cap enforced atomically).",
    },
    {
        "name": "Read saved search (persistence check)",
        "op": "READ",
        "method": "GET",
        "path": "/api/v1/saved-searches/{{saved_search_id}}",
        "expect": 200,
        "db": "Document fetched from `saved_searches` by key and owner.",
    },
    {
        "name": "Rename saved search",
        "op": "UPDATE",
        "method": "PATCH",
        "path": "/api/v1/saved-searches/{{saved_search_id}}",
        "body": SAVED_SEARCH_PATCH,
        "expect": 200,
        "db": "UPDATE of `name` and `updated_at` in `saved_searches`.",
    },
    {
        "name": "Create alert rule",
        "op": "CREATE",
        "method": "POST",
        "path": "/api/v1/alert-rules",
        "body": RULE_CREATE,
        "expect": 201,
        "save": {"rule_id": "id"},
        "db": "INSERT into `alert_rules` plus `user_owns_rule` graph edge.",
    },
    {
        "name": "Update alert rule",
        "op": "UPDATE",
        "method": "PATCH",
        "path": "/api/v1/alert-rules/{{rule_id}}",
        "body": RULE_PATCH,
        "expect": 200,
        "db": "UPDATE of the rule document; validated against the pydantic schema first.",
    },
    {
        "name": "Preview alert rule against stored events",
        "op": "READ",
        "method": "GET",
        "path": "/api/v1/alert-rules/{{rule_id}}/preview",
        "expect": 200,
        "db": "Geo/magnitude AQL over `events` using the stored rule conditions.",
    },
    {
        "name": "Create research snapshot",
        "op": "CREATE",
        "method": "POST",
        "path": "/api/v1/research/snapshots",
        "body": SNAPSHOT_CREATE,
        "expect": 201,
        "save": {"snapshot_id": "id"},
        "db": "Freezes matching event revisions into `research_snapshots` with a SHA-256 checksum.",
    },
    {
        "name": "Delete research snapshot",
        "op": "DELETE",
        "method": "DELETE",
        "path": "/api/v1/research/snapshots/{{snapshot_id}}",
        "expect": 204,
        "db": "REMOVE from `research_snapshots`.",
    },
    {
        "name": "Delete alert rule",
        "op": "DELETE",
        "method": "DELETE",
        "path": "/api/v1/alert-rules/{{rule_id}}",
        "expect": 204,
        "db": "REMOVE rule and its `user_owns_rule` edge.",
    },
    {
        "name": "Delete saved search",
        "op": "DELETE",
        "method": "DELETE",
        "path": "/api/v1/saved-searches/{{saved_search_id}}",
        "expect": 204,
        "db": "REMOVE from `saved_searches`.",
    },
    {
        "name": "Verify deletion (expect 404)",
        "op": "READ (negative)",
        "method": "GET",
        "path": "/api/v1/saved-searches/{{saved_search_id}}",
        "expect": 404,
        "db": "Lookup returns no document, proving the DELETE persisted.",
    },
]
