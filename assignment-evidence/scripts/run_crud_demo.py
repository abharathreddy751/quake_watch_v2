"""Execute the 15-request CRUD demonstration against the running backend (stdlib only).

usage: python run_crud_demo.py USERNAME PASSWORD OUT.json
Cookies (sessionid/csrftoken) are held in memory exactly as Postman's cookie jar would; the
evidence file stores them masked.
"""

from __future__ import annotations

import base64
import http.cookiejar
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

from crud_spec import BASE, REQUESTS


# Direct ArangoDB read-back after each write/delete: proves the API call really hit the database.
DB_CHECKS = {
    2: ("auth_users + sessions after login",
        "RETURN {user_exists: LENGTH(FOR u IN auth_users FILTER u.username == @user RETURN 1) == 1,"
        " live_sessions: LENGTH(sessions)}", ["user"]),
    5: ("saved_searches document after POST",
        "RETURN KEEP(DOCUMENT('saved_searches', @id), 'name', 'filters', 'user_id')",
        ["saved_search_id"]),
    7: ("saved_searches document after PATCH",
        "RETURN KEEP(DOCUMENT('saved_searches', @id), 'name', 'updated_at')",
        ["saved_search_id"]),
    8: ("alert_rules document and owner edge after POST",
        "RETURN {rule: KEEP(DOCUMENT('alert_rules', @id), 'name', 'enabled', 'cooldown_minutes'),"
        " owner_edges: LENGTH(FOR e IN user_owns_rule FILTER e._to == CONCAT('alert_rules/', @id)"
        " OR e._from == CONCAT('alert_rules/', @id) RETURN 1)}", ["rule_id"]),
    9: ("alert_rules document after PATCH",
        "RETURN KEEP(DOCUMENT('alert_rules', @id), 'name', 'cooldown_minutes', 'conditions')",
        ["rule_id"]),
    11: ("research_snapshots document after POST",
         "RETURN {title: DOCUMENT('research_snapshots', @id).title,"
         " members: LENGTH(DOCUMENT('research_snapshots', @id).members),"
         " content_sha256: DOCUMENT('research_snapshots', @id).content_sha256}", ["snapshot_id"]),
    12: ("research_snapshots lookup after DELETE",
         "RETURN DOCUMENT('research_snapshots', @id)", ["snapshot_id"]),
    13: ("alert_rules lookup and edge count after DELETE",
         "RETURN {rule: DOCUMENT('alert_rules', @id), owner_edges: LENGTH(FOR e IN user_owns_rule"
         " FILTER e._to == CONCAT('alert_rules/', @id) OR e._from == CONCAT('alert_rules/', @id)"
         " RETURN 1)}", ["rule_id"]),
    14: ("saved_searches lookup after DELETE",
         "RETURN DOCUMENT('saved_searches', @id)", ["saved_search_id"]),
}


def _env(name: str) -> str:
    for line in open(os.path.join(os.path.dirname(__file__), "..", "..", ".env"), encoding="utf-8"):
        if line.startswith(name + "="):
            return line.split("=", 1)[1].strip().strip("\"'")
    raise SystemExit(f"{name} missing from .env")


def _aql(query: str, binds: dict):
    auth = base64.b64encode(f"{_env('QW_ARANGO_USER')}:{_env('QW_ARANGO_PASSWORD')}".encode())
    request = urllib.request.Request(
        "http://127.0.0.1:8529/_db/" + _env("QW_ARANGO_DB") + "/_api/cursor",
        data=json.dumps({"query": query, "bindVars": binds}).encode(),
        headers={"Authorization": "Basic " + auth.decode()},
    )
    return json.load(urllib.request.urlopen(request, timeout=15))["result"][0]


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):  # noqa: ANN002, ANN003
        return None


def _dig(data, path: str):
    for part in path.split("."):
        data = data[part]
    return data


def _sub(text: str, variables: dict[str, str]) -> str:
    for key, value in variables.items():
        text = text.replace("{{" + key + "}}", value)
    return text


def main(username: str, password: str, out: str) -> int:
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(jar), _NoRedirect()
    )
    variables = {"username": username, "password": password}
    results = []
    failures = 0
    for number, spec in enumerate(REQUESTS, 1):
        path = _sub(spec["path"], variables)
        if spec.get("query"):
            path += "?" + urllib.parse.urlencode(spec["query"])
        headers = {"Accept": "application/json"}
        data = None
        if spec.get("body") is not None:
            if spec.get("form"):
                form = {k: _sub(v, variables) for k, v in spec["body"].items()}
                form["csrfmiddlewaretoken"] = next(c.value for c in jar if c.name == "csrftoken")
                data = urllib.parse.urlencode(form).encode()
                headers["Content-Type"] = "application/x-www-form-urlencoded"
                headers["Referer"] = BASE + "/accounts/login/"
            else:
                data = json.dumps(spec["body"]).encode()
                headers["Content-Type"] = "application/json"
        if spec["method"] != "GET" and not spec.get("form"):
            headers["X-CSRFToken"] = next(c.value for c in jar if c.name == "csrftoken")
        request = urllib.request.Request(
            BASE + path, data=data, headers=headers, method=spec["method"]
        )
        started = time.perf_counter()
        try:
            response = opener.open(request, timeout=30)
        except urllib.error.HTTPError as error:
            response = error
        elapsed = round((time.perf_counter() - started) * 1000, 1)
        raw = response.read().decode("utf-8", "replace")
        ctype = response.headers.get("Content-Type", "")
        try:
            body = json.loads(raw) if "json" in ctype and raw else None
        except ValueError:
            body = None
        saved = {}
        if body is not None:
            for var, dotted in spec.get("save", {}).items():
                variables[var] = str(_dig(body, dotted))
                saved[var] = variables[var]
        db_state = None
        if number in DB_CHECKS:
            label, aql, names = DB_CHECKS[number]
            binds = {("user" if n == "user" else "id"): variables.get(n, username) for n in names}
            db_state = {"check": label, "aql": aql, "bind": binds, "result": _aql(aql, binds)}
        ok = response.status == spec["expect"]
        failures += not ok
        results.append(
            {
                "n": number,
                "name": spec["name"],
                "op": spec["op"],
                "method": spec["method"],
                "url": BASE + path,
                "request_body": (
                    {**spec["body"], "password": "********"}
                    if spec.get("form")
                    else spec.get("body")
                ),
                "expected": spec["expect"],
                "actual": response.status,
                "passed": ok,
                "elapsed_ms": elapsed,
                "server_ms": response.headers.get("Server-Timing", "").replace("app;dur=", ""),
                "location": response.headers.get("Location"),
                "response_body": body if body is not None else (raw[:200] if raw else ""),
                "saved": saved,
                "db_state": db_state,
                "db": spec["db"],
            }
        )
        print(f"{number:>2} {spec['method']:<6} {path:<60} {response.status} "
              f"(expected {spec['expect']}) {'PASS' if ok else 'FAIL'}")
    with open(out, "w", encoding="utf-8") as handle:
        json.dump({"passed": len(results) - failures, "total": len(results),
                   "results": results}, handle, indent=2, ensure_ascii=False)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:4]))
