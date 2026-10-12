# QuakeWatch Review 2: Execution Report

**Run date:** 2026-10-11  
**Application:** QuakeWatch, Django + ArangoDB  
**Scope:** Isolated test database only; live `quakewatch` preserved.

## Outcome

The test-settings Django system check passed. The default pytest suite could not start because pytest is not installed in the existing web image; no tests were collected. Independent validations were completed against `quakewatch_test`: 15 read-only AQL queries, transaction commit/rollback/concurrent retry, saved-search API CRUD, and a native ArangoDB dump. The disposable test database was dropped after evidence capture. The final DB list is `_system,quakewatch`.

## Environment and safety

The fresh process fallback reported Windows PowerShell 5.1, working directory `D:\bharath projects\quakewatch`, harmless probe output `fresh-shell-probe`, exit code 0. The container probe immediately before system check and again immediately before pytest reported:

- `QW_ENV=test`
- effective database `quakewatch_test` (configured base name `quakewatch`)
- endpoint `http://arangodb:8529`
- database list `_system,quakewatch`
- `quakewatch_test` absent before setup

Pytest never started, so its fixtures did not create a database. The test database was then created by the existing schema command after an in-command exact-target guard. It was seeded only from the repository's recorded USGS fixture. Final cleanup used the project's test-suffix-guarded drop helper after all validations and dump copying. The protected `quakewatch` database remained present throughout; no Docker volumes or containers were reset or removed.

## Phase 1

- Django system check: **passed**, exit 0; `System check identified no issues (0 silenced).`
- Standard pytest: **blocked before collection**, exit 1; `/usr/local/bin/python: No module named pytest`. No tests ran, so pass/fail/skip/error counts are unavailable. Dependencies were not installed.
- Default selection would exclude live, E2E, and performance tests according to `pyproject.toml`; none were run.

Raw outputs: [phase1_django_check.log](phase1_django_check.log), [phase1_pytest.log](phase1_pytest.log).

## Isolated database and schema

The project `arango_migrate` command applied schema version 6 to `quakewatch_test` only: 31 declared collections, 32 declared named indexes, the `events_search` view, the graph, and a v2 identity-claims migration affecting 0 documents. The observed inventory contained 67 index definitions including built-ins.

The recorded fixture `tests/fixtures/usgs/all_day.geojson` yielded 221 normalized records and 0 rejected records. Ingestion inserted 221 events and 221 revisions with 0 per-record failures. Before test DB cleanup, the inventory contained 1,396 documents across declared collections, including 221 events, 221 revisions, 232 identity claims, and 221 each in `event_in_region` and `event_reported_by_network`. These are test-fixture figures, not live `quakewatch` counts.

Detailed evidence: [database_schema_inventory.json](database_schema_inventory.json), [database_final_inventory.json](database_final_inventory.json), [database_setup_seed_cleanup.log](database_setup_seed_cleanup.log).

## Query execution

**15/15 selected read-only queries executed; 0 query errors.** Six returned zero rows, which is recorded as a successful empty result rather than a skipped execution. All returned rows, sample binds, and timing values are in [aql_selected_15_results.json](aql_selected_15_results.json); the status table is [selected_15_query_execution.md](selected_15_query_execution.md).

## Transaction validation

The existing `run_in_transaction()` implementation was exercised on `quakewatch_test`:

- Commit across events and audit log: passed; both documents visible after commit.
- Invalid event causing rollback: passed; `DocumentInsertError`, with no partial audit/event writes.
- Two concurrent increments: passed; final counter 2, conflict retry observed, no worker errors.

A first harness run exited 1 during cleanup because it tried to delete the intentionally absent rollback document (HTTP 404). The behavior checks had completed; the corrected harness cleaned only inserted keys and exited 0. Both attempts are preserved in the transaction logs; successful result is [transaction_validation_retry_01.json](transaction_validation_retry_01.json).

## API CRUD validation

A real Django test client with allowed `Host: localhost` exercised saved-search create/read/list/rename/delete and post-delete list:

- POST 201
- GET detail 200; GET list 200 (one result)
- PATCH 200 with renamed value
- DELETE 204; subsequent GET list 200 with no result
- Temporary account, session, and search were verified absent after cleanup

The first attempt used default `Host: testserver` and was rejected by `ALLOWED_HOSTS`; it did not reach the endpoint. The successful retry and original failure are both retained in the API logs.

## Native export

`arangodump` 3.12.5 ran against `quakewatch_test` only, processed 31 collections, retrieved 955.4 KB, and produced a 32.8 KB compressed dump. The copied dump contains 65 non-empty files totaling 159,002 bytes; its manifest parses and all 31 gzip payloads decompress. Artifact path: [native_arangodump_2026-10-11](native_arangodump_2026-10-11). No restore validation was run.

## Failed, blocked, and unexecuted

- **Blocked:** standard pytest suite, missing pytest package in the container. No test counts are claimed.
- **Not run:** live, E2E, and performance suites; the default selection excludes them and pytest itself is unavailable.
- **Not run:** ArangoDB restore validation.
- **Not queried:** live `quakewatch` record counts; only the isolated test database was inventoried.
- **Not achieved:** a 500-event count in this run; the isolated fixture contained 221 events. No live count is substituted.
- **Not run:** alert-rule CRUD, research snapshot API export, and browser accessibility flows.

## Credential handling

A previous `.env` attachment exposed database credential material in the conversation. No credential value is repeated in this package. Rotate the affected credential through the owner's normal secret-management procedure; no credential change or service restart was performed here.

## Final deliverables

New dated deliverables are in `submission_artifacts/review2_2026-10-11/`: the DOCX/PDF report, selected-query PDF, and test-case workbook. The pre-existing undated deliverables and historical evidence were left unchanged. The run's artifact integrity summary is [artifact_integrity_verification.json](artifact_integrity_verification.json).
