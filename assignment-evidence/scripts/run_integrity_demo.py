import json
from apps.core.arango.client import get_db
from apps.core.arango.transactions import run_in_transaction
db = get_db(); out = {}
n_events = db.collection("events").count(); n_audit = db.collection("audit_log").count()
# 1. strict JSON-schema validation (BEFORE-INSERT trigger equivalent)
try:
    db.collection("events").insert({"_key": "evidence_invalid", "source": "NOT_USGS", "magnitude": 99})
    out["schema_validation"] = "ACCEPTED (unexpected)"
except Exception as e:
    out["schema_validation"] = {"rejected": True, "error_code": getattr(e, "error_code", None),
                                "message": str(getattr(e, "error_message", e))[:160]}
# 2. unique-index enforcement
full = next(db.aql.execute("FOR e IN events LIMIT 1 RETURN e"))
dup = {k: v for k, v in full.items() if k not in ("_id", "_rev")}
dup["_key"] = "evidence_dup"
try:
    db.collection("events").insert(dup)
    out["unique_index"] = "ACCEPTED (unexpected)"
except Exception as e:
    out["unique_index"] = {"rejected": True, "error_code": getattr(e, "error_code", None),
                           "message": str(getattr(e, "error_message", e))[:160]}
# 3. atomic rollback: valid audit insert + invalid event insert in one stream transaction
def work(txn):
    txn.collection("audit_log").insert({"_key": "evidence_txn_probe", "action": "evidence.rollback_probe"})
    txn.collection("events").insert({"_key": "evidence_txn_bad", "source": "NOT_USGS"})
try:
    run_in_transaction(db, work, write=["audit_log", "events"], max_attempts=1)
    out["transaction_rollback"] = "COMMITTED (unexpected)"
except Exception as e:
    out["transaction_rollback"] = {"aborted": True, "error_code": getattr(e, "error_code", None),
        "probe_doc_present_after": db.collection("audit_log").has("evidence_txn_probe")}
# 4. successful atomic commit across two collections, then clean up
def ok(txn):
    txn.collection("audit_log").insert({"_key": "evidence_txn_ok", "action": "evidence.commit_probe", "at": "2026-10-11T00:00:00.000Z"})
try:
    run_in_transaction(db, ok, write=["audit_log"], max_attempts=1)
    out["transaction_commit"] = {"committed": True, "present": db.collection("audit_log").has("evidence_txn_ok")}
except Exception as e:
    out["transaction_commit"] = {"error": str(e)[:200]}
finally:
    if db.collection("audit_log").has("evidence_txn_ok"): db.collection("audit_log").delete("evidence_txn_ok")
out["counts_unchanged"] = {"events": db.collection("events").count() == n_events, "audit_log": db.collection("audit_log").count() == n_audit}
print("QW_JSON_BEGIN" + json.dumps(out, default=str) + "QW_JSON_END")
