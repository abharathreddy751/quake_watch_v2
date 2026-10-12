"""Generate CRUD_API_DEMO_GUIDE.md from the verified evidence run (no hand-typed results)."""
import json
from urllib.parse import urlsplit, parse_qsl
ev = json.load(open("../02-postman-crud-evidence/crud_run_evidence.json", encoding="utf-8"))
out = ["""# QuakeWatch CRUD API demonstration: copy-paste guide

Demo account (already created in the running app): **username `qw_demo`**, **password `QuakeDemo#2026!Zx`**.
Backend: `http://localhost:8000` (Docker stack must be up: `docker compose up -d`).

## Fastest way (recommended)
1. Postman (desktop or VS Code extension) -> Import both files from `assignment-evidence/04-postman-collection/`:
   `QuakeWatch_CRUD.postman_collection.json` and `QuakeWatch_Local.postman_environment.json`.
2. Select environment **QuakeWatch Local**.
3. Press **Send** on requests 01 -> 15 **in order**. Nothing else to type.

## How each request gets its authentication
- Request 01 sets the `csrftoken` cookie (Postman cookie jar keeps it).
- Request 02 logs in; the server sets the HttpOnly `sessionid` cookie (jar keeps it, you never copy it) and rotates `csrftoken`; the test script stores the new value in the environment variable `csrf_token`.
- Requests 05-14 (POST/PATCH/DELETE) send header `X-CSRFToken: {{csrf_token}}`; the `Cookie` header is added automatically by the jar.
- IDs (`saved_search_id`, `rule_id`, `snapshot_id`) are saved from the create responses and reused in later URLs.
- There is no bearer token / JWT in this application.

Snapshot creation is throttled to 10 per hour per user; run the full sequence at most a few times per hour.

## Per-request details (values below are from the verified run; IDs differ on every run)
"""]
for r in ev["results"]:
    u = urlsplit(r["url"]); q = dict(parse_qsl(u.query))
    path = u.path
    for var, val in (("saved_search_id", None),):
        pass
    hdr = ["Accept: application/json"]
    if r["method"] != "GET" and "login" not in path:
        hdr += ["Content-Type: application/json", "X-CSRFToken: {{csrf_token}}"]
    if "login" in path and r["method"] == "POST":
        hdr += ["Content-Type: application/x-www-form-urlencoded", "Referer: http://localhost:8000/accounts/login/"]
    body = "none"
    if r["request_body"] is not None:
        if "login" in path:
            body = "x-www-form-urlencoded:\n  username = qw_demo\n  password = QuakeDemo#2026!Zx\n  csrfmiddlewaretoken = {{csrf_token}}  (copied from the csrftoken cookie by request 01)"
        else:
            body = json.dumps(r["request_body"], indent=2, ensure_ascii=False)
    resp = r["response_body"]
    if r["n"] == 1: resp = "HTML login page"
    elif r["n"] == 2: resp = f"empty body, header Location: {r['location']}, Set-Cookie sessionid (hidden)"
    elif resp in ("", None): resp = "empty body"
    else:
        resp = json.dumps(resp, indent=2, ensure_ascii=False)
        if len(resp) > 1500: resp = resp[:1500] + "\n  ... (truncated)"
    keys = ""
    if isinstance(r["response_body"], dict):
        keys = ", ".join(r["response_body"].keys())
    out.append(f"""### REQUEST {r['n']:02d} - {r['name']}

- **Method:** {r['method']}
- **URL:** `{r['url'].split('?')[0]}` (in Postman: `{{{{base_url}}}}{path}` with the IDs from earlier responses)
- **Authorization:** session cookie (`sessionid`) from request 02; no bearer token
- **Headers:**
```
{chr(10).join(hdr)}
```
- **Query parameters:** {json.dumps(q) if q else 'none'}
- **Body:**
```
{body}
```
- **Expected status:** {r['expected']}
- **Actual verified status:** {r['actual']}
- **Expected response structure:** {keys or '(see actual response)'}
- **Actual verified response:**
```
{resp}
```
- **Database operation:** {r['db']}
- **Screenshot filename:** `{r['n']:02d}_request.png`, `{r['n']:02d}_response.png`
""")
open("../05-reports/CRUD_API_DEMO_GUIDE.md", "w", encoding="utf-8").write("\n".join(out))
