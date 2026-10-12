"""Read-only inventory of the live ArangoDB database (collections, counts, indexes, views, graph)."""
import base64, json, os, sys, urllib.request
sys.path.insert(0, os.path.dirname(__file__))
from run_crud_demo import _env  # noqa: E402

DB = _env("QW_ARANGO_DB")
AUTH = "Basic " + base64.b64encode(f"{_env('QW_ARANGO_USER')}:{_env('QW_ARANGO_PASSWORD')}".encode()).decode()


def get(path):
    req = urllib.request.Request(f"http://127.0.0.1:8529/_db/{DB}{path}", headers={"Authorization": AUTH})
    return json.load(urllib.request.urlopen(req, timeout=30))


def aql(query, binds=None):
    req = urllib.request.Request(f"http://127.0.0.1:8529/_db/{DB}/_api/cursor",
        data=json.dumps({"query": query, "bindVars": binds or {}}).encode(), headers={"Authorization": AUTH})
    return json.load(urllib.request.urlopen(req, timeout=60))["result"]

facts = {"database": DB, "server": get("/_api/version")["version"]}
cols = [c for c in get("/_api/collection?excludeSystem=true")["result"]]
out = []
for c in sorted(cols, key=lambda c: c["name"]):
    n = c["name"]
    count = get(f"/_api/collection/{n}/count")["count"]
    idx = [{k: i.get(k) for k in ("name", "type", "fields", "unique", "sparse", "geoJson", "expireAfter")}
           for i in get(f"/_api/index?collection={n}")["indexes"]]
    out.append({"name": n, "type": "edge" if c["type"] == 3 else "document", "count": count, "indexes": idx})
facts["collections"] = out
facts["views"] = get("/_api/view")["result"]
facts["view_properties"] = {v["name"]: get(f"/_api/view/{v['name']}/properties") for v in facts["views"]}
facts["graphs"] = get("/_api/gharial")["graphs"]
facts["analyzers"] = [a for a in get("/_api/analyzer")["result"] if not a["name"].startswith("_system::") ]
try:
    facts["aql_functions"] = get("/_api/aqlfunction")
except Exception as e:  # noqa
    facts["aql_functions"] = str(e)
facts["event_stats"] = aql("""RETURN {events: LENGTH(events), revisions: LENGTH(event_revisions),
  min_time: MIN(FOR e IN events RETURN e.occurred_at), max_time: MAX(FOR e IN events RETURN e.occurred_at),
  min_mag: MIN(FOR e IN events RETURN e.magnitude), max_mag: MAX(FOR e IN events RETURN e.magnitude)}""")[0]
facts["sample_event"] = aql("FOR e IN events SORT e.occurred_at DESC LIMIT 1 RETURN e")[0]
facts["sample_revision"] = aql("FOR r IN event_revisions LIMIT 1 RETURN UNSET(r,'payload')")[0]
json.dump(facts, open(sys.argv[1], "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print(len(out), "collections;", sum(c["count"] for c in out), "documents total")
