# QuakeWatch Phase 0 — baseline report (2026-10-07, ~02:05 UTC)

**Outcome: Phase 0 baseline complete.** All gates passed; every check that was run is reported
with its real output. Raw logs: `D:\qw-baseline\reports\phase0-logs-20261007T0200Z\`.
Previous (stopped) run: `phase0-overnight-report-20261006T1715Z.md` (not modified).

## 1. Stages completed (UTC, 2026-10-07)

| Stage | Result | Evidence |
|---|---|---|
| R4.1e — `/etc/containerd/config.toml` (`disabled_plugins = ["io.containerd.grpc.v1.cri"]`) | PASS | sha256 `26993d2d…62297f1`; effective config shows CRI disabled; nothing started |
| R4.1d rerun (inner sha256 `18c4aa24…dbfbe07c`, unchanged) | PASS | `WSL_EXIT=0`; no TCP listener; graceful stop; self-bind mount released by `systemctl stop` alone |
| R4.2 — engine/network inventory before, during, after | PASS | Docker 29.1.3 (API 1.52), cgroup v2/systemd, seccomp; pools `10.214.0.0/16`; no Windows ports 2375/2376; no portproxy |
| R5 — tar-stream copy into `qwb:/srv/qwb/quakewatch` + preflight | PASS | 244 files, per-file hashes identical to `D:\quakewatch`; no `.env` (only `.env.example`, a template) |
| Engine start gate | PASS | identity, empty, no TCP listener |
| R6 — `qwb-net` (internal) + `arangodb:3.12.5` + `redis:7.4-alpine` | PASS | `internal=true`, no published ports, anonymous volumes only |
| R7 — `python:3.12-slim` (`qwb-py`): deps on temporary bridge, then internal-only | PASS | Python 3.12.15; 88 packages (`pip-freeze.txt`); final networks `qwb-net` only |
| Isolation gate (`isolation-v2.py`) + reviewed preflight | PASS | positive controls reachable; 25 blocked targets unreachable (Windows host 172.19.0.1 incl. :1521, qwb eth0, docker0, WSL DNS, LAN gateway candidates, internet); no DNS; mounts `/work` (copy) + `/tools` (ro) only; no docker socket; Arango fresh (`_system` only) |
| R8 — default test suite + coverage | **PASS** | see §3 |
| R9 — benchmark 500 / 10k / 100k (no `--write`) | **PASS** | see §4 |
| O1 — ruff check / ruff format --check / mypy | PASS | "All checks passed!"; "178 files already formatted"; "Success: no issues found in 107 source files" |
| O2 — browser + accessibility (Playwright, axe) | PASS | 58 passed in 183.8 s |
| O3 — pip-audit (requirements + dev) | PASS | "No known vulnerabilities found" |
| O4 — `manage.py check --deploy --fail-level WARNING` (throwaway prod env) | PASS | "System check identified no issues (0 silenced)" |
| O5 — `arango_migrate` + `aql_catalog` (no `--write`) | **FAIL (exit 1), unresolved** | see §5 |
| R10 — cleanup + verification | PASS | see §6 |

Deviations from the reviewed plan (none weaken a gate): containers/network carry label
`qwb.baseline=phase0` (used to verify identity before cleanup); a keepalive `sleep` session kept `qwb`
up during R6–R10 (stopped at the end); Git Bash `MSYS_NO_PATHCONV=1` for the tar extraction (first
attempt aborted before writing anything); an extra isolation probe beyond the reviewed preflight — its
first version had a prefix bug (`"/d"` matched `/dev`), fixed to exact-path matching in
`isolation-v2.py` and rerun; O2/O3 downloads done in the same temporary-bridge window as R7.

## 2. Environment
`qwb` (Ubuntu 24.04.5, WSL2 kernel 6.18.33.2) · Docker 29.1.3 (containerd snapshotter, overlayfs) ·
12 logical CPUs, 3.66 GiB VM memory · ArangoDB 3.12.5, Redis 7.4 · Python 3.12.15 · Django 6.0.9,
python-arango 8.3.6, celery 5.6.3, redis-py 6.4.0, pytest 9.1.1.

## 3. Test results (R8)
- `pytest --cov=apps --cov-report=term-missing:skip-covered --cov-report=xml --cov-fail-under=90`
  (project default markers exclude `live`, `e2e`, `perf`).
- **601 passed, 0 failed, 0 errors, 61 deselected** in 135.6 s.
- **Coverage 93.96 %** (4,421 statements, 267 missed) — requirement 90 % met.
- Lowest-covered modules: `apps/core/management/commands/aql_catalog.py` 0 %, `arango_migrate.py`
  (command) 75 %, `apps/core/locks.py` 78 % (fail-open/release-error paths, lines 36-41, 48-49),
  `arango_benchmark.py` (command) 79 %.
- e2e (O2): 58 passed. `live` tests (real USGS) intentionally not run.

## 4. Performance (R9) vs historical `docs/BENCHMARKS.md` (2026-09-25, Windows 11 + Docker Desktop, Python 3.12.0)

Same command, defaults (2 warm-up + 20 timed runs). **Scanned document counts (full/index) are
identical to the historical table in all 30 cells → identical query plans and index usage.**
Latency, with indexes, p95 ms (historical → measured, change):

| Workload | 500 | 10,000 | 100,000 |
|---|---|---|---|
| event_list_filtered | 4.9 → 4.18 (−15 %) | 6.4 → 5.24 (−18 %) | 4.9 → 5.62 (+15 %) |
| event_list_latest | 5.2 → 2.00 (−62 %) | 13.0 → 7.76 (−40 %) | 36.7 → 26.71 (−27 %) |
| geo_radius | 5.4 → 8.31 (+54 %) | 6.7 → 7.86 (+17 %) | 51.0 → 53.97 (+6 %) |
| analytics_magnitude_histogram | 3.9 → 7.51 (+93 %) | 6.7 → 7.96 (+19 %) | 7.3 → 11.66 (+60 %) |
| revision_lookup | 2.0 → 5.54 (+177 %) | 2.6 → 1.96 (−25 %) | 3.6 → 2.41 (−33 %) |

100k p50 with indexes: filtered 4.0 → 3.76 (−6 %), latest 26.8 → 24.52 (−9 %), geo 18.1 → 25.73
(+42 %), histogram 6.5 → 8.47 (+30 %), revision 2.2 → 2.00 (−9 %).
100k p95 without indexes: filtered 74.2 → 111.40 (+50 %), latest 96.4 → 130.29 (+35 %), geo 133.4 →
130.37 (−2 %), histogram 58.0 → 39.81 (−31 %), revision 72.5 → 55.11 (−24 %).

- Slowest indexed p95: **53.97 ms** (geo_radius, 100k) — PRD target p95 < 500 ms met.
- Seeding: 500 in 0.2 s, 10,000 in 6.4 s, 100,000 in 37.8 s (≈ 2,650 events/s, derived).
- Throughput (requests/s) is **not measured** by this benchmark (latency only).
- Resource samples (15 s, `docker stats`): peak qwb-arango 123.6 % CPU / 598 MiB; qwb-py 98.5 % CPU /
  356 MiB.
- Interpretation: the environment differs (WSL engine vs Docker Desktop, different Python patch and
  drivers); single-digit-millisecond differences over 20 runs are within noise for this setup. These
  numbers are the **pre-migration reference** for later phases, measured in `qwb`; they are not
  evidence of a code regression (the code is unchanged).

## 5. Outstanding failures / unresolved
1. **O5 `aql_catalog`: 2 of 47 queries flagged** — `analytics_time_to_reviewed` used
   `qw_revisions_observed_at` (catalogue expects `qw_revisions_changed_fields`);
   `events_strongest_in_range` used `qw_events_occurred_at` (expects `qw_events_magnitude`). Both used an
   index. The command ran on a **freshly migrated, empty** `quakewatch` database; the catalogue code
   notes optimizer choice depends on data selectivity. R8's `test_indexed_plans_use_their_indexes`
   (seeded data) passed. Classification: **data-dependent plan choice — unverified**; re-run the
   catalogue on seeded data to decide whether it is a real gap or a test-environment artefact.
2. `live` tests (real USGS API) not run — by design (no internet in the test container).

## 6. Cleanup and current state
- Removed after identity check (label `qwb.baseline=phase0`): containers `qwb-py`, `qwb-arango`,
  `qwb-redis`; network `qwb-net`; their 3 anonymous volumes (via `--rm`). Engine now has no
  containers, no volumes, networks `bridge host none` only.
- Kept in `qwb` (by plan): images `python:3.12-slim` (179 MB), `redis:7.4-alpine` (57.8 MB),
  `arangodb:3.12.5` (843 MB) (`/var/lib/containerd` 1.1 GB); the copy `/srv/qwb/quakewatch`;
  `/srv/qwb/tools` (preflight, isolation probes, hashes); `/srv/qwb/logs`.
- Services: `docker.service`, `docker.socket`, `containerd.service` = **inactive, disabled**, no boot
  links, no processes; data on `/dev/sdd` (qwb's ext4).
- VM-level leftovers until the WSL VM shuts down: `docker0` (DOWN, 10.213.0.1/24), `ip_forward=1`,
  Docker firewall chains (FORWARD policy DROP).
- `qwb`: keepalive ended; idles to Stopped on its own. `Ubuntu` (default) and `docker-desktop`:
  Stopped, untouched. Docker Desktop: not running. No Docker API/DB ports on Windows.
- `D:\quakewatch`: fingerprint `93287696…0bc605` (244 files) — **unchanged**; `docs/BENCHMARKS.md`
  `c16daf6c…e2ccd5` — **unchanged**. No application code modified, no migration started, nothing
  pushed.

## 7. Next recommended step
Phase 1a: Redis job locks → ArangoDB `job_leases` (design in the 2026-10-06 report, §8). Owner
decisions still open: **P1** lock-unavailable behaviour (today fail-open), **P2** CLI locking,
**P3** lease renewal, **P4** clock source, **P5** ADR number. Optional first: re-run `aql_catalog` on
seeded data in `qwb` to settle §5.1.
