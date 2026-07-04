const TORONTO_CENTER = [43.6532, -79.3832];
let map = null;
let routeLayer = null;
let selectedAgentIndex = 0;
let currentPlan = null;

const els = {
  form: document.getElementById("controls"),
  runBtn: document.getElementById("run-btn"),
  loading: document.getElementById("loading"),
  error: document.getElementById("error"),
  results: document.getElementById("results"),
  empty: document.getElementById("empty"),
  heroStats: document.getElementById("hero-stats"),
  priorityZone: document.getElementById("priority-zone"),
  pipeline: document.getElementById("agent-pipeline"),
  matches: document.getElementById("matches"),
  routeStops: document.getElementById("route-stops"),
  ethics: document.getElementById("ethics"),
  auditTrail: document.getElementById("audit-trail"),
  pickupSchedule: document.getElementById("pickup-schedule"),
};

function initMap() {
  if (map) return;
  map = L.map("map").setView(TORONTO_CENTER, 11);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: '&copy; <a href="https://openstreetmap.org/copyright">OpenStreetMap</a>',
  }).addTo(map);
  routeLayer = L.layerGroup().addTo(map);
}

function esc(text) {
  const d = document.createElement("div");
  d.textContent = text ?? "";
  return d.innerHTML;
}

function renderHero(plan) {
  const approved = plan.matches.filter((m) => m.approved).length;
  const zone = plan.priority_zone?.region ?? "—";
  const km = plan.route_stats?.total_km ?? "—";
  const mins = plan.route_stats?.est_minutes ?? "—";
  const smallOrg = plan.ethics_report?.small_org_allocations ?? 0;

  els.heroStats.innerHTML = `
    <div class="stat-card"><div class="label">Priority zone</div><div class="value">${esc(zone)}</div></div>
    <div class="stat-card coral"><div class="label">Matches</div><div class="value">${plan.matches.length}</div></div>
    <div class="stat-card green"><div class="label">Approved</div><div class="value">${approved}</div></div>
    <div class="stat-card"><div class="label">Small-org</div><div class="value">${smallOrg}</div></div>
    <div class="stat-card"><div class="label">Route</div><div class="value">${km} km</div></div>
    <div class="stat-card"><div class="label">Est. time</div><div class="value">${mins} min</div></div>
  `;
}

function renderPriorityZone(zone) {
  if (!zone) {
    els.priorityZone.innerHTML = "<p>No priority zone identified.</p>";
    return;
  }
  const signals = (zone.top_signals || [])
    .map((s) => `<li>${esc(s)}</li>`)
    .join("");
  els.priorityZone.innerHTML = `
    <div class="zone-name">${esc(zone.region)}</div>
    <div class="meta">
      <span>Need score: ${zone.priority_score}</span>
      <span>${zone.event_count} GDELT events</span>
      ${zone.biomass_need_score ? `<span>Biomass signal: ${zone.biomass_need_score}</span>` : ""}
    </div>
    <ul class="signals">${signals || "<li>No headline signals</li>"}</ul>
  `;
}

function renderPipeline(logs) {
  els.pipeline.innerHTML = logs
    .map(
      (log, i) => `
    <li class="pipeline-item${i === selectedAgentIndex ? " active" : ""}" data-index="${i}">
      <span class="step-num">${i + 1}</span>
      <div>
        <span class="agent-name">${esc(log.agent_name)}</span>
        <span class="summary">${esc(log.summary)}</span>
        ${log.approved_count != null ? `<span class="counts">✓${log.approved_count} / ✗${log.rejected_count ?? 0}</span>` : ""}
      </div>
    </li>`
    )
    .join("");

  els.pipeline.querySelectorAll(".pipeline-item").forEach((el) => {
    el.addEventListener("click", () => {
      selectedAgentIndex = parseInt(el.dataset.index, 10);
      renderPipeline(currentPlan.agent_logs);
      renderAuditTrail(currentPlan.agent_logs[selectedAgentIndex]);
    });
  });
}

function renderAuditTrail(log) {
  if (!log?.decision_steps?.length) {
    els.auditTrail.innerHTML = "<p class='hint'>No decision steps recorded for this agent.</p>";
    return;
  }
  els.auditTrail.innerHTML = log.decision_steps
    .map(
      (step) => `
    <div class="audit-step">
      <div class="step-label">Step ${step.step}</div>
      <div class="audit-rule">${esc(step.rule)}</div>
      <div class="audit-io"><strong>Input:</strong> ${esc(step.input_summary)}</div>
      <div class="audit-outcome"><strong>Outcome:</strong> ${esc(step.outcome)}</div>
      ${
        step.metadata && Object.keys(step.metadata).length
          ? `<pre class="audit-meta">${esc(JSON.stringify(step.metadata, null, 2))}</pre>`
          : ""
      }
    </div>`
    )
    .join("");
}

function renderMatches(matches) {
  if (!matches.length) {
    els.matches.innerHTML = "<p>No matches generated.</p>";
    return;
  }
  els.matches.innerHTML = matches
    .map((m) => {
      const status = m.approved ? "approved" : "deferred";
      const reasons = m.reasons.map((r) => `<li>${esc(r)}</li>`).join("");
      const flags = m.ethics_flags
        .map((f) => `<p class="flag">⚠️ ${esc(f)}</p>`)
        .join("");
      return `
      <article class="match-card ${status}">
        <div class="match-header">
          <h3>${esc(m.donor.name)} → ${esc(m.recipient.name)}</h3>
          <span class="badge ${status}">${status}</span>
        </div>
        <div class="match-meta">
          Score ${m.match_score.toFixed(2)} · ${m.distance_km.toFixed(1)} km ·
          ${m.allocated_kg?.toFixed(1) ?? "—"} kg · tier: ${esc(m.fairness_tier || "standard")}
        </div>
        <ul class="match-reasons">${reasons}</ul>
        ${flags}
      </article>`;
    })
    .join("");
}

function renderRoute(stops) {
  if (!stops.length) {
    els.routeStops.innerHTML = "<li>No route planned.</li>";
    return;
  }
  els.routeStops.innerHTML = stops
    .map((s) => {
      const icon = s.stop_type === "pickup" ? "📦" : "🏠";
      return `
      <li>
        <span class="icon">${icon}</span>
        <div>
          <div class="stop-name">${s.sequence}. ${esc(s.name)}</div>
          <div class="stop-notes">${esc(s.notes)}${s.cumulative_km ? ` · ${s.cumulative_km} km` : ""}</div>
        </div>
      </li>`;
    })
    .join("");
}

function renderPickupSchedule(schedule) {
  if (!schedule?.length) {
    els.pickupSchedule.innerHTML = "<li>No windows negotiated.</li>";
    return;
  }
  els.pickupSchedule.innerHTML = schedule
    .map(
      (w) => `
    <li>
      <span class="icon">🕐</span>
      <div>
        <div class="stop-name">${esc(w.name)}</div>
        <div class="stop-notes">${esc(w.start)} – ${esc(w.end)}</div>
      </div>
    </li>`
    )
    .join("");
}

function renderEthics(report) {
  const issues = report.safety_issues.length
    ? `<ul>${report.safety_issues.map((i) => `<li>${esc(i)}</li>`).join("")}</ul>`
    : "";
  const recs = report.recommendations
    .slice(0, 5)
    .map((r) => `<li>${esc(r)}</li>`)
    .join("");
  const approvalClass = report.human_approval_required ? "" : "ok";
  const approvalText = report.human_approval_required
    ? "⛔ Human approval required before dispatch"
    : "✓ Ready for coordinator review";

  els.ethics.innerHTML = `
    <div class="fairness">Fairness score: ${report.fairness_score}</div>
    ${report.environmental_note ? `<p class="env-note">${esc(report.environmental_note)}</p>` : ""}
    ${issues}
    <ul>${recs}</ul>
    <div class="approval-banner ${approvalClass}">${approvalText}</div>
  `;
}

function renderMap(plan) {
  initMap();
  routeLayer.clearLayers();
  const bounds = [];

  plan.route.forEach((stop) => {
    const latlng = [stop.latitude, stop.longitude];
    bounds.push(latlng);
    const color = stop.stop_type === "pickup" ? "#2d8a6e" : "#d4654a";
    const marker = L.circleMarker(latlng, {
      radius: 8,
      fillColor: color,
      color: "#fff",
      weight: 2,
      fillOpacity: 0.9,
    }).bindPopup(`<strong>${esc(stop.name)}</strong><br>${esc(stop.notes)}`);
    routeLayer.addLayer(marker);
  });

  if (plan.route.length >= 2) {
    const latlngs = plan.route.map((s) => [s.latitude, s.longitude]);
    L.polyline(latlngs, { color: "#0f5c5c", weight: 3, opacity: 0.7, dashArray: "8 6" }).addTo(
      routeLayer
    );
  }

  if (bounds.length) {
    map.fitBounds(bounds, { padding: [40, 40] });
  } else {
    map.setView(TORONTO_CENTER, 11);
  }
}

function renderPlan(plan) {
  currentPlan = plan;
  selectedAgentIndex = 0;
  renderHero(plan);
  renderPriorityZone(plan.priority_zone);
  renderPipeline(plan.agent_logs);
  renderAuditTrail(plan.agent_logs[0]);
  renderMatches(plan.matches);
  renderRoute(plan.route);
  renderPickupSchedule(plan.pickup_schedule);
  renderEthics(plan.ethics_report);
  renderMap(plan);
}

async function runPlanning(e) {
  e.preventDefault();
  const region = document.getElementById("region").value;
  const top = document.getElementById("top").value;
  const fast = document.getElementById("fast").checked;
  const maxDistance = document.getElementById("max_distance_km").value;

  const params = new URLSearchParams({ top, fast, max_distance_km: maxDistance });
  if (region) params.set("region", region);

  els.empty.classList.add("hidden");
  els.results.classList.add("hidden");
  els.error.classList.add("hidden");
  els.loading.classList.remove("hidden");
  els.runBtn.disabled = true;

  try {
    const res = await fetch(`/api/plan?${params}`);
    if (!res.ok) throw new Error(`Server error (${res.status})`);
    const plan = await res.json();
    els.loading.classList.add("hidden");
    els.results.classList.remove("hidden");
    renderPlan(plan);
    setTimeout(() => map?.invalidateSize(), 100);
  } catch (err) {
    els.loading.classList.add("hidden");
    els.error.textContent = err.message || "Failed to run planning.";
    els.error.classList.remove("hidden");
  } finally {
    els.runBtn.disabled = false;
  }
}

els.form.addEventListener("submit", runPlanning);
