/* QuakeWatch map helpers (Leaflet + markercluster).
 *
 * The server decides between "points" (≤ 2000 events, clustered client-side by markercluster)
 * and "clusters" (server-side grid aggregation for dense viewports). Magnitude is shown by
 * marker size *and* colour; every map is paired with a text list elsewhere on the page, which
 * is the accessible equivalent of the markers.
 */
(function () {
  "use strict";
  const { h, fmt, band, loader } = window.QW;

  const TILE_URL = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png";
  const TILE_ATTRIBUTION = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors · Data: USGS';
  // Pulse halos mark strong, recent events: M4.5+ that occurred in the last 24 hours.
  const HALO_MIN_MAG = 4.5;
  const HALO_WINDOW_MS = 24 * 3600 * 1000;
  const HALO_MAX = 12; // keep continuous animation cheap on busy maps

  function cssVar(name) {
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  }

  function color(mag) {
    const b = band(mag);
    return cssVar(`--qw-mag-${b === null ? 0 : b}`);
  }

  function radius(mag) {
    if (mag === null || mag === undefined) return 3;
    return Math.max(3, Math.min(22, 2 + Math.pow(Math.max(mag, 0), 1.6)));
  }

  /** Circle-marker style for an event of magnitude `mag` in the current theme. */
  function markerStyle(mag) {
    return { radius: radius(mag), color: cssVar("--qw-marker-stroke"), weight: 1, fillColor: color(mag), fillOpacity: 0.85 };
  }

  function wrapLon(lon) {
    return ((((lon + 180) % 360) + 360) % 360) - 180;
  }

  /** Leaflet bounds → API bbox "south,west,north,east" (antimeridian-aware). */
  function bboxParam(map) {
    const b = map.getBounds();
    const south = Math.max(-90, b.getSouth());
    const north = Math.min(90, b.getNorth());
    if (b.getEast() - b.getWest() >= 360) return `${south.toFixed(4)},-180,${north.toFixed(4)},180`;
    return [south, wrapLon(b.getWest()), north, wrapLon(b.getEast())].map((v) => v.toFixed(4)).join(",");
  }

  function legendControl() {
    const control = L.control({ position: "bottomright" });
    control.onAdd = function () {
      const labels = ["< 2.5", "2.5 – 4.5", "4.5 – 6", "6 – 7", "≥ 7"];
      const div = h("div", { class: "qw-legend", role: "img", "aria-label": "Legend: circle size and colour grow with magnitude; a pulsing ring marks M4.5+ events from the last 24 hours" },
        h("strong", {}, "Magnitude"),
        labels.map((label, i) => h("div", {}, h("i", { class: `l${i}` }), label)),
        h("div", { class: "qw-legend-note" }, h("i", { class: "lp" }), "M4.5+, last 24 h"));
      L.DomEvent.disableClickPropagation(div);
      return div;
    };
    return control;
  }

  /** Cursor position readout (decorative duplicate of what the pointer shows; hidden from AT). */
  function coordsControl() {
    const control = L.control({ position: "bottomleft" });
    control.onAdd = function (map) {
      const div = h("div", { class: "qw-coords", "aria-hidden": "true" }, "—");
      const fmtLat = (v) => `${Math.abs(v).toFixed(2)}°${v >= 0 ? "N" : "S"}`;
      const fmtLon = (v) => `${Math.abs(v).toFixed(2)}°${v >= 0 ? "E" : "W"}`;
      const show = (ll) => { div.textContent = `${fmtLat(ll.lat)}  ${fmtLon(wrapLon(ll.lng))}`; };
      show(map.getCenter());
      map.on("mousemove", (e) => show(e.latlng));
      map.on("moveend", () => show(map.getCenter()));
      return div;
    };
    return control;
  }

  function create(el, { center = [20, 0], zoom = 2, legend = true, scrollWheelZoom = true } = {}) {
    const map = L.map(el, { center, zoom, minZoom: 1, maxZoom: 12, worldCopyJump: true, scrollWheelZoom });
    L.tileLayer(TILE_URL, { attribution: TILE_ATTRIBUTION, maxZoom: 18 }).addTo(map);
    if (legend) legendControl().addTo(map);
    coordsControl().addTo(map);
    el.setAttribute("role", "region");
    return map;
  }

  /** Show or hide a loading overlay over the map. Always call busy(map, false) when done. */
  function busy(map, on, label = "Loading earthquake data…") {
    const container = map.getContainer();
    const current = container.querySelector(".qw-busy-overlay");
    if (!on) {
      if (current) current.remove();
      return;
    }
    if (current) return;
    // the visible text duplicates the page's own role="status" line, so the overlay is not announced
    container.append(h("div", { class: "qw-busy-overlay", "aria-hidden": "true" }, loader(label, { size: "lg" })));
  }

  /** Move a reticle to `latlng` (or remove it with null). The ring acknowledges the selection. */
  function selectRing(map, latlng, mag) {
    if (map._qwSelect) { map._qwSelect.remove(); map._qwSelect = null; }
    if (!latlng) return;
    const size = Math.round(radius(mag) * 2 + 14);
    map._qwSelect = L.marker(latlng, {
      icon: L.divIcon({ html: "<span></span>", className: "qw-select-ring", iconSize: [size, size] }),
      interactive: false,
      keyboard: false,
      zIndexOffset: 1000,
    }).addTo(map);
  }

  function popup(key, mag, depth, occurredAt, place) {
    return h("div", {},
      h("div", { class: "fw-semibold" }, `M ${fmt.mag(mag)}`, place ? ` — ${place}` : ""),
      h("div", { class: "small" }, fmt.utc(occurredAt), " · depth ", fmt.depth(depth)),
      h("a", { href: `/events/${encodeURIComponent(key)}/` }, "Event details →"));
  }

  /**
   * A layer that renders an /events/map response. onSelect(key, latlng, mag) is called when a
   * point is clicked (e.g. to open a side panel).
   */
  function eventLayer(map, { onSelect } = {}) {
    const clusterGroup = L.markerClusterGroup({
      showCoverageOnHover: false,
      maxClusterRadius: 40,
      chunkedLoading: true,
      iconCreateFunction: (cluster) => {
        const n = cluster.getChildCount();
        const size = n < 10 ? 30 : n < 100 ? 38 : 46;
        return L.divIcon({ html: `<span>${n}</span>`, className: "qw-cluster", iconSize: [size, size] });
      },
    });
    const gridGroup = L.layerGroup();
    const haloGroup = L.layerGroup(); // not clustered: halos never change cluster counts
    map.addLayer(haloGroup);
    map.addLayer(clusterGroup);
    map.addLayer(gridGroup);
    let markers = [];

    function halos(points) {
      const now = Date.now();
      points
        .filter(([, , , mag, , occurredAt]) => mag !== null && mag >= HALO_MIN_MAG && now - new Date(occurredAt).getTime() <= HALO_WINDOW_MS)
        .sort((a, b) => b[3] - a[3])
        .slice(0, HALO_MAX)
        .forEach(([, lat, lon, mag]) => {
          const size = Math.round(radius(mag) * 2 + 10);
          haloGroup.addLayer(L.marker([lat, lon], {
            icon: L.divIcon({ html: "<span></span><span></span>", className: "qw-halo", iconSize: [size, size] }),
            interactive: false,
            keyboard: false,
          }));
        });
    }

    function render(data) {
      clusterGroup.clearLayers();
      gridGroup.clearLayers();
      haloGroup.clearLayers();
      markers = [];
      if (data.mode === "points") {
        markers = data.points.map(([key, lat, lon, mag, depth, occurredAt]) => {
          const marker = L.circleMarker([lat, lon], markerStyle(mag));
          marker.qwMag = mag;
          marker.bindPopup(() => popup(key, mag, depth, occurredAt));
          if (onSelect) marker.on("click", () => onSelect(key, marker.getLatLng(), mag));
          return marker;
        });
        clusterGroup.addLayers(markers);
        halos(data.points);
      } else {
        for (const c of data.clusters) {
          const size = Math.max(26, Math.min(60, 18 + Math.log2(c.count) * 5));
          const marker = L.marker([c.lat, c.lon], {
            icon: L.divIcon({ html: `<span>${c.count}</span>`, className: "qw-cluster", iconSize: [size, size] }),
            keyboard: true,
            title: `${c.count} events, strongest M ${fmt.mag(c.max_magnitude)}`,
            alt: `${c.count} events`,
          });
          marker.on("click", () => map.setView([c.lat, c.lon], Math.min(map.getZoom() + 3, 12)));
          gridGroup.addLayer(marker);
        }
      }
    }

    // markers carry the theme's colours: repaint them when the theme changes
    document.addEventListener("qw:theme", () => {
      for (const marker of markers) marker.setStyle(markerStyle(marker.qwMag));
    });

    return { render, clear: () => { clusterGroup.clearLayers(); gridGroup.clearLayers(); haloGroup.clearLayers(); markers = []; } };
  }

  window.QWMap = { create, eventLayer, bboxParam, color, radius, markerStyle, busy, selectRing, cssVar };
})();
