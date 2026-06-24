/**
 * AgriCrop – Dashboard JS
 * Loads stats, charts, recent predictions, farms, and notification badge.
 */

document.addEventListener("DOMContentLoaded", async () => {
  Auth.requireAuth();
  Utils.showSkeleton("stats-grid", 4, "100px");
  Utils.showSkeleton("recent-disease-list", 3, "70px");
  Utils.showSkeleton("recent-soil-list", 3, "70px");

  try {
    const data = await AgriCropAPI.history.getDashboard();
    renderStats(data);
    renderCharts(data);
    renderRecentPredictions(data);
    renderFarms(data.farms || []);
    loadUnreadCount();
    Utils.initEntranceAnimations();
  } catch (e) {
    Utils.showToast("Failed to load dashboard data.", "error");
    console.error(e);
  }
});

function renderStats(data) {
  const user = Auth.getUser();
  const nameEl = document.getElementById("welcome-name");
  if (nameEl) nameEl.textContent = user?.name?.split(" ")[0] || "Farmer";

  const stats = [
    { id: "stat-total-preds",  value: data.total_predictions || 0,         suffix: "" },
    { id: "stat-disease-preds",value: data.total_disease_predictions || 0, suffix: "" },
    { id: "stat-soil-preds",   value: data.total_soil_predictions || 0,    suffix: "" },
    { id: "stat-farms",        value: data.total_farms || 0,                suffix: "" },
    { id: "stat-healthy",      value: data.severity_breakdown?.healthy || 0,suffix: "" },
    { id: "stat-diseased",     value: data.diseased_count || 0,             suffix: "" },
    { id: "stat-moisture",     value: data.average_soil_moisture || 0,      suffix: "%" },
    { id: "stat-irrigation",   value: data.irrigation_needed_count || 0,    suffix: "" },
  ];
  const statsGrid = document.getElementById("stats-grid");
  if (statsGrid) statsGrid.innerHTML = buildStatsHTML(data);

  setTimeout(() => {
    stats.forEach(s => {
      const el = document.getElementById(s.id);
      if (el) Utils.animateCounter(el, s.value, 1200, s.suffix);
    });
  }, 50);
}

function buildStatsHTML(data) {
  const sev = data.severity_breakdown || {};
  return `
    <div class="col-sm-6 col-xl-3 anim-hidden animate-fade-up delay-100">
      <div class="stat-card">
        <div class="stat-icon green">🌾</div>
        <div>
          <div class="stat-label">Total Scans</div>
          <div class="stat-value" id="stat-total-preds">0</div>
          <div class="stat-change up">↑ Disease + Soil</div>
        </div>
      </div>
    </div>
    <div class="col-sm-6 col-xl-3 anim-hidden animate-fade-up delay-200">
      <div class="stat-card">
        <div class="stat-icon red">🦠</div>
        <div>
          <div class="stat-label">Disease Scans</div>
          <div class="stat-value" id="stat-disease-preds">0</div>
          <div class="stat-change ${data.severity_breakdown?.severe > 0 ? 'down' : 'up'}">
            ${data.severity_breakdown?.severe || 0} severe cases
          </div>
        </div>
      </div>
    </div>
    <div class="col-sm-6 col-xl-3 anim-hidden animate-fade-up delay-300">
      <div class="stat-card">
        <div class="stat-icon blue">💧</div>
        <div>
          <div class="stat-label">Soil Predictions</div>
          <div class="stat-value" id="stat-soil-preds">0</div>
          <div class="stat-change ${data.irrigation_needed_count > 0 ? 'down' : 'up'}">
            ${data.irrigation_needed_count || 0} need irrigation
          </div>
        </div>
      </div>
    </div>
    <div class="col-sm-6 col-xl-3 anim-hidden animate-fade-up delay-400">
      <div class="stat-card">
        <div class="stat-icon amber">🌡️</div>
        <div>
          <div class="stat-label">Avg Soil Moisture</div>
          <div class="stat-value" id="stat-moisture">0</div>
          <div class="stat-change up">% moisture level</div>
        </div>
      </div>
    </div>
  `;
}

function renderCharts(data) {
  Charts.renderSeverityDonut("severity-chart", data.severity_breakdown || {});
  Charts.renderMonthlyBar("monthly-chart", data.monthly_disease_counts, data.monthly_soil_counts);
  Charts.renderHealthPie("health-pie-chart", data.healthy_count || 0, data.diseased_count || 0);
}

function renderRecentPredictions(data) {
  // Disease
  const dList = document.getElementById("recent-disease-list");
  const dPreds = data.recent_disease_predictions || [];
  if (dList) {
    if (!dPreds.length) {
      dList.innerHTML = `<div class="text-center py-4 text-muted"><small>No disease predictions yet.<br><a href="/upload.html" class="text-success">Upload your first leaf image →</a></small></div>`;
    } else {
      dList.innerHTML = dPreds.map(p => `
        <a href="/disease-result.html?id=${p.prediction_id}" class="d-flex align-items-center gap-3 p-3 mb-2 ag-card text-decoration-none" style="border-radius:10px;">
          <img src="${p.image_url || 'assets/images/leaf-placeholder.png'}" alt="leaf" style="width:48px;height:48px;border-radius:8px;object-fit:cover;flex-shrink:0;">
          <div style="min-width:0;flex:1;">
            <div class="fw-600 truncate" style="font-size:0.88rem;color:var(--text-primary);">${p.disease_name || "Unknown"}</div>
            <div class="d-flex align-items-center gap-2 mt-1">
              ${Utils.severityBadge(p.severity || "unknown")}
              <small class="text-muted">${Utils.formatRelativeTime(p.created_at)}</small>
            </div>
          </div>
          <div style="font-size:0.88rem;font-weight:600;color:var(--primary-light);">
            ${Utils.formatConfidence(p.confidence || 0)}
          </div>
        </a>
      `).join("");
    }
  }

  // Soil
  const sList = document.getElementById("recent-soil-list");
  const sPreds = data.recent_soil_predictions || [];
  if (sList) {
    if (!sPreds.length) {
      sList.innerHTML = `<div class="text-center py-4 text-muted"><small>No soil predictions yet.<br><a href="/soil-prediction.html" class="text-success">Run a soil analysis →</a></small></div>`;
    } else {
      sList.innerHTML = sPreds.map(p => `
        <a href="/history.html" class="d-flex align-items-center gap-3 p-3 mb-2 ag-card text-decoration-none" style="border-radius:10px;">
          <div class="stat-icon blue" style="width:48px;height:48px;border-radius:10px;font-size:1.3rem;flex-shrink:0;">💧</div>
          <div style="min-width:0;flex:1;">
            <div class="fw-600" style="font-size:0.88rem;color:var(--text-primary);">
              Moisture: ${Utils.formatMoisture(p.predicted_moisture)}
            </div>
            <div class="d-flex align-items-center gap-2 mt-1">
              <span class="badge-severity ${p.irrigation_recommended ? 'moderate' : 'healthy'}" style="font-size:0.7rem;">
                ${p.irrigation_recommended ? "💧 Irrigation Needed" : "✅ OK"}
              </span>
              <small class="text-muted">${Utils.formatRelativeTime(p.created_at)}</small>
            </div>
          </div>
          <div style="font-size:0.78rem;color:var(--text-muted);text-transform:capitalize;">
            ${p.irrigation_type || "none"}
          </div>
        </a>
      `).join("");
    }
  }
}

function renderFarms(farms) {
  const el = document.getElementById("farms-list");
  if (!el) return;
  if (!farms.length) {
    el.innerHTML = `<div class="text-center py-4"><small class="text-muted">No farms added yet.<br><a href="/profile.html" class="text-success">Add your farm →</a></small></div>`;
    return;
  }
  el.innerHTML = farms.slice(0, 4).map(f => `
    <div class="d-flex align-items-center gap-3 p-3 mb-2" style="background:var(--bg-input);border-radius:10px;border:1px solid var(--border);">
      <div class="stat-icon green" style="width:40px;height:40px;border-radius:8px;font-size:1rem;flex-shrink:0;">🌱</div>
      <div style="min-width:0;flex:1;">
        <div class="fw-600 truncate" style="font-size:0.88rem;color:var(--text-primary);">${f.name}</div>
        <small class="text-muted">${[f.district, f.state].filter(Boolean).join(", ") || "Location not set"}</small>
      </div>
      <small class="text-muted">${(f.crop_types || []).slice(0, 2).join(", ") || "No crops"}</small>
    </div>
  `).join("");
}

async function loadUnreadCount() {
  try {
    const res = await AgriCropAPI.notifications.unreadCount();
    const badge = document.getElementById("notif-badge");
    if (badge && res.unread_count > 0) {
      badge.textContent = res.unread_count;
      badge.classList.remove("hidden");
    }
  } catch (e) { /* silent */ }
}
