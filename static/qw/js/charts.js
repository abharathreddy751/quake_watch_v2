/* Chart.js wrappers. Each chart is a <figure> with: a canvas (role="img" + summary label), a
 * visible caption, and a collapsible data table — the accessible equivalent of the chart. */
(function () {
  "use strict";
  const { h, fmt } = window.QW;
  const charts = new Set();

  function cssVar(name) {
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  }

  /** Chart.js defaults from the design tokens (re-applied on every theme change). */
  function themeDefaults() {
    Chart.defaults.color = cssVar("--qw-chart-text");
    Chart.defaults.borderColor = cssVar("--qw-chart-grid");
    Chart.defaults.font.family = cssVar("--qw-font-sans") || "system-ui";
    Chart.defaults.font.size = 12;
    Chart.defaults.animation.duration = 600;
    Chart.defaults.animation.easing = "easeOutQuart";
    const tip = Chart.defaults.plugins.tooltip;
    tip.backgroundColor = cssVar("--qw-surface-alt");
    tip.borderColor = cssVar("--qw-border-strong");
    tip.borderWidth = 1;
    tip.titleColor = cssVar("--qw-text");
    tip.bodyColor = cssVar("--qw-text-2");
    tip.titleFont = { family: cssVar("--qw-font-mono"), weight: "600", size: 12 };
    tip.bodyFont = { family: cssVar("--qw-font-sans"), size: 12 };
    tip.padding = 10;
    tip.cornerRadius = 6;
    tip.boxPadding = 4;
    tip.caretSize = 5;
    const legend = Chart.defaults.plugins.legend.labels;
    legend.usePointStyle = true;
    legend.pointStyle = "rectRounded";
    legend.boxWidth = 10;
    legend.boxHeight = 10;
  }

  const PALETTE = ["--qw-mag-0", "--qw-mag-1", "--qw-mag-2", "--qw-mag-3", "--qw-mag-4"];
  function palette(i) {
    return cssVar(PALETTE[i % PALETTE.length]);
  }

  function table(columns, rows) {
    return window.QW.scrollRegion("Chart data table",
      h("table", { class: "table table-sm qw-table" },
        h("thead", {}, h("tr", {}, columns.map((c, i) => h("th", { scope: "col", class: i ? "num" : null }, c)))),
        h("tbody", {}, rows.map((r) => h("tr", {}, r.map((v, i) => (i ? h("td", { class: "num" }, v) : h("th", { scope: "row" }, v))))))));
  }

  /**
   * figure(container, {summary, config, columns, rows})
   *   summary: one-sentence description used as the canvas label and caption.
   *   columns/rows: the data table (first column = row header).
   */
  function figure(container, { summary, config, columns, rows }) {
    for (const old of charts) {
      if (!old.canvas.isConnected) { old.destroy(); charts.delete(old); }
    }
    themeDefaults();
    const canvas = h("canvas", { role: "img", "aria-label": summary });
    const fig = h("figure", { class: "mb-0" },
      h("div", { class: "qw-chart" }, canvas),
      h("figcaption", { class: "small text-body-secondary mt-2" }, summary),
      h("details", { class: "small mt-1" }, h("summary", {}, "Show data table"), table(columns, rows)));
    container.append(fig);
    config.options = Object.assign({ responsive: true, maintainAspectRatio: false, animation: matchMedia("(prefers-reduced-motion: reduce)").matches ? false : undefined }, config.options || {});
    const chart = new Chart(canvas, config);
    charts.add(chart);
    return chart;
  }

  document.addEventListener("qw:theme", () => {
    themeDefaults();
    for (const chart of charts) {
      // datasets carry the CSS token they were coloured from, so dark mode gets its own steps
      for (const ds of chart.data.datasets) {
        if (ds.qwToken) ds.backgroundColor = cssVar(ds.qwToken);
        if (ds.borderColor && ds.qwGap) ds.borderColor = surface();
      }
      chart.update("none");
    }
  });

  function series() {
    return cssVar("--qw-series-1");
  }

  function surface() {
    return cssVar("--qw-surface") || "#fff";
  }

  /** Single-series bar chart: one colour, no legend (the heading names the series).
   * token: the CSS colour token for the series (default --qw-series-1; depth uses --qw-series-2). */
  function bar(container, { labels, values, yTitle, xTitle, summary, columns, horizontal = false, format = fmt.num, token = "--qw-series-1" }) {
    return figure(container, {
      summary,
      config: {
        type: "bar",
        data: { labels, datasets: [{ label: yTitle, data: values, backgroundColor: cssVar(token), qwToken: token, borderRadius: 3, borderSkipped: "start", maxBarThickness: 32 }] },
        options: {
          indexAxis: horizontal ? "y" : "x",
          plugins: { legend: { display: false }, tooltip: { callbacks: { label: (ctx) => `${yTitle}: ${format(ctx.parsed[horizontal ? "x" : "y"])}` } } },
          scales: {
            [horizontal ? "x" : "y"]: { beginAtZero: true, title: { display: Boolean(yTitle), text: yTitle }, border: { display: false } },
            [horizontal ? "y" : "x"]: { title: { display: Boolean(xTitle), text: xTitle }, grid: { display: false } },
          },
        },
      },
      columns: columns || [xTitle || "", yTitle],
      rows: labels.map((l, i) => [String(l), format(values[i])]),
    });
  }

  window.QWCharts = { figure, palette, table, fmt, bar, series, surface, cssVar };
})();
