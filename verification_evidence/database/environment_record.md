# Environment record (verification, 2026-10-10)

Recorded without starting, stopping, or connecting to any service.

| Item | Finding | Evidence |
|---|---|---|
| Working copy | `D:\quakewatch`, 286 files (excluding caches), includes the frontend redesign | file count, `static/qw/css/qw.css`, `templates/partials/mark.html` |
| Git | Working copy is not a Git repository. Committed checkout: `D:\qw-baseline\repo\quake-watch`, branch `arangodb-only-migration` at `7e6b788` | `git` in the checkout |
| Project virtualenv | `.venv` is **absent** from `D:\quakewatch` | directory listing |
| Python for tests | Project targets Python 3.12. Installed: 3.9 (has matplotlib, no openpyxl/reportlab), 3.11 (no matplotlib). No 3.12 found | `py -0p` |
| ArangoDB on localhost | No listener on `127.0.0.1:8529` (HTTP 000) | probe, previous audit |
| Docker | Windows Docker CLI cannot reach an engine (`dockerDesktopLinuxEngine` pipe absent). Docker Desktop must not be started (see memory note) | `docker ps` failure |
| WSL `qwb` | Registered, state **Stopped**. Phase 0 baseline run used it on 2026-10-07. Whether its ArangoDB data is present and which database it holds is **not verified** | `wsl -l -v`; baseline report |
| Document tooling | MiKTeX `xelatex` at `D:\AB\latex\miktex`; Pandoc 3.10.2; Times New Roman installed. Required LaTeX packages are present (fontspec, setspace, geometry, longtable, booktabs, hyperref, caption, graphicx, xcolor). MiKTeX is set to auto-install; builds are restricted to the present packages | `kpsewhich`, `initexmf` |

## Database target status

- **Target identified:** none that is running and verifiable.
- **Target candidates:** the development database named `quakewatch` (per `docs/RUNBOOK.md`) and the disposable `qwcat_s5` used for the AQL catalogue sample run (245 events). Neither is reachable now.
- **Writes performed:** none.
- **Count, query, transaction, export, and current-test operations:** **BLOCKED BY ENVIRONMENT**. Each needs an ArangoDB service that you start yourself in an identified isolated environment.

## Historical evidence (not current)

| Evidence | Date | Tree | Status |
|---|---|---|---|
| `qwb` baseline: 601 passed, 0 failed, 61 deselected, coverage 93.96% | 2026-10-07 | 244-file tree | Historical; the working copy has changed since |
| `qwb` browser/accessibility suite: 58 passed | 2026-10-07 | 244-file tree | Historical |
| `qwb` AQL catalogue run: 2 of 47 queries flagged (different index chosen on an empty DB) | 2026-10-07 | 244-file tree | Unresolved |
| Benchmarks 500 / 10k / 100k (synthetic data) | 2026-10-07 | 244-file tree | Synthetic; not application data |

Copies of these files are in `verification_evidence\tests\`, `verification_evidence\performance\`, and `verification_evidence\queries\`, prefixed `baseline_2026-10-07_`. The originals in `D:\qw-baseline\reports\` are unchanged.

## To unblock database work (user action)

1. Start the development ArangoDB yourself in an isolated environment (for example, the `qwb` Docker compose project, after confirming its volume and database name).
2. Tell me the database name and the host address to use. I will then run read-only counts and queries against that database only.
3. Approve an isolated integration test run. The test suite creates and drops a `<db>_test` database, so the target must be confirmed first.
