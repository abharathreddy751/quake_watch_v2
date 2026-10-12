# Selected 15 AQL Queries: Actual Execution

All 15 selected named queries were executed through the application's `run_query()` against the isolated, seeded `quakewatch_test` database with `read_only=True` registry entries only. Each used the registry's representative sample bind variables. No write query or EXPLAIN-only result is counted as execution. The full bind values, durations, and returned rows are preserved in [aql_selected_15_results.json](aql_selected_15_results.json).

| ID | Query | Status | Returned rows |
|---|---|---:|---:|
| Q01 | `analytics_avg_magnitude_by_region` | Executed | 20 |
| Q02 | `analytics_dashboard_summary` | Executed | 1 |
| Q03 | `analytics_network_stats` | Executed | 12 |
| Q04 | `analytics_magnitude_changes` | Executed | 0 |
| Q05 | `analytics_ingestion_latency` | Executed | 1 |
| Q06 | `analytics_significant_by_week` | Executed | 0 |
| Q07 | `alerts_user_rules` | Executed | 0 |
| Q08 | `alerts_matched_events_graph` | Executed | 0 |
| Q09 | `event_graph_relationships` | Executed | 1 |
| Q10 | `events_in_viewport` | Executed | 1 |
| Q11 | `events_within_radius` | Executed | 1 |
| Q12 | `events_location_text` | Executed | 1 |
| Q13 | `ops_run_stats` | Executed | 0 |
| Q14 | `analytics_depth_histogram` | Executed | 17 |
| Q15 | `event_nearby_space_time` | Executed | 0 |

**Results:** 15 executed, 0 errors. The six zero-result queries above did execute successfully; they returned empty row lists and were not skipped. Query selection and names match [submission_artifacts/06_aql_queries/selected_15_queries.md](../../submission_artifacts/06_aql_queries/selected_15_queries.md).
