const statusDot = document.getElementById("statusDot");
const statusText = document.getElementById("statusText");
const alertsBody = document.getElementById("alertsBody");
const refreshInput = document.getElementById("refreshInput");

const totalCount = document.getElementById("totalCount");
const criticalCount = document.getElementById("criticalCount");
const highCount = document.getElementById("highCount");
const mediumCount = document.getElementById("mediumCount");
const lowCount = document.getElementById("lowCount");

const rowTemplate = document.getElementById("rowTemplate");

let timerId = null;

function setStatus(ok, message) {
  statusDot.classList.remove("ok", "bad");
  statusDot.classList.add(ok ? "ok" : "bad");
  statusText.textContent = message;
}

function labelClass(label) {
  const safe = (label || "other").toLowerCase();
  if (["critical", "high", "medium", "low"].includes(safe)) {
    return `severity-${safe}`;
  }
  return "severity-low";
}

function formatTime(raw) {
  const dt = new Date(raw);
  if (Number.isNaN(dt.getTime())) {
    return raw || "n/a";
  }
  return dt.toLocaleString();
}

function renderRows(alerts) {
  alertsBody.innerHTML = "";
  const rows = alerts.slice().reverse();

  for (const alert of rows) {
    const fragment = rowTemplate.content.cloneNode(true);
    fragment.querySelector(".time").textContent = formatTime(alert.timestamp);

    const sevCell = fragment.querySelector(".severity");
    const badge = document.createElement("span");
    const label = (alert.severity_label || "low").toLowerCase();
    badge.className = `severity-badge ${labelClass(label)}`;
    badge.textContent = label;
    sevCell.appendChild(badge);

    fragment.querySelector(".src").textContent = alert.src_ip || "unknown";
    fragment.querySelector(".dst").textContent = alert.dest_ip || "unknown";
    fragment.querySelector(".sig").textContent = alert.signature || "unknown-signature";
    fragment.querySelector(".proto").textContent = alert.proto || "unknown";

    alertsBody.appendChild(fragment);
  }
}

function renderSummary(summary) {
  totalCount.textContent = summary.total ?? 0;
  const counts = summary.counts || {};
  criticalCount.textContent = counts.critical ?? 0;
  highCount.textContent = counts.high ?? 0;
  mediumCount.textContent = counts.medium ?? 0;
  lowCount.textContent = counts.low ?? 0;
}

async function fetchJson(url) {
  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  return response.json();
}

async function refresh() {
  try {
    const [alertsData, summaryData] = await Promise.all([
      fetchJson("/api/alerts?limit=200"),
      fetchJson("/api/summary"),
    ]);
    renderRows(alertsData.alerts || []);
    renderSummary(summaryData || {});
    setStatus(true, "Connected");
  } catch (error) {
    setStatus(false, `Disconnected (${error.message})`);
  }
}

function startPolling() {
  if (timerId) {
    clearInterval(timerId);
  }

  const refreshSeconds = Math.max(1, Math.min(60, Number(refreshInput.value) || 2));
  timerId = setInterval(refresh, refreshSeconds * 1000);
}

refreshInput.addEventListener("change", () => {
  startPolling();
  refresh();
});

refresh();
startPolling();
