const API_BASE = "";
  const $ = (id) => document.getElementById(id);
  const statusEl = $("status");
  const editModal = $("editModal");

  let experimentsCache = [];
  let publicsCache = [];

  $("apiBase").textContent = location.origin;

  function setStatus(msg, isError=false){
    statusEl.textContent = msg;
    statusEl.style.borderColor = isError ? "#ef4444" : "#e5e5e5";
    statusEl.style.color = isError ? "#b91c1c" : "#6b7280";
  }

  function showToast(message, type = 'success') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast toast--${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
  }

  function asIntOrNull(v) {
    if (v === "" || v === null || v === undefined) return null;
    const n = Number(v);
    return Number.isFinite(n) ? n : null;
  }
  function asFloatOrNull(v) {
    if (v === "" || v === null || v === undefined) return null;
    const n = Number(v);
    return Number.isFinite(n) ? n : null;
  }

  async function apiGet(path) {
    const r = await fetch(API_BASE + path);
    if (!r.ok) throw new Error(await r.text());
    return r.json();
  }

  async function apiPost(path, body) {
    const r = await fetch(API_BASE + path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!r.ok) throw new Error(await r.text());
    return r.json();
  }

  async function apiPatch(path, body) {
    const r = await fetch(API_BASE + path, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!r.ok) throw new Error(await r.text());
    return r.json();
  }

  function openEditModal() {
    editModal.classList.remove("hidden");
    editModal.setAttribute("aria-hidden", "false");
  }

  function closeEditModal() {
    editModal.classList.add("hidden");
    editModal.setAttribute("aria-hidden", "true");
  }

  function uniqueSorted(values){
    return [...new Set(values.filter(Boolean))].sort((a, b) => a.localeCompare(b, "es"));
  }

  function fillPublicSelect(selectEl, keepValue=true){
    const prev = keepValue ? selectEl.value : "";
    selectEl.innerHTML = "";
    const optNone = document.createElement("option");
    optNone.value = "";
    optNone.textContent = "Sin público";
    selectEl.appendChild(optNone);
    publicsCache.forEach(publico => {
      const opt = document.createElement("option");
      opt.value = publico.id;
      opt.textContent = publico.name;
      selectEl.appendChild(opt);
    });
    if (keepValue && prev && [...selectEl.options].some(o => o.value === prev)) {
      selectEl.value = prev;
    } else {
      selectEl.value = "";
    }
  }

  async function loadPublics(){
    publicsCache = await apiGet("/publics");
    ["organic_publico", "live_publico", "paid_publico", "upd_publico"].forEach(id => {
      const el = $(id);
      if (el) fillPublicSelect(el);
    });
  }

  function fillFilterSelect(selectEl, options, keepValue=true, allLabel="(todos)"){
    const prev = keepValue ? selectEl.value : "";
    selectEl.innerHTML = "";
    const optAll = document.createElement("option");
    optAll.value = "";
    optAll.textContent = allLabel;
    selectEl.appendChild(optAll);
    for (const value of options){
      const opt = document.createElement("option");
      opt.value = value;
      opt.textContent = value;
      selectEl.appendChild(opt);
    }
    if (keepValue && prev && [...selectEl.options].some(o => o.value === prev)) {
      selectEl.value = prev;
    } else {
      selectEl.value = "";
    }
  }

  function syncProjectNameOptions(){
    const projectSelect = $("project_existing");
    const projectNames = uniqueSorted(experimentsCache.map(e => e.project_name));
    const prev = projectSelect.value;
    projectSelect.innerHTML = '<option value="">-- seleccionar --</option>';
    for (const name of projectNames) {
      const opt = document.createElement("option");
      opt.value = name;
      opt.textContent = name;
      projectSelect.appendChild(opt);
    }
    if (prev && [...projectSelect.options].some(o => o.value === prev)) {
      projectSelect.value = prev;
    }
  }

  function updateProjectModeVisibility(){
    const mode = $("project_mode").value;
    const isExisting = mode === "existing";
    $("project_existing_group").style.display = isExisting ? "" : "none";
    $("project_name_group").style.display = isExisting ? "none" : "";
  }

  // Auto-fill session ID when metric X is selected
  async function autoFillSessionId(expId, sessionInputId, prefix) {
    if (!expId) return;
    try {
      const recs = await apiGet(`/records/?experiment_id=${expId}&limit=50000`);
      const next = recs.length + 1;
      $(sessionInputId).value = `${prefix}-${String(next).padStart(3, '0')}`;
    } catch(e) {
      $(sessionInputId).value = `${prefix}-001`;
    }
  }

  function pickExperimentForRecord({ prefix, trafficType }) {
    const project = $(`${prefix}_project_filter`).value;
    const metricX = $(`${prefix}_metric_x_filter`).value;
    const candidates = experimentsCache.filter(e => {
      if (e.traffic_type !== trafficType) return false;
      if (project && e.project_name !== project) return false;
      if (metricX && e.independent_variable !== metricX) return false;
      return true;
    });
    if (!candidates.length) {
      $(`${prefix}_experiment_id`).value = "";
      return null;
    }
    const chosen = candidates.slice().sort((a, b) => b.id - a.id)[0];
    $(`${prefix}_experiment_id`).value = String(chosen.id);
    return chosen;
  }

  function updateRecordFormFilters({ prefix, trafficType, sessionPrefix }){
    const formExps = experimentsCache.filter(e => e.traffic_type === trafficType);
    const projectSel = $(`${prefix}_project_filter`);
    const metricSel = $(`${prefix}_metric_x_filter`);

    fillFilterSelect(projectSel, uniqueSorted(formExps.map(e => e.project_name)), true, "(todos)");
    const project = projectSel.value;
    const byProject = formExps.filter(e => !project || e.project_name === project);
    fillFilterSelect(metricSel, uniqueSorted(byProject.map(e => e.independent_variable)), true, "(todas)");
    const chosen = pickExperimentForRecord({ prefix, trafficType });
    if (chosen) {
      autoFillSessionId(chosen.id, `${prefix}_session_id`, sessionPrefix);
    }
  }

  function updateUpdateRecordFilters(){
    const projectSel = $("upd_project_filter");
    const metricSel = $("upd_metric_x_filter");
    const channel = $("upd_channel_filter").value;
    const channelExperiments = experimentsCache.filter(e => !channel || e.traffic_type === channel);
    fillFilterSelect(projectSel, uniqueSorted(channelExperiments.map(e => e.project_name)), true, "(todos)");
    const project = projectSel.value;
    const metricCandidates = channelExperiments.filter(e => !project || e.project_name === project);
    fillFilterSelect(metricSel, uniqueSorted(metricCandidates.map(e => e.independent_variable)), true, "(todas)");
  }

  function syncFormSelects(){
    syncProjectNameOptions();
    updateProjectModeVisibility();
    updateRecordFormFilters({ prefix: "organic", trafficType: "organic", sessionPrefix: "s" });
    updateRecordFormFilters({ prefix: "paid", trafficType: "paid", sessionPrefix: "p" });
    updateRecordFormFilters({ prefix: "live", trafficType: "live", sessionPrefix: "l" });
    updateUpdateRecordFilters();
    refreshRecordList().catch(e => { setStatus("error", true); showToast(String(e), 'error'); });
  }

  async function refreshAll() {
    setStatus("cargando...");
    experimentsCache = await apiGet("/experiments/");
    await loadPublics();
    syncFormSelects();
    refreshRecordList().catch(e => { setStatus("error", true); showToast(String(e), 'error'); });
    setStatus("listo");
  }

  // Eventos
  $("btnRefresh").onclick = async () => {
    try { await refreshAll(); }
    catch(e){ setStatus("error", true); showToast(String(e), 'error'); }
  };

  // Create experiment
  $("btnCreateExperiment").onclick = async () => {
    try {
      const projectMode = $("project_mode").value;
      const projectName = projectMode === "existing"
        ? $("project_existing").value
        : $("project_name").value.trim();
      const body = {
        project_name: projectName,
        hypothesis: $("hypothesis").value.trim(),
        traffic_type: $("traffic_type").value,
        hypothesis_type: $("hypothesis_type").value || null,
        independent_variable: $("independent_variable").value.trim() || null,
        primary_metric: $("primary_metric").value || null,
        threshold_operator: $("threshold_operator").value || null,
        threshold_value: asFloatOrNull($("threshold_value").value),
        threshold_type: $("threshold_type").value || null,
        volume_min_value: asIntOrNull($("volume_min_value").value),
        volume_unit: $("volume_unit").value || null,
        experiment_status: "draft",
        contexto: $("contexto").value.trim() || null,
      };
      if (!body.project_name || !body.hypothesis) throw new Error("project_name y hypothesis son obligatorios.");
      await apiPost("/experiments/", body);
      await refreshAll();
      ["project_name","hypothesis","independent_variable","threshold_value","volume_min_value","contexto"].forEach(id => $(id).value = "");
      $("project_mode").value = "new";
      $("project_existing").value = "";
      $("hypothesis_type").value = "";
      $("primary_metric").value = "";
      $("threshold_operator").value = "";
      $("threshold_type").value = "";
      $("volume_unit").value = "";
      $("traffic_type").value = "paid";
    } catch(e){
      setStatus("error", true);
      showToast(String(e), 'error');
    }
  };

  // Create organic record
  $("btnCreateOrganicRecord").onclick = async () => {
    try {
      const expId = Number($("organic_experiment_id").value);
      if (!expId) throw new Error("Selecciona un experimento organico.");

      const body = {
        experiment_id: expId,
        session_id: $("organic_session_id").value.trim(),
        record_name: $("organic_record_name").value.trim() || null,
        public_id: asIntOrNull($("organic_publico").value),
        clicks: asIntOrNull($("organic_clicks").value),
        views: asIntOrNull($("organic_views").value),
        views_profile: asIntOrNull($("organic_views_profile").value),
        live_new_followers: asIntOrNull($("organic_new_followers").value),
        inicia_test: asIntOrNull($("organic_inicia_test").value),
        initiate_checkouts: asIntOrNull($("organic_initiate_checkouts").value),
        view_content: asIntOrNull($("organic_view_content").value),
        lead_form: asIntOrNull($("organic_lead_form").value),
        purchase: asIntOrNull($("organic_purchase").value),
        organic_piece_type: $("organic_piece_type").value.trim() || null,
        likes: asIntOrNull($("organic_likes").value),
        comments: asIntOrNull($("organic_comments").value),
        shares: asIntOrNull($("organic_shares").value),
        saves: asIntOrNull($("organic_saves").value),
        video_url: $("organic_video_url").value.trim() || null,
        views_finish_pct: asFloatOrNull($("organic_views_finish_pct").value),
        retention_pct: asFloatOrNull($("organic_retention_pct").value),
        avg_watch_time: asFloatOrNull($("organic_avg_watch_time").value),
        video_duration: asFloatOrNull($("organic_video_duration").value),
        execution_type: "organic_video",
        contexto_record: $("organic_contexto_record").value.trim() || null,
        hook_text: $("organic_hook_text").value.trim() || null,
        hook_type: $("organic_hook_type").value || null,
        cta_text: $("organic_cta_text").value.trim() || null,
        cta_type: $("organic_cta_type").value || null,
        creative_id: $("organic_creative_id").value.trim() || null,
      };
      if (!body.session_id) throw new Error("session_id es obligatorio.");

      await apiPost("/records/", body);

      ["organic_session_id","organic_record_name","organic_publico","organic_clicks","organic_views","organic_views_profile",
       "organic_new_followers","organic_inicia_test","organic_initiate_checkouts","organic_view_content","organic_lead_form",
       "organic_purchase","organic_piece_type",
       "organic_likes","organic_comments","organic_shares","organic_saves",
       "organic_video_url","organic_views_finish_pct","organic_retention_pct",
       "organic_avg_watch_time","organic_video_duration",
       "organic_hook_text","organic_cta_text","organic_creative_id","organic_contexto_record"
      ].forEach(id => $(id).value = "");
      $("organic_hook_type").value = "";
      $("organic_cta_type").value = "";

      showToast("Record organico creado", "success");
    } catch(e){
      setStatus("error", true);
      showToast(String(e), 'error');
    }
  };

  // Create live record
  $("btnCreateLiveRecord").onclick = async () => {
    try {
      const expId = Number($("live_experiment_id").value);
      if (!expId) throw new Error("Selecciona un experimento live.");

      const body = {
        experiment_id: expId,
        session_id: $("live_session_id").value.trim(),
        record_name: $("live_record_name").value.trim() || null,
        public_id: asIntOrNull($("live_publico").value),
        clicks: asIntOrNull($("live_clicks").value),
        views: asIntOrNull($("live_views").value),
        views_profile: asIntOrNull($("live_views_profile").value),
        inicia_test: asIntOrNull($("live_inicia_test").value),
        live_viewers_peak: asIntOrNull($("live_viewers_peak").value),
        live_avg_viewers: asIntOrNull($("live_avg_viewers").value),
        live_duration: asFloatOrNull($("live_duration").value),
        live_new_followers: asIntOrNull($("live_new_followers").value),
        likes: asIntOrNull($("live_likes").value),
        comments: asIntOrNull($("live_comments").value),
        shares: asIntOrNull($("live_shares").value),
        saves: asIntOrNull($("live_saves").value),
        organic_piece_type: null,
        execution_type: "live_session",
        contexto_record: $("live_contexto_record").value.trim() || null,
        hook_text: $("live_hook_text").value.trim() || null,
        hook_type: $("live_hook_type").value || null,
        cta_text: $("live_cta_text").value.trim() || null,
        cta_type: $("live_cta_type").value || null,
        creative_id: $("live_creative_id").value.trim() || null,
      };

      if (!body.session_id) throw new Error("session_id es obligatorio.");

      await apiPost("/records/", body);

      ["live_session_id","live_record_name","live_publico","live_clicks","live_views","live_views_profile",
       "live_inicia_test","live_viewers_peak","live_avg_viewers","live_duration","live_new_followers",
       "live_likes","live_comments","live_shares","live_saves",
       "live_hook_text","live_cta_text","live_creative_id","live_contexto_record"
      ].forEach(id => $(id).value = "");
      $("live_hook_type").value = "";
      $("live_cta_type").value = "";

      showToast("Record live creado", "success");
    } catch(e){
      setStatus("error", true);
      showToast(String(e), 'error');
    }
  };

  // Create paid record
  $("btnCreatePaidRecord").onclick = async () => {
    try {
      const expId = Number($("paid_experiment_id").value);
      if (!expId) throw new Error("Selecciona un experimento paid.");

      const body = {
        experiment_id: expId,
        session_id: $("paid_session_id").value.trim(),
        record_name: $("paid_record_name").value.trim() || null,
        public_id: asIntOrNull($("paid_publico").value),
        clicks: asIntOrNull($("paid_clicks").value),
        views: asIntOrNull($("paid_views").value),
        views_profile: asIntOrNull($("paid_views_profile").value),
        live_new_followers: asIntOrNull($("paid_new_followers").value),
        inicia_test: asIntOrNull($("paid_inicia_test").value),
        initiate_checkouts: asIntOrNull($("paid_initiate_checkouts").value),
        view_content: asIntOrNull($("paid_view_content").value),
        lead_form: asIntOrNull($("paid_lead").value),
        purchase: asIntOrNull($("paid_purchase").value),
        cpc: asFloatOrNull($("paid_cpc").value),
        ctr: asFloatOrNull($("paid_ctr").value),
        paid_video_duration: asFloatOrNull($("paid_video_duration").value),
        campaign_id: $("paid_campaign_id").value.trim() || null,
        ad_set_id: $("paid_ad_set_id").value.trim() || null,
        ad_id: $("paid_ad_id").value.trim() || null,
        organic_piece_type: null,
        execution_type: "paid_ad",
        contexto_record: $("paid_contexto_record").value.trim() || null,
        hook_text: $("paid_hook_text").value.trim() || null,
        hook_type: $("paid_hook_type").value || null,
        cta_text: $("paid_cta_text").value.trim() || null,
        cta_type: $("paid_cta_type").value || null,
        creative_id: $("paid_creative_id").value.trim() || null,
      };

      if (!body.session_id) throw new Error("session_id es obligatorio.");

      await apiPost("/records/", body);

      ["paid_session_id","paid_record_name","paid_publico","paid_clicks","paid_views","paid_views_profile",
       "paid_new_followers","paid_inicia_test","paid_initiate_checkouts","paid_view_content","paid_lead","paid_purchase",
       "paid_cpc","paid_ctr",
       "paid_video_duration","paid_campaign_id","paid_ad_set_id","paid_ad_id",
       "paid_hook_text","paid_cta_text","paid_creative_id","paid_contexto_record"
      ].forEach(id => $(id).value = "");
      $("paid_hook_type").value = "";
      $("paid_cta_type").value = "";

      showToast("Record paid creado", "success");
    } catch(e){
      setStatus("error", true);
      showToast(String(e), 'error');
    }
  };

  // ==================== UPDATE RECORD ====================

  async function refreshRecordList() {
    const recordSelect = $("upd_record_id");
    recordSelect.innerHTML = '<option value="">-- seleccionar --</option>';
    const channel = $("upd_channel_filter").value;
    const project = $("upd_project_filter").value;
    const metricX = $("upd_metric_x_filter").value;
    const filteredExps = experimentsCache.filter(e => {
      if (channel && e.traffic_type !== channel) return false;
      if (project && e.project_name !== project) return false;
      if (metricX && e.independent_variable !== metricX) return false;
      return true;
    });
    if (!filteredExps.length) return;
    const recordsByExp = await Promise.all(
      filteredExps.map(exp => apiGet(`/records/?experiment_id=${exp.id}&limit=5000`))
    );
    const records = recordsByExp.flat().sort((a, b) => String(b.created_at).localeCompare(String(a.created_at)));
    for (const rec of records) {
      const opt = document.createElement("option");
      opt.value = String(rec.id);
      const statusTag = rec.record_status ? ` [${rec.record_status}]` : "";
      const name = rec.record_name || rec.session_id;
      opt.textContent = `${rec.id} — ${name}${statusTag}`;
      recordSelect.appendChild(opt);
    }
  }

  $("upd_project_filter").onchange = () => {
    updateUpdateRecordFilters();
    refreshRecordList().catch(e => { setStatus("error", true); showToast(String(e), 'error'); });
  };
  $("upd_channel_filter").onchange = () => {
    updateUpdateRecordFilters();
    refreshRecordList().catch(e => { setStatus("error", true); showToast(String(e), 'error'); });
  };
  $("upd_metric_x_filter").onchange = () => {
    refreshRecordList().catch(e => { setStatus("error", true); showToast(String(e), 'error'); });
  };

  $("upd_record_id").onchange = () => {
    if ($("upd_record_id").value) {
      $("btnLoadRecord").click();
    }
  };

  $("btnLoadRecord").onclick = async () => {
    try {
      const rid = Number($("upd_record_id").value);
      if (!rid) throw new Error("Ingresa un Record ID.");
      const rec = await apiGet(`/records/${rid}`);

      $("updRecordInfo").style.display = "block";
      $("updRecordInfo").classList.remove("hidden");
      $("updFields").style.display = "block";
      $("updFields").classList.remove("hidden");
      const statusClass = rec.record_status === "closed" ? "color:#991b1b;" : "color:#065f46;";
      $("updRecordMeta").innerHTML =
        `<strong>Record #${rec.id}</strong> | Session: ${rec.session_id} | ` +
        (rec.record_name ? `Nombre: "${rec.record_name}" | ` : "") +
        `Status: <span style="${statusClass}font-weight:600;">${rec.record_status}</span> | ` +
        `Experiment: ${rec.experiment_id} | ` +
        (rec.hook_text ? `Hook: "${rec.hook_text}" | ` : "") +
        (rec.cta_text ? `CTA: "${rec.cta_text}" | ` : "") +
        `Created: ${rec.created_at}` +
        (rec.updated_at ? ` | Updated: ${rec.updated_at}` : "");

      // Fill fields with current values
      const fields = [
        "record_name","clicks","views","views_profile","inicia_test","initiate_checkouts",
        "view_content","lead_form","purchase",
        "likes","comments","shares","saves",
        "live_viewers_peak","live_avg_viewers","live_duration","live_new_followers",
        "ctr","cpc","views_finish_pct","retention_pct","avg_watch_time","video_duration"
      ];
      for (const f of fields) {
        const el = $("upd_" + f);
        if (el) el.value = rec[f] !== null && rec[f] !== undefined ? rec[f] : "";
      }
      const matchedPublic = publicsCache.find(p => p.name === rec.publico);
      $("upd_publico").value = rec.public_id
        ? String(rec.public_id)
        : (matchedPublic ? String(matchedPublic.id) : "");

      setStatus("record cargado");
    } catch(e) {
      setStatus("error", true);
      showToast(String(e), 'error');
    }
  };

  $("btnUpdateRecord").onclick = async () => {
    try {
      const rid = Number($("upd_record_id").value);
      if (!rid) throw new Error("Ingresa un Record ID.");

      const body = {};
      const fields = [
        ["record_name", (v) => v.trim() || null],
        ["clicks", asIntOrNull], ["views", asIntOrNull],
        ["views_profile", asIntOrNull], ["inicia_test", asIntOrNull],
        ["initiate_checkouts", asIntOrNull], ["view_content", asIntOrNull],
        ["lead_form", asIntOrNull], ["purchase", asIntOrNull],
        ["likes", asIntOrNull], ["comments", asIntOrNull],
        ["shares", asIntOrNull], ["saves", asIntOrNull],
        ["live_viewers_peak", asIntOrNull], ["live_avg_viewers", asIntOrNull],
        ["live_duration", asFloatOrNull], ["live_new_followers", asIntOrNull],
        ["ctr", asFloatOrNull], ["cpc", asFloatOrNull],
        ["views_finish_pct", asFloatOrNull], ["retention_pct", asFloatOrNull],
        ["avg_watch_time", asFloatOrNull], ["video_duration", asFloatOrNull],
      ];

      for (const [f, conv] of fields) {
        const v = $("upd_" + f).value;
        if (v !== "" && v !== null && v !== undefined) {
          body[f] = conv(v);
        }
      }
      body.public_id = asIntOrNull($("upd_publico").value);

      await apiPatch(`/records/${rid}`, body);
      showToast("Record actualizado", "success");

      // Reload the record to show updated info
      $("btnLoadRecord").click();
    } catch(e) {
      setStatus("error", true);
      showToast(String(e), 'error');
    }
  };

  $("btnCloseRecord").onclick = async () => {
    try {
      const rid = Number($("upd_record_id").value);
      if (!rid) throw new Error("Ingresa un Record ID.");
      await apiPost(`/records/${rid}/close`, {});
      showToast("Record cerrado", "success");
      $("btnLoadRecord").click();
    } catch(e) {
      setStatus("error", true);
      showToast(String(e), 'error');
    }
  };

  $("btnReopenRecord").onclick = async () => {
    try {
      const rid = Number($("upd_record_id").value);
      if (!rid) throw new Error("Ingresa un Record ID.");
      await apiPost(`/records/${rid}/reopen`, {});
      showToast("Record reabierto", "success");
      $("btnLoadRecord").click();
    } catch(e) {
      setStatus("error", true);
      showToast(String(e), 'error');
    }
  };

  $("project_mode").addEventListener("change", updateProjectModeVisibility);
  $("live_project_filter").addEventListener("change", () => updateRecordFormFilters({ prefix: "live", trafficType: "live", sessionPrefix: "l" }));
  $("organic_project_filter").addEventListener("change", () => updateRecordFormFilters({ prefix: "organic", trafficType: "organic", sessionPrefix: "s" }));
  $("paid_project_filter").addEventListener("change", () => updateRecordFormFilters({ prefix: "paid", trafficType: "paid", sessionPrefix: "p" }));
  $("live_metric_x_filter").addEventListener("change", () => updateRecordFormFilters({ prefix: "live", trafficType: "live", sessionPrefix: "l" }));
  $("organic_metric_x_filter").addEventListener("change", () => updateRecordFormFilters({ prefix: "organic", trafficType: "organic", sessionPrefix: "s" }));
  $("paid_metric_x_filter").addEventListener("change", () => updateRecordFormFilters({ prefix: "paid", trafficType: "paid", sessionPrefix: "p" }));
  $("btnOpenEditModal").addEventListener("click", openEditModal);
  $("btnCloseEditModal").addEventListener("click", closeEditModal);
  editModal.addEventListener("click", (event) => {
    if (event.target === editModal) closeEditModal();
  });

  // init
  refreshAll().catch(e => { setStatus("error", true); showToast(String(e), 'error'); });
