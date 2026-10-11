# Selected AQL queries (15): verification status

Source: `docs/AQL_QUERIES.md` (generated catalogue). AQL text below is copied verbatim.

**Output status for every query: NOT CAPTURED.** The catalogue's JSON blocks are bind-variable
samples, and its 'Measured' line is a sample-run timing and row count, not returned rows.
Execution against a verified development database is pending.

| # | Query | Catalogue # | Why selected | Features | Execution | Output |
|---|---|---|---|---|---|---|
| Q01 | `analytics_avg_magnitude_by_region` | 5 | Aggregation with COLLECT, AGGREGATE, SORT and LIMIT over events | aggregation | NOT RUN | NOT CAPTURED |
| Q02 | `analytics_dashboard_summary` | 7 | Dashboard summary: aggregation with subqueries | aggregation, subqueries | NOT RUN | NOT CAPTURED |
| Q03 | `analytics_network_stats` | 15 | Network statistics: COLLECT over event-to-network data | aggregation, join | NOT RUN | NOT CAPTURED |
| Q04 | `analytics_magnitude_changes` | 11 | Magnitude changes: nested FOR over revision arrays | array index, join | NOT RUN | NOT CAPTURED |
| Q05 | `analytics_ingestion_latency` | 9 | Ingestion latency: percentiles with subqueries | percentiles, subqueries | NOT RUN | NOT CAPTURED |
| Q06 | `analytics_significant_by_week` | 18 | Significant events by ISO week: date bucketing and aggregation | aggregation | NOT RUN | NOT CAPTURED |
| Q07 | `alerts_user_rules` | 4 | User alert rules: persistent-index lookup plus graph traversal | persistent index, graph traversal | NOT RUN | NOT CAPTURED |
| Q08 | `alerts_matched_events_graph` | 23 | Matched events via 2-hop graph traversal (user -> rule -> event) | graph traversal, 2 hops | NOT RUN | NOT CAPTURED |
| Q09 | `event_graph_relationships` | 24 | Event relationships: OUTBOUND and INBOUND traversal | graph traversal, OUTBOUND, INBOUND | NOT RUN | NOT CAPTURED |
| Q10 | `events_in_viewport` | 48 | Map viewport: geo index (GEO_CONTAINS), COLLECT count and subqueries | geo index, GEO_CONTAINS | NOT RUN | NOT CAPTURED |
| Q11 | `events_within_radius` | 53 | Radius search: geo index (GEO_DISTANCE) with ordering | geo index, GEO_DISTANCE | NOT RUN | NOT CAPTURED |
| Q12 | `events_location_text` | 49 | Location text search: ArangoSearch view with text analyzer | ArangoSearch view, text analyzer | NOT RUN | NOT CAPTURED |
| Q13 | `ops_run_stats` | 40 | Ingestion run statistics: aggregation, percentiles, array operators | aggregation, percentiles, array operators | NOT RUN | NOT CAPTURED |
| Q14 | `analytics_depth_histogram` | 8 | Depth histogram: bucketed aggregation | aggregation | NOT RUN | NOT CAPTURED |
| Q15 | `event_nearby_space_time` | 22 | Nearby events in space and time: geo index plus time window | geo index, GEO_DISTANCE, time window | NOT RUN | NOT CAPTURED |

Excluded and flagged: `analytics_time_to_reviewed` (#20) and `events_strongest_in_range` (#51). The 2026-10-07 aql_catalog run found the optimizer chose a different index for them on an empty database.

Reserve candidates: `analytics_daily_counts_by_band`, `analytics_magnitude_by_month`, `analytics_most_revised`, `analytics_revision_count_distribution`, `ops_backfill_jobs`

# Query details

## Q01: `analytics_avg_magnitude_by_region` (catalogue #5)

- **Purpose (catalogue):** Event count and average/max magnitude by derived region (README Q3).
- **Features:** aggregation
- **Indexes expected by catalogue:** `qw_events_occurred_at` (expected one of: qw_events_occurred_at)
- **Plan from historical sample run:** SingletonNode, IndexNode, MaterializeNode, CollectNode, SortNode, LimitNode, CalculationNode, ReturnNode; estimated cost 2016
- **Historical sample timing:** 5.2 ms, 20 row(s) (sample binds)
- **Execution:** NOT RUN in this task
- **Output:** NOT CAPTURED

**AQL (verbatim):**

```aql
    FOR e IN events
      FILTER e.occurred_at >= @since FILTER e.merged_into == null
      COLLECT region = e.derived.region_name
      AGGREGATE n = LENGTH(1), avg_mag = AVERAGE(e.magnitude), max_mag = MAX(e.magnitude)
      SORT n DESC
      LIMIT @limit
      RETURN {region: region, count: n, avg_magnitude: ROUND(avg_mag * 100) / 100,
              max_magnitude: max_mag}
```

**Bind variables (catalogue sample):**

```json
{
  "since": "2026-08-26T00:00:00.000Z",
  "limit": 20
}
```


## Q02: `analytics_dashboard_summary` (catalogue #7)

- **Purpose (catalogue):** Situational summary: counts in the last 24 h / 7 d, strongest events, significant events.
- **Features:** aggregation, subqueries
- **Indexes expected by catalogue:** `qw_events_occurred_at` (expected one of: qw_events_occurred_at)
- **Plan from historical sample run:** SingletonNode, SubqueryStartNode x7, IndexNode x2, MaterializeNode x2, SubqueryEndNode x7, CalculationNode x12, EnumerateListNode x5, SortNode x3, LimitNode x5, FilterNode, ReturnNode; estimated cost 3744
- **Historical sample timing:** 5.5 ms, 1 row(s) (sample binds)
- **Execution:** NOT RUN in this task
- **Output:** NOT CAPTURED

**AQL (verbatim):**

```aql
    LET day = (FOR e IN events FILTER e.occurred_at >= @day FILTER e.merged_into == null
               RETURN e)
    LET week = (FOR e IN events FILTER e.occurred_at >= @week FILTER e.merged_into == null
                RETURN KEEP(e, "_key", "magnitude", "place", "occurred_at", "alert",
                            "significance", "tsunami", "depth_km", "status"))
    RETURN {
      count_24h: LENGTH(day),
      count_7d: LENGTH(week),
      m45_plus_7d: LENGTH(FOR e IN week FILTER e.magnitude >= 4.5 RETURN 1),
      strongest_24h: FIRST(FOR e IN day FILTER e.magnitude != null SORT e.magnitude DESC LIMIT 1
                           RETURN MERGE(KEEP(e, "magnitude", "place", "occurred_at", "depth_km"),
                                        {key: e._key})),
      strongest_7d: FIRST(FOR e IN week FILTER e.magnitude != null SORT e.magnitude DESC LIMIT 1
                          RETURN MERGE(UNSET(e, "_key"), {key: e._key})),
      significant_7d: (FOR e IN week
                         FILTER e.significance >= 600 OR e.alert != null OR e.tsunami
                         SORT e.significance DESC LIMIT 10
                         RETURN MERGE(UNSET(e, "_key"), {key: e._key})),
      reviewed_share_7d: LENGTH(week) == 0 ? null
        : LENGTH(FOR e IN week FILTER e.status == "reviewed" RETURN 1) / LENGTH(week)
    }
```

**Bind variables (catalogue sample):**

```json
{
  "day": "2026-08-26T00:00:00.000Z",
  "week": "2026-08-26T00:00:00.000Z"
}
```


## Q03: `analytics_network_stats` (catalogue #15)

- **Purpose (catalogue):** Per-network event statistics joined with network names via the graph (README Q11).
- **Features:** aggregation, join
- **Indexes expected by catalogue:** `qw_events_occurred_at` (expected one of: qw_events_occurred_at)
- **Plan from historical sample run:** SingletonNode, IndexNode, MaterializeNode, CalculationNode x3, CollectNode, SortNode x2, ReturnNode; estimated cost 4281
- **Historical sample timing:** 2.5 ms, 12 row(s) (sample binds)
- **Execution:** NOT RUN in this task
- **Output:** NOT CAPTURED

**AQL (verbatim):**

```aql
    FOR e IN events
      FILTER e.occurred_at >= @since FILTER e.merged_into == null
      COLLECT code = e.network
      AGGREGATE n = LENGTH(1), avg_mag = AVERAGE(e.magnitude), max_mag = MAX(e.magnitude),
                reviewed = SUM(e.status == "reviewed" ? 1 : 0)
      LET network = DOCUMENT("networks", code)
      SORT n DESC
      RETURN {network: code, name: network.name, count: n,
              avg_magnitude: ROUND(avg_mag * 100) / 100, max_magnitude: max_mag,
              reviewed_share: ROUND(reviewed / n * 1000) / 1000}
```

**Bind variables (catalogue sample):**

```json
{
  "since": "2026-08-26T00:00:00.000Z"
}
```


## Q04: `analytics_magnitude_changes` (catalogue #11)

- **Purpose (catalogue):** Revisions whose magnitude changed by at least a threshold (README Q14).
- **Features:** array index, join
- **Indexes expected by catalogue:** `qw_revisions_changed_fields` (expected one of: qw_revisions_changed_fields)
- **Plan from historical sample run:** SingletonNode, IndexNode, CalculationNode x5, FilterNode, SortNode, LimitNode, ReturnNode; estimated cost 20
- **Historical sample timing:** 1.7 ms, 0 row(s) (sample binds)
- **Execution:** NOT RUN in this task
- **Output:** NOT CAPTURED

**AQL (verbatim):**

```aql
    FOR r IN event_revisions
      FILTER "magnitude" IN r.changed_fields[*]
      FILTER r.before.magnitude != null AND r.after.magnitude != null
      LET delta = r.after.magnitude - r.before.magnitude
      FILTER ABS(delta) >= @threshold
      SORT ABS(delta) DESC, r.observed_at DESC
      LIMIT @limit
      LET e = DOCUMENT("events", r.event_key)
      RETURN {key: r.event_key, revision_number: r.revision_number, observed_at: r.observed_at,
              before: r.before.magnitude, after: r.after.magnitude,
              delta: ROUND(delta * 100) / 100, place: e.place}
```

**Bind variables (catalogue sample):**

```json
{
  "threshold": 0.3,
  "limit": 20
}
```


## Q05: `analytics_ingestion_latency` (catalogue #9)

- **Purpose (catalogue):** Seconds from origin time to first observation by QuakeWatch, for events that occurred after live monitoring began (README Q15, derived value).
- **Features:** percentiles, subqueries
- **Indexes expected by catalogue:** `qw_events_occurred_at`, `qw_runs_kind_started` (expected one of: qw_runs_kind_started, qw_events_occurred_at)
- **Plan from historical sample run:** SingletonNode, SubqueryStartNode x2, IndexNode x2, LimitNode, SubqueryEndNode x2, CalculationNode x2, ReturnNode; estimated cost 29
- **Historical sample timing:** 2.2 ms, 1 row(s) (sample binds)
- **Execution:** NOT RUN in this task
- **Output:** NOT CAPTURED

**AQL (verbatim):**

```aql
    LET monitoring_start = FIRST(
      FOR r IN ingestion_runs OPTIONS {indexHint: "qw_runs_kind_started"}
        FILTER r.kind == "feed_sync" AND r.status IN ["succeeded", "partial"]
        SORT r.kind ASC, r.started_at ASC
        LIMIT 1
        RETURN r.started_at
    )
    LET since = monitoring_start == null ? @since : MAX([@since, monitoring_start])
    LET latencies = (
      FOR e IN events
        FILTER e.occurred_at >= since FILTER e.merged_into == null
        FILTER e.derived.first_seen_via == "feed" AND e.derived.first_seen_latency_s != null
        RETURN e.derived.first_seen_latency_s
    )
    RETURN {
      monitoring_start: monitoring_start,
      count: LENGTH(latencies),
      p50_s: LENGTH(latencies) == 0 ? null : PERCENTILE(latencies, 50),
      p90_s: LENGTH(latencies) == 0 ? null : PERCENTILE(latencies, 90),
      p99_s: LENGTH(latencies) == 0 ? null : PERCENTILE(latencies, 99),
      min_s: MIN(latencies), max_s: MAX(latencies)
    }
```

**Bind variables (catalogue sample):**

```json
{
  "since": "2026-08-26T00:00:00.000Z"
}
```


## Q06: `analytics_significant_by_week` (catalogue #18)

- **Purpose (catalogue):** Significant events (significance ≥ 600, PAGER alert or tsunami flag) per ISO week (README Q12).
- **Features:** aggregation
- **Indexes expected by catalogue:** `qw_events_occurred_at` (expected one of: qw_events_occurred_at)
- **Plan from historical sample run:** SingletonNode, IndexNode, MaterializeNode, CalculationNode x4, FilterNode, CollectNode, SortNode, ReturnNode; estimated cost 7038
- **Historical sample timing:** 3.2 ms, 1 row(s) (sample binds)
- **Execution:** NOT RUN in this task
- **Output:** NOT CAPTURED

**AQL (verbatim):**

```aql
    FOR e IN events
      FILTER e.occurred_at >= @since FILTER e.merged_into == null
      FILTER e.significance >= 600 OR e.alert != null OR e.tsunami
      LET iso = DATE_ISOWEEKYEAR(e.occurred_at)
      COLLECT week = CONCAT(iso.year, "-W", RIGHT(CONCAT("0", iso.week), 2)) INTO members = e
      SORT week
      RETURN {week: week, count: LENGTH(members),
              strongest: MAX(members[*].magnitude)}
```

**Bind variables (catalogue sample):**

```json
{
  "since": "2026-08-26T00:00:00.000Z"
}
```


## Q07: `alerts_user_rules` (catalogue #4)

- **Purpose (catalogue):** A user's alert rules with match counts (CRUD list).
- **Features:** persistent index, graph traversal
- **Indexes expected by catalogue:** `edge`, `qw_rules_user` (expected one of: qw_rules_user)
- **Plan from historical sample run:** SingletonNode, CalculationNode x4, IndexNode, SortNode, SubqueryStartNode, TraversalNode, SubqueryEndNode, ReturnNode; estimated cost 2
- **Historical sample timing:** 5.6 ms, 0 row(s) (sample binds)
- **Execution:** NOT RUN in this task
- **Output:** NOT CAPTURED

**AQL (verbatim):**

```aql
        FOR r IN alert_rules
          FILTER r.user_id == @user_id
          SORT r.created_at DESC
          LET matches = LENGTH(FOR v IN 1..1 OUTBOUND r rule_matched_event RETURN 1)
          RETURN MERGE(UNSET(r, "_id", "_rev", "_key"), {id: r._key, match_count: matches})
```

**Bind variables (catalogue sample):**

```json
{
  "user_id": 1
}
```


## Q08: `alerts_matched_events_graph` (catalogue #23)

- **Purpose (catalogue):** Events matched by any of a user's watch rules via 2-hop traversal users → rules → events (README Q13).
- **Features:** graph traversal, 2 hops
- **Indexes expected by catalogue:** `edge` (expected one of: edge)
- **Plan from historical sample run:** SingletonNode, TraversalNode x2, CalculationNode x2, SortNode, LimitNode, ReturnNode; estimated cost 8
- **Historical sample timing:** 2.9 ms, 0 row(s) (sample binds)
- **Execution:** NOT RUN in this task
- **Output:** NOT CAPTURED

**AQL (verbatim):**

```aql
        FOR rule IN 1..1 OUTBOUND CONCAT("users/", @user_id) user_owns_rule
          FOR ev, edge IN 1..1 OUTBOUND rule rule_matched_event
            FILTER ev.merged_into == null
            SORT edge.matched_at DESC
            LIMIT @limit
            RETURN {rule: rule.name, rule_id: rule._key, event_key: ev._key,
                    magnitude: ev.magnitude, place: ev.place, occurred_at: ev.occurred_at,
                    matched_at: edge.matched_at}
```

**Bind variables (catalogue sample):**

```json
{
  "user_id": 1,
  "limit": 20
}
```


## Q09: `event_graph_relationships` (catalogue #24)

- **Purpose (catalogue):** Region and network of an event and other recent events in the same region (graph traversal event → region ← events; README Q10).
- **Features:** graph traversal, OUTBOUND, INBOUND
- **Indexes expected by catalogue:** `edge` (expected one of: edge)
- **Plan from historical sample run:** SingletonNode, CalculationNode x11, SubqueryStartNode x4, TraversalNode x4, LimitNode x3, SubqueryEndNode x4, FilterNode x3, SortNode, ReturnNode; estimated cost 93
- **Historical sample timing:** 2.8 ms, 1 row(s) (sample binds)
- **Execution:** NOT RUN in this task
- **Output:** NOT CAPTURED

**AQL (verbatim):**

```aql
        LET start = DOCUMENT("events", @key)
        LET region = FIRST(FOR v IN 1..1 OUTBOUND start event_in_region RETURN v)
        LET network = FIRST(FOR v IN 1..1 OUTBOUND start event_reported_by_network RETURN v)
        LET same_region = region == null ? [] : (
          FOR other IN 1..1 INBOUND region event_in_region
            FILTER other._key != @key AND other.merged_into == null
            SORT other.occurred_at DESC
            LIMIT @limit
            RETURN MERGE(KEEP(other, "magnitude", "place", "occurred_at", "depth_km"),
                         {key: other._key})
        )
        LET region_total = region == null ? 0 : LENGTH(
          FOR other IN 1..1 INBOUND region event_in_region
            FILTER other.merged_into == null RETURN 1)
        RETURN {region: region == null ? null : UNSET(region, "_id", "_rev"),
                network: network == null ? null : UNSET(network, "_id", "_rev"),
                same_region: same_region, region_event_count: region_total}
```

**Bind variables (catalogue sample):**

```json
{
  "key": "usgs_x",
  "limit": 10
}
```


## Q10: `events_in_viewport` (catalogue #48)

- **Purpose (catalogue):** Events inside a map viewport bounding box.
- **Features:** geo index, GEO_CONTAINS
- **Indexes expected by catalogue:** `qw_events_geo` (expected one of: qw_events_geo)
- **Plan from historical sample run:** SingletonNode, SubqueryStartNode x2, IndexNode x2, CollectNode, LimitNode x2, SubqueryEndNode x2, CalculationNode x4, SortNode, ReturnNode; estimated cost 23
- **Historical sample timing:** 4.4 ms, 1 row(s) (sample binds)
- **Execution:** NOT RUN in this task
- **Output:** NOT CAPTURED

**AQL (verbatim):**

```aql
LET total = FIRST(
FOR e IN events
  FILTER GEO_CONTAINS(@bbox0, e.coordinates)
  FILTER e.merged_into == null
  COLLECT WITH COUNT INTO n
  RETURN n
)
LET rows = (
FOR e IN events
  FILTER GEO_CONTAINS(@bbox0, e.coordinates)
  FILTER e.merged_into == null
  SORT e.occurred_at DESC, e._key DESC
  LIMIT @offset, @limit
  RETURN MERGE(KEEP(e, @fields), {key: e._key, region_name: e.derived.region_name})
)
RETURN {total: total, rows: rows}
```

**Bind variables (catalogue sample):**

```json
{
  "bbox0": {
    "type": "Polygon",
    "coordinates": [
      [
        [
          -170.0,
          50.0
        ],
        [
          -130.0,
          50.0
        ],
        [
          -130.0,
          72.0
        ],
        [
          -170.0,
          72.0
        ],
        [
          -170.0,
          50.0
        ]
      ]
    ]
  },
  "fields": [
    "source_event_id",
    "magnitude",
    "magnitude_type",
    "place",
    "occurred_at",
    "depth_km",
    "latitude",
    "longitude",
    "alert",
    "status",
    "tsunami",
    "network",
    "significance",
    "event_type",
    "felt",
    "revision_count",
    "source_updated_at"
  ],
  "offset": 0,
  "limit": 25
}
```


## Q11: `events_within_radius` (catalogue #53)

- **Purpose (catalogue):** Events within a geographic radius of a point (README Q2).
- **Features:** geo index, GEO_DISTANCE
- **Indexes expected by catalogue:** `qw_events_geo` (expected one of: qw_events_geo)
- **Plan from historical sample run:** SingletonNode, SubqueryStartNode x2, IndexNode x2, CollectNode, LimitNode x2, SubqueryEndNode x2, CalculationNode x4, SortNode, ReturnNode; estimated cost 23
- **Historical sample timing:** 1.8 ms, 1 row(s) (sample binds)
- **Execution:** NOT RUN in this task
- **Output:** NOT CAPTURED

**AQL (verbatim):**

```aql
LET total = FIRST(
FOR e IN events
  FILTER GEO_DISTANCE(e.coordinates, [@lon, @lat]) <= @radius_m
  FILTER e.magnitude >= @min_mag
  FILTER e.merged_into == null
  COLLECT WITH COUNT INTO n
  RETURN n
)
LET rows = (
FOR e IN events
  FILTER GEO_DISTANCE(e.coordinates, [@lon, @lat]) <= @radius_m
  FILTER e.magnitude >= @min_mag
  FILTER e.merged_into == null
  SORT e.occurred_at DESC, e._key DESC
  LIMIT @offset, @limit
  RETURN MERGE(KEEP(e, @fields), {key: e._key, region_name: e.derived.region_name})
)
RETURN {total: total, rows: rows}
```

**Bind variables (catalogue sample):**

```json
{
  "lon": -149.9,
  "lat": 61.2,
  "radius_m": 300000.0,
  "min_mag": 2.5,
  "fields": [
    "source_event_id",
    "magnitude",
    "magnitude_type",
    "place",
    "occurred_at",
    "depth_km",
    "latitude",
    "longitude",
    "alert",
    "status",
    "tsunami",
    "network",
    "significance",
    "event_type",
    "felt",
    "revision_count",
    "source_updated_at"
  ],
  "offset": 0,
  "limit": 25
}
```


## Q12: `events_location_text` (catalogue #49)

- **Purpose (catalogue):** Full-text location search over place and derived region (ArangoSearch view).
- **Features:** ArangoSearch view, text analyzer
- **Indexes expected by catalogue:** none
- **Plan from historical sample run:** SingletonNode, SubqueryStartNode x2, EnumerateViewNode x2, CalculationNode x6, FilterNode x2, CollectNode, LimitNode x2, SubqueryEndNode x2, SortNode, ReturnNode; estimated cost 3963
- **Historical sample timing:** 7.3 ms, 1 row(s) (sample binds)
- **Execution:** NOT RUN in this task
- **Output:** NOT CAPTURED

**AQL (verbatim):**

```aql
LET total = FIRST(
FOR e IN events_search SEARCH ANALYZER(TOKENS(@q, 'text_en') ALL == e.place, 'text_en') OR ANALYZER(TOKENS(@q, 'text_en') ALL == e.derived.region_name, 'text_en')
  FILTER e.merged_into == null
  COLLECT WITH COUNT INTO n
  RETURN n
)
LET rows = (
FOR e IN events_search SEARCH ANALYZER(TOKENS(@q, 'text_en') ALL == e.place, 'text_en') OR ANALYZER(TOKENS(@q, 'text_en') ALL == e.derived.region_name, 'text_en')
  FILTER e.merged_into == null
  SORT e.occurred_at DESC, e._key DESC
  LIMIT @offset, @limit
  RETURN MERGE(KEEP(e, @fields), {key: e._key, region_name: e.derived.region_name})
)
RETURN {total: total, rows: rows}
```

**Bind variables (catalogue sample):**

```json
{
  "q": "fiji islands",
  "fields": [
    "source_event_id",
    "magnitude",
    "magnitude_type",
    "place",
    "occurred_at",
    "depth_km",
    "latitude",
    "longitude",
    "alert",
    "status",
    "tsunami",
    "network",
    "significance",
    "event_type",
    "felt",
    "revision_count",
    "source_updated_at"
  ],
  "offset": 0,
  "limit": 25
}
```


## Q13: `ops_run_stats` (catalogue #40)

- **Purpose (catalogue):** Run outcomes and durations per kind since a timestamp (success rate, p95).
- **Features:** aggregation, percentiles, array operators
- **Indexes expected by catalogue:** `qw_runs_started_at` (expected one of: qw_runs_started_at, qw_runs_kind_started)
- **Plan from historical sample run:** SingletonNode, IndexNode, CalculationNode x5, CollectNode, SortNode, SubqueryStartNode, EnumerateListNode, SubqueryEndNode, ReturnNode; estimated cost 1
- **Historical sample timing:** 1.7 ms, 0 row(s) (sample binds)
- **Execution:** NOT RUN in this task
- **Output:** NOT CAPTURED

**AQL (verbatim):**

```aql
        FOR r IN ingestion_runs
          FILTER r.started_at >= @since
          COLLECT kind = r.kind INTO runs = r
          LET durations = runs[* FILTER CURRENT.duration_ms != null RETURN CURRENT.duration_ms]
          RETURN {
            kind: kind,
            total: LENGTH(runs),
            by_status: MERGE(FOR st IN UNIQUE(runs[*].status)
                               RETURN {[st]: LENGTH(runs[* FILTER CURRENT.status == st])}),
            p50_ms: LENGTH(durations) == 0 ? null : PERCENTILE(durations, 50),
            p95_ms: LENGTH(durations) == 0 ? null : PERCENTILE(durations, 95)
          }
```

**Bind variables (catalogue sample):**

```json
{
  "since": "2026-09-01T00:00:00.000Z"
}
```


## Q14: `analytics_depth_histogram` (catalogue #8)

- **Purpose (catalogue):** Depth distribution (shallow < 70 km, intermediate 70 to 300 km, deep > 300 km, 10 km bins).
- **Features:** aggregation
- **Indexes expected by catalogue:** `qw_events_occurred_at` (expected one of: qw_events_occurred_at)
- **Plan from historical sample run:** SingletonNode, IndexNode, CalculationNode x2, CollectNode, SortNode, ReturnNode; estimated cost 2348
- **Historical sample timing:** 1.8 ms, 19 row(s) (sample binds)
- **Execution:** NOT RUN in this task
- **Output:** NOT CAPTURED

**AQL (verbatim):**

```aql
    FOR e IN events
      FILTER e.occurred_at >= @since FILTER e.merged_into == null FILTER e.depth_km != null
      COLLECT bin = FLOOR(e.depth_km / 10) * 10 WITH COUNT INTO n
      SORT bin
      RETURN {bin: bin, count: n}
```

**Bind variables (catalogue sample):**

```json
{
  "since": "2026-08-26T00:00:00.000Z"
}
```


## Q15: `event_nearby_space_time` (catalogue #22)

- **Purpose (catalogue):** Other events within a radius and a time window of an event (proximity only; not an aftershock classification — ESD §20C).
- **Features:** geo index, GEO_DISTANCE, time window
- **Indexes expected by catalogue:** `qw_events_geo` (expected one of: qw_events_geo)
- **Plan from historical sample run:** SingletonNode, IndexNode, CalculationNode x2, SortNode, LimitNode, ReturnNode; estimated cost 13
- **Historical sample timing:** 3.7 ms, 0 row(s) (sample binds)
- **Execution:** NOT RUN in this task
- **Output:** NOT CAPTURED

**AQL (verbatim):**

```aql
        FOR e IN events
          FILTER GEO_DISTANCE(e.coordinates, @point) <= @radius_m
          FILTER e.occurred_at >= @start AND e.occurred_at <= @end
          FILTER e._key != @key AND e.merged_into == null
          LET distance_km = GEO_DISTANCE(e.coordinates, @point) / 1000
          SORT distance_km ASC
          LIMIT @limit
          RETURN {key: e._key, magnitude: e.magnitude, place: e.place,
                  occurred_at: e.occurred_at, distance_km: ROUND(distance_km * 10) / 10}
```

**Bind variables (catalogue sample):**

```json
{
  "point": [
    -150.0,
    61.0
  ],
  "radius_m": 100000,
  "start": "2026-09-01T00:00:00.000Z",
  "end": "2026-09-15T00:00:00.000Z",
  "key": "usgs_x",
  "limit": 10
}
```

