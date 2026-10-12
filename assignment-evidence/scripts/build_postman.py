"""Generate the importable Postman collection + environment from crud_spec.REQUESTS.

usage: python build_postman.py USERNAME PASSWORD OUT_DIR
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from crud_spec import BASE, REQUESTS

# Extra response assertions per request number (JavaScript, run in Postman's `pm` sandbox).
CHECKS = {
    3: ["pm.expect(j.status).to.eql('ok'); pm.expect(j.database).to.eql('up');"],
    4: ["pm.expect(j.results.length).to.be.above(0);",
        "pm.expect(j.results[0].magnitude).to.be.at.least(4.5);"],
    5: ["pm.expect(j.name).to.eql('Strong quakes M4.5+ (demo)');",
        "pm.expect(j.id).to.be.a('string');"],
    6: ["pm.expect(j.id).to.eql(pm.environment.get('saved_search_id'));",
        "pm.expect(j.filters.min_magnitude).to.eql(4.5);"],
    7: ["pm.expect(j.name).to.eql('Strong quakes M4.5+ (renamed)');"],
    8: ["pm.expect(j.enabled).to.eql(true); pm.expect(j.cooldown_minutes).to.eql(30);"],
    9: ["pm.expect(j.name).to.eql('Alaska M3.0+ watch (updated)');",
        "pm.expect(j.conditions.minimum_magnitude).to.eql(3);",
        "pm.expect(j.cooldown_minutes).to.eql(15);"],
    10: ["pm.expect(j.rule.id).to.eql(pm.environment.get('rule_id'));",
         "pm.expect(j.would_match).to.be.an('array');"],
    11: ["pm.expect(j.row_count).to.be.above(0);",
         "pm.expect(j.content_sha256).to.have.lengthOf(64);"],
    15: ["pm.expect(j.error.code).to.eql('not_found');"],
}


def _url(path: str, query: dict | None) -> dict:
    raw = "{{base_url}}" + path
    url: dict = {"raw": raw, "host": ["{{base_url}}"], "path": path.lstrip("/").split("/")}
    if query:
        url["query"] = [{"key": k, "value": v} for k, v in query.items()]
        url["raw"] += "?" + "&".join(f"{k}={v}" for k, v in query.items())
    return url


def _item(n: int, spec: dict) -> dict:
    headers = [{"key": "Accept", "value": "application/json"}]
    pre = []
    request: dict = {"method": spec["method"], "header": headers, "url": _url(spec["path"], spec.get("query"))}
    if spec.get("form"):
        request["body"] = {"mode": "urlencoded", "urlencoded": [
            {"key": "csrfmiddlewaretoken", "value": "{{csrf_token}}"},
            {"key": "username", "value": "{{username}}"},
            {"key": "password", "value": "{{password}}"},
        ]}
        headers.append({"key": "Referer", "value": "{{base_url}}/accounts/login/"})
    elif spec.get("body") is not None:
        headers.append({"key": "Content-Type", "value": "application/json"})
        request["body"] = {"mode": "raw", "raw": json.dumps(spec["body"], indent=2),
                           "options": {"raw": {"language": "json"}}}
    if spec["method"] != "GET" and not spec.get("form"):
        headers.append({"key": "X-CSRFToken", "value": "{{csrf_token}}"})
    test = [f"pm.test('Status is {spec['expect']}', () => pm.response.to.have.status({spec['expect']}));"]
    if n == 1:
        test.append("pm.environment.set('csrf_token', pm.cookies.get('csrftoken'));")
        test.append("pm.test('csrftoken cookie issued', () => pm.expect(pm.cookies.has('csrftoken')).to.be.true);")
    if n == 2:  # Django rotates the CSRF cookie at login: capture the new value
        test.append("pm.environment.set('csrf_token', pm.cookies.get('csrftoken'));")
        test.append("pm.test('sessionid cookie issued (HttpOnly, held in cookie jar)', "
                    "() => pm.expect(pm.cookies.has('sessionid')).to.be.true);")
        test.append("pm.test('Redirects to dashboard', () => pm.expect(pm.response.headers.get('Location')).to.eql('/'));")
    body_checks = CHECKS.get(n, [])
    saves = spec.get("save", {})
    if body_checks or saves:
        test.append("const j = pm.response.json();")
        for var, dotted in saves.items():
            test.append(f"pm.environment.set('{var}', String(j.{dotted}));")
        for check in body_checks:
            label = check.split(";")[0][:70].replace("'", "")
            test.append(f"pm.test('{label}', () => {{ {check} }});")
    item: dict = {
        "name": f"{n:02d} — {spec['name']}",
        "request": request,
        "event": [{"listen": "test", "script": {"type": "text/javascript", "exec": test}}],
    }
    if pre:
        item["event"].insert(0, {"listen": "prerequest", "script": {"type": "text/javascript", "exec": pre}})
    if n == 2:
        item["protocolProfileBehavior"] = {"followRedirects": False}
    return item


def main(username: str, password: str, out: str) -> None:
    out_dir = Path(out)
    out_dir.mkdir(parents=True, exist_ok=True)
    collection = {
        "info": {
            "name": "QuakeWatch — 15-request CRUD demonstration",
            "description": "Real requests against the local QuakeWatch backend (Django + ArangoDB). "
                           "Run in order; IDs are captured automatically into the environment.",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        },
        "item": [_item(n, s) for n, s in enumerate(REQUESTS, 1)],
    }
    env = {
        "name": "QuakeWatch Local",
        "values": [
            {"key": "base_url", "value": BASE, "enabled": True},
            {"key": "username", "value": username, "enabled": True},
            {"key": "password", "value": password, "type": "secret", "enabled": True},
            {"key": "csrf_token", "value": "", "enabled": True},
            {"key": "saved_search_id", "value": "", "enabled": True},
            {"key": "rule_id", "value": "", "enabled": True},
            {"key": "snapshot_id", "value": "", "enabled": True},
        ],
        "_postman_variable_scope": "environment",
    }
    (out_dir / "QuakeWatch_CRUD.postman_collection.json").write_text(
        json.dumps(collection, indent=2, ensure_ascii=False), encoding="utf-8")
    (out_dir / "QuakeWatch_Local.postman_environment.json").write_text(
        json.dumps(env, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main(*sys.argv[1:4])
