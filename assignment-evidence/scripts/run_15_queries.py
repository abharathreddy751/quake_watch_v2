import importlib, json, pkgutil, time
for m in ["apps.earthquakes.repository","apps.alerts.repository","apps.analytics.repository","apps.operations.repository","apps.research.repository","apps.ingestion.repository"]:
    try: importlib.import_module(m)
    except Exception as e: print("skip", m, e)
from apps.core.arango import catalog
from apps.core.arango.client import get_db
from apps.core.arango.query import run_query, explain, indexes_used
NAMES = ["analytics_avg_magnitude_by_region","analytics_dashboard_summary","analytics_network_stats",
 "analytics_magnitude_changes","analytics_ingestion_latency","analytics_significant_by_week",
 "alerts_user_rules","alerts_matched_events_graph","event_graph_relationships","events_in_viewport",
 "events_within_radius","events_location_text","ops_run_stats","analytics_depth_histogram","event_nearby_space_time"]
db = get_db(); out = []
for n, name in enumerate(NAMES, 1):
    q = catalog.get(name); binds = dict(q.sample_binds())
    if "user_id" in binds: binds["user_id"] = 2
    plan = explain(db, q.aql, binds)
    res = run_query(db, "evidence_" + name, q.aql, binds, record_metrics=False)
    rows = res.rows
    out.append({"n": n, "name": name, "category": q.category, "question": q.question, "features": list(q.features),
                "aql": q.aql, "binds": binds, "indexes_used": sorted(set(indexes_used(plan))),
                "estimated_cost": plan.get("estimatedCost"), "duration_ms": res.duration_ms,
                "row_count": len(rows), "rows": rows[:5]})
print("QW_JSON_BEGIN" + json.dumps(out, default=str) + "QW_JSON_END")
