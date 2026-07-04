const AGENT_ORDER = [
  { key: "ethics_decision", label: "Ethics Agent", id: "ethics" },
  { key: "surplus_decision", label: "Surplus Agent", id: "surplus" },
  { key: "need_decision", label: "Need Agent", id: "need" },
  { key: "matching_decision", label: "Matching Agent", id: "matching" },
  { key: "logistics_decision", label: "Logistics Agent", id: "logistics" },
  { key: "coordinator_summary", label: "Coordinator", id: "coordinator" },
];

let pipelineData = null;
let selectedAgentKey = "ethics_decision";

const runBtn = document.getElementById("runBtn");
const agentCards = document.getElementById("agentCards");
const auditTrail = document.getElementById("auditTrail");
const allocList = document.getElementById("allocList");
const routeList = document.getElementById("routeList");

runBtn.addEventListener("click", runPipeline);

async function loadStats() {
  const res = await fetch("/api/stats");
  const data = await res.json();
  document.getElementById("statEst").textContent = data.dinesafe_establishments.toLocaleString();
}

async function runPipeline() {
  runBtn.disabled = true;
  document.body.classList.add("loading");

  const params = new URLSearchParams({
    max_donors: document.getElementById("maxDonors").value,
    max_allocations: document.getElementById("maxAlloc").value,
    max_distance_km: document.getElementById("maxDist").value,
    refresh: "true",
  });

  try {
    const res = await fetch(`/api/pipeline/run?${params}`);
    pipelineData = await res.json();
    renderAll();
  } catch (err) {
    alert("Pipeline failed: " + err.message);
  } finally {
    runBtn.disabled = false;
    document.body.classList.remove("loading");
  }
}

function renderAll() {
  if (!pipelineData) return;
  const s = pipelineData.stats;
  document.getElementById("statDonors").textContent = s.eligible_donors;
  document.getElementById("statAlloc").textContent = s.allocations;
  document.getElementById("statKg").textContent = `${s.total_kg} kg`;
  document.getElementById("statKm").textContent = `${s.route_km} km`;

  renderAgentCards();
  renderAllocations();
  renderRoute();
  renderAudit(selectedAgentKey);
}

function renderAgentCards() {
  agentCards.innerHTML = AGENT_ORDER.map(({ key, label, id }) => {
    const d = pipelineData[key];
    const active = key === selectedAgentKey ? " active" : "";
    const counts = d.approved_count != null
      ? ` · ✓${d.approved_count} / ✗${d.rejected_count}`
      : "";
    return `
      <div class="agent-card${active}" data-agent="${id}" data-key="${key}">
        <div class="name">${label}${counts}</div>
        <div class="summary">${d.summary}</div>
      </div>`;
  }).join("");

  agentCards.querySelectorAll(".agent-card").forEach((el) => {
    el.addEventListener("click", () => {
      selectedAgentKey = el.dataset.key;
      renderAgentCards();
      renderAudit(selectedAgentKey);
    });
  });
}

function renderAllocations() {
  const items = pipelineData.allocations;
  if (!items.length) {
    allocList.innerHTML = "<p class='hint'>No matches within distance constraint.</p>";
    return;
  }
  allocList.innerHTML = items.map((a) => `
    <div class="alloc-item">
      <div class="row">
        <span class="donor">${esc(a.donor.name)}</span>
        <span>${a.allocated_kg} kg</span>
      </div>
      <div class="meta">
        → ${esc(a.recipient.name)} · ${a.distance_km} km
        · <span class="tier">${a.fairness_tier}</span>
      </div>
      <div class="meta">${esc(a.matching_reason)}</div>
    </div>
  `).join("");
}

function renderRoute() {
  const route = pipelineData.route;
  if (!route.length) {
    routeList.innerHTML = "<li class='hint'>No route</li>";
    return;
  }
  routeList.innerHTML = route.map((stop) => {
    const typeClass = `type-${stop.stop_type}`;
    const kg = stop.allocated_kg ? ` · ${stop.allocated_kg} kg` : "";
    return `
      <li>
        <span class="seq">${stop.sequence}</span>
        <span class="${typeClass}">[${stop.stop_type}]</span>
        <span>${esc(stop.name)}${kg}</span>
        <span style="margin-left:auto;color:var(--muted)">${stop.cumulative_km} km</span>
      </li>`;
  }).join("");
}

function renderAudit(key) {
  const decision = pipelineData[key];
  if (!decision?.steps?.length) {
    auditTrail.innerHTML = "<p class='hint'>No steps recorded.</p>";
    return;
  }
  auditTrail.innerHTML = decision.steps.map((step) => `
    <div class="audit-step">
      <div class="step-num">Step ${step.step}</div>
      <div class="rule">${esc(step.rule)}</div>
      <div class="io"><strong>Input:</strong> ${esc(step.input_summary)}</div>
      <div class="outcome"><strong>Outcome:</strong> ${esc(step.outcome)}</div>
      ${Object.keys(step.metadata || {}).length
        ? `<pre class="meta">${esc(JSON.stringify(step.metadata, null, 2))}</pre>`
        : ""}
    </div>
  `).join("");
}

function esc(s) {
  const d = document.createElement("div");
  d.textContent = s ?? "";
  return d.innerHTML;
}

loadStats().then(runPipeline);
