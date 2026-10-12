"""Run the 7-operation saved-search CRUD demonstration and record the real status codes."""
import http.cookiejar, json, sys, urllib.error, urllib.parse, urllib.request
B = "http://localhost:8000"
jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
tok = lambda: next(c.value for c in jar if c.name == "csrftoken")
op.open(B + "/accounts/login/").read()
req = urllib.request.Request(B + "/accounts/login/", urllib.parse.urlencode(
    {"username": "qw_demo", "password": "QuakeDemo#2026!Zx", "csrfmiddlewaretoken": tok()}).encode(),
    headers={"Referer": B + "/accounts/login/"})
op.open(req).read()
def call(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(B + path, data, method=method, headers={
        "Content-Type": "application/json", "Accept": "application/json", "X-CSRFToken": tok()})
    try:
        resp = op.open(r)
    except urllib.error.HTTPError as e:
        resp = e
    raw = resp.read().decode()
    return resp.status, (json.loads(raw) if raw else None)
res = []
s, b = call("POST", "/api/v1/saved-searches", {"name": "Strong earthquakes M4.5+", "filters": {"min_magnitude": 4.5, "sort": "magnitude", "direction": "desc"}})
sid = b["id"]; res.append(("Create saved search", "POST", s, 201))
s, b = call("GET", "/api/v1/saved-searches"); res.append(("List saved searches", "GET", s, 200)); assert any(x["id"] == sid for x in b["results"])
s, b = call("GET", f"/api/v1/saved-searches/{sid}"); res.append(("Read saved search by id", "GET", s, 200))
s, b = call("PATCH", f"/api/v1/saved-searches/{sid}", {"name": "Strong earthquakes M4.5+ (renamed)"}); res.append(("Update (rename) saved search", "PATCH", s, 200)); assert b["name"].endswith("(renamed)")
s, b = call("GET", f"/api/v1/saved-searches/{sid}/events?page_size=2"); res.append(("Run saved search on earthquake data", "GET", s, 200)); total = b["total"]
s, b = call("DELETE", f"/api/v1/saved-searches/{sid}"); res.append(("Delete saved search", "DELETE", s, 204))
s, b = call("GET", f"/api/v1/saved-searches/{sid}"); res.append(("Verify deletion", "GET", s, 404))
out = [{"n": i, "operation": n, "method": m, "status": s, "expected": e, "ok": s == e} for i, (n, m, s, e) in enumerate(res, 1)]
json.dump({"matching_events_total": total, "results": out}, open(sys.argv[1], "w"), indent=2)
for o in out: print(o)
