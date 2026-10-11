/* Dashboard (ESD §10): summary, 24 h map preview, recent events, daily activity, significant events. */
(function () {
  "use strict";
  const { h, load, fmt, magBadge, time, eventLink, api, state, band } = window.QW;

  /** A metric panel: mono label, large tabular value, optional note. `tone` only tints the gauge tick. */
  function stat(label, value, { note, tone } = {}) {
    return h("div", { class: "col-6 col-md-3 col-xl-2" },
      h("div", { class: "qw-metric", "data-tone": tone || null },
        h("div", { class: "qw-metric__label" }, label),
        h("div", { class: "qw-metric__value" }, value),
        note ? h("div", { class: "qw-metric__note" }, note) : null));
  }

  function strongestCard(label, e) {
    const b = e ? band(e.magnitude) : null;
    // the epicentre pulses only for a strong event (M4.5+), the same rule as the map's halos
    const glyph = e ? h("span", { class: `qw-epicentre${e.magnitude >= 4.5 ? "" : " qw-epicentre--static"}${b !== null && b >= 3 ? " qw-epicentre--severe" : ""}`, "aria-hidden": "true" }) : null;
    return h("div", { class: "col-12 col-xl-4" },
      h("div", { class: "qw-metric qw-metric--feature", "data-tone": "accent" },
        h("div", { class: "d-flex justify-content-between align-items-center" }, h("div", { class: "qw-metric__label" }, label), glyph),
        e ? h("div", { class: "qw-feature-row" }, magBadge(e.magnitude),
          h("div", {}, eventLink(e.key, e.place || e.key),
            h("div", { class: "qw-event__meta" }, time(e.occurred_at), " · depth ", fmt.depth(e.depth_km))))
          : h("p", { class: "mb-0 text-body-secondary" }, "No events in this window.")));
  }

  function renderSummary(s, el) {
    el.append(
      stat("Events · 24 h", fmt.num(s.count_24h), { tone: "info" }),
      stat("Events · 7 days", fmt.num(s.count_7d)),
      stat("M4.5+ · 7 days", fmt.num(s.m45_plus_7d), { tone: "accent" }),
      stat("Reviewed · 7 days", fmt.pct(s.reviewed_share_7d), { note: "USGS review status", tone: "ok" }),
      strongestCard("Strongest in the last 24 h", s.strongest_24h),
    );
    renderSignificant(s.significant_7d);
  }

  /** Console-style event list: severity tick, magnitude badge, place, mono metadata line. */
  function eventList(rows) {
    return h("ul", { class: "qw-event-list" }, rows.map((e) => {
      const b = band(e.magnitude);
      return h("li", { class: "qw-event", "data-band": b === null ? null : String(b) },
        magBadge(e.magnitude, e.magnitude_type),
        h("div", { class: "qw-event__body" },
          eventLink(e.key, e.place || e.key),
          h("div", { class: "qw-event__meta" }, time(e.occurred_at), " · depth ", fmt.depth(e.depth_km),
            e.status ? ` · ${e.status}` : "", e.tsunami ? " · tsunami flag" : "")));
    }));
  }

  function renderSignificant(rows) {
    const el = document.getElementById("significant");
    if (!rows || !rows.length) return state(el, "empty", { message: "No significant events in the last 7 days." });
    window.QW.fill(el, eventList(rows));
  }

  function isoDaysAgo(days) {
    return new Date(Date.now() - days * 86400000).toISOString().replace(/\.\d+Z$/, ".000Z");
  }

  async function renderMap() {
    const el = document.getElementById("preview-map");
    const status = document.getElementById("preview-map-state");
    const map = QWMap.create(el, { zoom: 1, scrollWheelZoom: false });
    const layer = QWMap.eventLayer(map);
    status.replaceChildren(window.QW.loader("Loading events…", { size: "sm" }));
    QWMap.busy(map, true);
    const result = await api("/events/map", { params: { bbox: "-85,-180,85,180", start: isoDaysAgo(1) } });
    QWMap.busy(map, false);
    if (!result.ok) {
      status.replaceChildren(h("span", { class: "text-danger" }, h("i", { class: "bi bi-exclamation-triangle", "aria-hidden": "true" }), " Could not load map data: ", result.error.message));
      return;
    }
    layer.render(result.data);
    status.textContent = result.data.count
      ? `${fmt.num(result.data.count)} events in the last 24 hours${result.data.mode === "clusters" ? " (grouped)" : ""}.`
      : "No events in the last 24 hours.";
  }

  // fixed band → ramp step (colour follows the band, not its position in the filtered list)
  const BAND_STEP = { "<2.5": 0, "2.5-4.5": 1, "4.5-6": 2, "6+": 3 };

  function renderActivity(data, el) {
    const since = isoDaysAgo(14).slice(0, 10);
    const rows = data.daily_by_band.filter((r) => r.day > since);
    if (!rows.length) return false;
    const days = [...new Set(rows.map((r) => r.day))].sort();
    const bands = ["<2.5", "2.5-4.5", "4.5-6", "6+", "unknown"].filter((b) => rows.some((r) => r.band === b));
    const count = (day, b) => (rows.find((r) => r.day === day && r.band === b) || { count: 0 }).count;
    const totals = days.map((d) => bands.reduce((sum, b) => sum + count(d, b), 0));
    const peak = days[totals.indexOf(Math.max(...totals))];
    QWCharts.figure(el, {
      summary: `Stacked daily event counts by magnitude band over ${days.length} days; busiest day ${peak} with ${fmt.num(Math.max(...totals))} events.`,
      config: {
        type: "bar",
        data: { labels: days, datasets: bands.map((b) => ({ label: `M ${b}`, data: days.map((d) => count(d, b)), qwToken: b === "unknown" ? "--qw-series-muted" : `--qw-mag-${BAND_STEP[b]}`, qwGap: true, backgroundColor: QWCharts.cssVar(b === "unknown" ? "--qw-series-muted" : `--qw-mag-${BAND_STEP[b]}`), borderColor: QWCharts.surface(), borderWidth: { top: 2 }, maxBarThickness: 28 })) },
        options: { scales: { x: { stacked: true, grid: { display: false } }, y: { stacked: true, beginAtZero: true, border: { display: false }, title: { display: true, text: "Events" } } } },
      },
      columns: ["Day", ...bands.map((b) => `M ${b}`), "Total"],
      rows: days.map((d, i) => [d, ...bands.map((b) => fmt.num(count(d, b))), fmt.num(totals[i])]),
    });
    return true;
  }

  document.addEventListener("DOMContentLoaded", () => {
    const significant = document.getElementById("significant");
    state(significant, "loading", { message: "Loading significant events…" });
    load(document.getElementById("summary"), "/analytics/summary", renderSummary, { rows: 2, loading: "Loading activity summary…" }).then((result) => {
      if (result && !result.ok) window.QW.errorState(significant, result);
    });
    load(document.getElementById("recent"), "/events", (data, el) => {
      if (!data.results.length) return false;
      el.append(eventList(data.results));
      return true;
    }, { params: { page_size: 8 }, loading: "Loading earthquake data…", empty: "No events have been ingested yet. The first sync runs within a few minutes of start-up." });
    load(document.getElementById("activity"), "/analytics/timeseries", renderActivity, { params: { days: 14 }, loading: "Loading activity…", empty: "No activity recorded in the last 14 days." });
    renderMap();
  });
})();
