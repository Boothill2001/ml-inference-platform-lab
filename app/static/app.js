const form = document.querySelector("#predictForm");
const toast = document.querySelector("#toast");
const scoreButton = document.querySelector("#scoreButton");
const modeButtons = document.querySelectorAll(".segment");
const eventList = document.querySelector("#eventList");
const terminalPreview = document.querySelector("#terminalPreview");
let scoringMode = "production";

const samples = {
  low: {
    customer_age: 48,
    tenure_months: 72,
    monthly_spend: 54.2,
    num_support_tickets: 0,
    contract_type: "two_year",
    payment_delay_days: 1,
    usage_frequency: 34,
    model_version: "",
  },
  high: {
    customer_age: 29,
    tenure_months: 3,
    monthly_spend: 124.9,
    num_support_tickets: 7,
    contract_type: "monthly",
    payment_delay_days: 18,
    usage_frequency: 5,
    model_version: "",
  },
};

function showToast(message) {
  toast.textContent = message;
  toast.classList.add("show");
  window.setTimeout(() => toast.classList.remove("show"), 2600);
}

function addEvent(message) {
  const item = document.createElement("li");
  item.innerHTML = `<span></span><p>${message}</p>`;
  eventList.prepend(item);
  while (eventList.children.length > 5) {
    eventList.removeChild(eventList.lastElementChild);
  }
}

function payloadFromForm() {
  const data = new FormData(form);
  const payload = {
    customer_age: Number(data.get("customer_age")),
    tenure_months: Number(data.get("tenure_months")),
    monthly_spend: Number(data.get("monthly_spend")),
    num_support_tickets: Number(data.get("num_support_tickets")),
    contract_type: data.get("contract_type"),
    payment_delay_days: Number(data.get("payment_delay_days")),
    usage_frequency: Number(data.get("usage_frequency")),
  };
  const modelVersion = data.get("model_version");
  if (modelVersion && scoringMode === "production") {
    payload.model_version = modelVersion;
  }
  return payload;
}

function fillForm(sample) {
  Object.entries(sample).forEach(([key, value]) => {
    const field = form.elements.namedItem(key);
    if (field) field.value = value;
  });
}

function setMode(mode) {
  scoringMode = mode;
  modeButtons.forEach((button) => {
    button.classList.toggle("active", button.dataset.mode === mode);
  });
  scoreButton.innerHTML =
    mode === "canary"
      ? '<i data-lucide="git-branch"></i> Score via canary'
      : '<i data-lucide="play"></i> Score customer';
  lucide.createIcons();
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed: ${response.status}`);
  }
  return response.json();
}

function renderPrediction(result) {
  const probability = Math.round(result.churn_probability * 100);
  const degrees = Math.round(result.churn_probability * 360);
  const risk = result.risk_level;

  document.querySelector("#riskTitle").textContent =
    risk === "high" ? "High churn risk" : risk === "medium" ? "Medium churn risk" : "Low churn risk";
  document.querySelector("#riskPill").textContent = risk.toUpperCase();
  document.querySelector("#riskPill").className = `pill ${risk}`;
  document.querySelector("#probability").textContent = `${probability}%`;
  document.querySelector("#predictionLabel").textContent =
    result.prediction === 1 ? "Likely churn" : "Likely retained";
  document.querySelector("#modelVersion").textContent = `${result.model_name}:${result.model_version}`;
  document.querySelector("#requestId").textContent = result.request_id;
  document.querySelector("#latencyMs").textContent = `${result.latency_ms} ms`;
  document.querySelector("#lastLatency").textContent = `${result.latency_ms} ms`;
  document.querySelector(".gauge").style.background =
    `conic-gradient(var(--teal) ${degrees}deg, #e5ecef ${degrees}deg)`;
  terminalPreview.textContent = `POST /predict
model=${result.model_name}:${result.model_version}
latency=${result.latency_ms} ms
risk=${risk}
probability=${result.churn_probability}`;
  addEvent(
    `Inference completed with ${risk} risk on ${result.model_name}:${result.model_version} in ${result.latency_ms} ms.`
  );
}

async function submitPrediction(event) {
  event.preventDefault();
  scoreButton.disabled = true;
  const endpoint = scoringMode === "canary" ? "/predict/canary" : "/predict";

  try {
    const result = await api(endpoint, {
      method: "POST",
      body: JSON.stringify(payloadFromForm()),
    });
    renderPrediction(result);
    showToast(scoringMode === "canary" ? `Routed to ${result.routed_model_version}` : "Prediction complete");
  } catch (error) {
    showToast("Prediction failed. Check input values.");
    console.error(error);
  } finally {
    scoreButton.disabled = false;
  }
}

async function refreshReady() {
  try {
    const ready = await api("/ready");
    document.querySelector("#readyState").textContent = ready.ready ? "Ready" : "Not ready";
    document.querySelector("#readyModels").textContent = ready.loaded_models.join(", ");
    document.querySelector("#sidebarStatus").textContent = "API online";
    document.querySelector(".status-dot").classList.add("ok");
    addEvent(`Registry ready with ${ready.loaded_models.length} loaded model artifacts.`);
  } catch (error) {
    document.querySelector("#readyState").textContent = "Offline";
    document.querySelector("#readyModels").textContent = "Registry unavailable";
    document.querySelector("#sidebarStatus").textContent = "API offline";
  }
}

async function runCanarySampling() {
  const button = document.querySelector("#runCanary");
  button.disabled = true;
  const counts = { v1: 0, v2: 0 };
  const payload = { ...samples.high };
  delete payload.model_version;

  try {
    const calls = Array.from({ length: 25 }, () =>
      api("/predict/canary", { method: "POST", body: JSON.stringify(payload) })
    );
    const results = await Promise.all(calls);
    results.forEach((result) => {
      counts[result.routed_model_version] += 1;
    });
    const total = counts.v1 + counts.v2;
    const v1Width = Math.max(10, Math.round((counts.v1 / total) * 100));
    const v2Width = Math.max(10, 100 - v1Width);
    document.querySelector("#v1Bar").style.width = `${v1Width}%`;
    document.querySelector("#v2Bar").style.width = `${v2Width}%`;
    document.querySelector("#v1Count").textContent = counts.v1;
    document.querySelector("#v2Count").textContent = counts.v2;
    document.querySelector("#sampleCount").textContent = total;
    addEvent(`Canary sample routed ${counts.v1} requests to v1 and ${counts.v2} requests to v2.`);
    showToast("Canary sample complete");
  } catch (error) {
    showToast("Canary sample failed");
    console.error(error);
  } finally {
    button.disabled = false;
  }
}

async function checkDrift() {
  const button = document.querySelector("#checkDrift");
  button.disabled = true;
  const records = [
    { ...samples.high, monthly_spend: 142.4, payment_delay_days: 21, usage_frequency: 4 },
    { ...samples.high, customer_age: 27, monthly_spend: 131.1, payment_delay_days: 17 },
    { ...samples.high, num_support_tickets: 8, usage_frequency: 6 },
  ].map((record) => {
    delete record.model_version;
    return record;
  });

  try {
    const result = await api("/drift/check", {
      method: "POST",
      body: JSON.stringify({ records }),
    });
    document.querySelector("#driftScore").textContent = result.drift_score.toFixed(2);
    document.querySelector("#driftStatus").textContent = result.drift_detected
      ? "Drift detected against baseline"
      : "No drift detected";
    const tags = document.querySelector("#driftFeatures");
    tags.innerHTML = "";
    const features = result.features_with_drift.length ? result.features_with_drift : ["no flagged features"];
    features.forEach((feature) => {
      const tag = document.createElement("span");
      tag.className = "tag";
      tag.textContent = feature;
      tags.appendChild(tag);
    });
    addEvent(
      result.drift_detected
        ? `Drift signal raised at score ${result.drift_score.toFixed(2)} for ${features.join(", ")}.`
        : `Drift check passed at score ${result.drift_score.toFixed(2)}.`
    );
    showToast("Drift check complete");
  } catch (error) {
    showToast("Drift check failed");
    console.error(error);
  } finally {
    button.disabled = false;
  }
}

document.querySelector("#loadLowRisk").addEventListener("click", () => fillForm(samples.low));
document.querySelector("#loadHighRisk").addEventListener("click", () => fillForm(samples.high));
document.querySelector("#runCanary").addEventListener("click", runCanarySampling);
document.querySelector("#checkDrift").addEventListener("click", checkDrift);
form.addEventListener("submit", submitPrediction);
modeButtons.forEach((button) => button.addEventListener("click", () => setMode(button.dataset.mode)));

refreshReady();
lucide.createIcons();
