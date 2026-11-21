const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

let catalog = null;
let currentResult = null;
let toastTimer = null;

const fields = {
  detencion: [
    { key: "v0", label: "Velocidad inicial", unit: "m/s", min: 0.01, max: 50, step: 0.1, digits: 2 },
    { key: "tr", label: "Tiempo de reacción", unit: "s", min: 0, max: 30, step: 0.1, digits: 2 },
    { key: "a", label: "Desaceleración constante", unit: "m/s²", min: 0.0001, max: 20, scale: "log", digits: 4 },
    { key: "distance_limit", label: "Umbral de comparación didáctico", unit: "m", min: 0.01, max: 100000, scale: "log", digits: 3 },
    { key: "h", label: "Paso temporal", unit: "s", min: 0.01, max: 10, scale: "log", digits: 4 },
  ],
  deterioro: [
    { key: "d0", label: "Indicador inicial D₀", unit: "u.", min: 0, max: 0.99, step: 0.01, digits: 3 },
    { key: "alpha", label: "Coeficiente lineal α", unit: "u./año", min: 0.000001, max: 2, scale: "log", digits: 6 },
    { key: "beta", label: "Coeficiente cuadrático β", unit: "u./año²", min: 0, max: 1, minPositive: 0.00000001, scale: "log-zero", digits: 7 },
    { key: "threshold", label: "Umbral del indicador", unit: "u.", min: 0.001, max: 10, scale: "log", digits: 4 },
    { key: "tol", label: "Tolerancia numérica", unit: "", min: 1e-10, max: 0.01, scale: "log", digits: 2 },
  ],
  oscilaciones: [
    { key: "mass", label: "Masa equivalente", unit: "kg", min: 0.05, max: 50000, scale: "log", digits: 3 },
    { key: "damping", label: "Amortiguamiento", unit: "N·s/m", min: 0, max: 500000, minPositive: 0.01, scale: "log-zero", digits: 3 },
    { key: "stiffness", label: "Rigidez", unit: "N/m", min: 0.05, max: 1000000, scale: "log", digits: 3 },
    { key: "force", label: "Amplitud de fuerza", unit: "N", min: 0, max: 5000, minPositive: 0.01, scale: "log-zero", digits: 3 },
    { key: "frequency", label: "Frecuencia angular externa", unit: "rad/s", min: 0.01, max: 20, step: 0.0001, digits: 4 },
    { key: "x0", label: "Desplazamiento inicial", unit: "m", min: -10, max: 10, step: 0.01, digits: 3 },
    { key: "v0", label: "Velocidad inicial", unit: "m/s", min: -10, max: 10, step: 0.01, digits: 3 },
    { key: "duration", label: "Duración simulada", unit: "s", min: 0.01, max: 60, step: 0.1, digits: 2 },
    { key: "h", label: "Paso temporal", unit: "s", min: 0.002, max: 0.5, scale: "log", digits: 4 },
  ],
  sensores: [
    { key: "nodes", label: "Nodos de entrenamiento", unit: "puntos", min: 4, max: 24, step: 1, digits: 0 },
    { key: "noise", label: "Amplitud máxima del ruido", unit: "mm", min: 0, max: 0.5, minPositive: 1e-12, scale: "log-zero", digits: 8 },
  ],
};

const scenarioNames = {
  normal: "Normal",
  estres: "Estrés",
  mal_condicionado: "Mal condicionado",
};

async function api(path, options = {}) {
  let response;
  try {
    response = await fetch(path, {
      headers: { "Content-Type": "application/json", ...(options.headers || {}) },
      ...options,
    });
  } catch {
    throw Error("No se pudo conectar con la aplicación local.");
  }

  let data;
  try {
    data = await response.json();
  } catch {
    data = { error: "Respuesta no válida del servidor." };
  }
  if (!response.ok) throw Error(data.error || "Error del servidor");
  return data;
}

function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  })[character]);
}

function fmt(value, digits = 5) {
  if (value === null || value === undefined || !Number.isFinite(Number(value))) return "—";
  const number = Number(value);
  if (Math.abs(number) > 0 && (Math.abs(number) >= 1e5 || Math.abs(number) < 1e-4)) {
    return number.toExponential(3);
  }
  return number.toLocaleString("es-BO", { maximumFractionDigits: digits });
}

function fmtLimit(value, digits = 5) {
  if (value === null || value === undefined || !Number.isFinite(Number(value))) return "—";
  return Number(value).toLocaleString("es-BO", { maximumFractionDigits: digits });
}

const sliderResolution = 1000;

function positionForValue(field, value) {
  if (field.scale === "log") {
    const bounded = Math.min(field.max, Math.max(field.min, Number(value)));
    const fraction = (Math.log(bounded) - Math.log(field.min)) / (Math.log(field.max) - Math.log(field.min));
    return Math.round(fraction * sliderResolution);
  }
  if (field.scale === "log-zero") {
    if (Number(value) <= 0) return 0;
    const positiveMinimum = field.minPositive;
    const bounded = Math.min(field.max, Math.max(positiveMinimum, Number(value)));
    const fraction = (Math.log(bounded) - Math.log(positiveMinimum)) / (Math.log(field.max) - Math.log(positiveMinimum));
    return 1 + Math.round(fraction * (sliderResolution - 1));
  }
  return Number(value);
}

function valueForPosition(field, position) {
  if (field.scale === "log") {
    const fraction = Number(position) / sliderResolution;
    return Math.exp(Math.log(field.min) + fraction * (Math.log(field.max) - Math.log(field.min)));
  }
  if (field.scale === "log-zero") {
    if (Number(position) <= 0) return 0;
    const fraction = (Number(position) - 1) / (sliderResolution - 1);
    return Math.exp(Math.log(field.minPositive) + fraction * (Math.log(field.max) - Math.log(field.minPositive)));
  }
  return Number(position);
}

function validateParameterSet(code, parameters) {
  const errors = {};
  const mark = (key, message) => { if (!errors[key]) errors[key] = message; };

  for (const field of fields[code]) {
    const value = Number(parameters[field.key]);
    if (!Number.isFinite(value) || value < field.min || value > field.max) {
      mark(field.key, `Usa un valor entre ${fmt(field.min, field.digits)} y ${fmt(field.max, field.digits)} ${field.unit || ""}.`.trim());
    }
  }

  if (code === "detencion") {
    const v0 = Number(parameters.v0);
    const reaction = Number(parameters.tr);
    const deceleration = Number(parameters.a);
    const step = Number(parameters.h);
    if (v0 <= 0) mark("v0", "La velocidad inicial debe ser mayor que cero.");
    if (deceleration <= 0) mark("a", "La desaceleración debe ser mayor que cero.");
    if (step > 0 && deceleration > 0) {
      const constantIntervals = Math.max(2, Math.ceil((v0 / deceleration) / step));
      const gamma = 0.05;
      const variableTime = 2 * v0 / (deceleration + Math.sqrt(deceleration ** 2 + 2 * deceleration * gamma * v0));
      const variableIntervals = Math.max(2, Math.ceil(variableTime / step));
      if (constantIntervals > 2000 || variableIntervals > 2000) {
        mark("h", "Este paso crea más de 2000 intervalos; aumenta el paso temporal.");
      }
    }
    if (reaction < 0) mark("tr", "El tiempo de reacción no puede ser negativo.");
    if (Number(parameters.distance_limit) <= 0) mark("distance_limit", "El umbral debe ser mayor que cero.");
  }

  if (code === "deterioro") {
    if (Number(parameters.d0) >= Number(parameters.threshold)) {
      mark("threshold", "El umbral debe ser mayor que el indicador inicial D₀.");
    }
    if (Number(parameters.alpha) <= 0) mark("alpha", "El coeficiente lineal debe ser positivo.");
  }

  if (code === "oscilaciones") {
    const mass = Number(parameters.mass);
    const damping = Number(parameters.damping);
    const stiffness = Number(parameters.stiffness);
    const duration = Number(parameters.duration);
    const step = Number(parameters.h);
    if (mass <= 0) mark("mass", "La masa debe ser mayor que cero.");
    if (stiffness <= 0) mark("stiffness", "La rigidez debe ser mayor que cero.");
    if (duration > 0 && step > 0 && mass > 0 && stiffness > 0) {
      const intervals = Math.max(2, Math.ceil(duration / step));
      const effectiveStep = duration / intervals;
      if (intervals > 2000) {
        mark("h", "Este paso crea más de 2000 intervalos; aumenta el paso temporal.");
      } else if (effectiveStep * Math.max(Math.sqrt(stiffness / mass), damping / mass) > 2.5) {
        mark("h", "Este paso puede ser inestable para estos parámetros; aumenta h o ajusta masa, rigidez o amortiguamiento.");
      }
    }
  }

  if (code === "sensores") {
    const nodes = Number(parameters.nodes);
    if (!Number.isInteger(nodes)) mark("nodes", "La cantidad de nodos debe ser un número entero.");
  }
  return errors;
}

function validateManualPoints(raw) {
  const rows = String(raw || "").replaceAll(";", "\n").split(/\r?\n/).map((row) => row.trim()).filter(Boolean);
  if (rows.length === 0) return null;
  const points = [];
  const decimalNumber = /^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$/;
  for (const row of rows) {
    const columns = row.split(",").map((column) => column.trim());
    if (columns.length !== 2) return "Cada fila debe tener dos valores: tiempo, lectura.";
    if (columns.some((column) => column === "")) return "Completa ambos valores de cada fila.";
    if (!decimalNumber.test(columns[0]) || !decimalNumber.test(columns[1])) {
      if (points.length === 0 && ["x", "t", "tiempo", "tiempo_s"].includes(columns[0].toLowerCase())) continue;
      return "Usa números finitos con punto decimal.";
    }
    const time = Number(columns[0]);
    const reading = Number(columns[1]);
    if (!Number.isFinite(time) || !Number.isFinite(reading)) {
      if (points.length === 0 && ["x", "t", "tiempo", "tiempo_s"].includes(columns[0].toLowerCase())) continue;
      return "Usa números finitos con punto decimal.";
    }
    points.push([time, reading]);
  }
  if (points.length === 0) return "Agrega al menos 4 muestras numéricas.";
  if (points.length < 4 || points.length > 40) return "Se requieren entre 4 y 40 muestras.";
  if (new Set(points.map(([time]) => time)).size !== points.length) return "Los tiempos deben ser distintos.";
  return null;
}

function toast(message, isError = false) {
  const element = $("#toast");
  element.textContent = message;
  element.className = `show${isError ? " error" : ""}`;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => (element.className = ""), 3800);
}

function navigate(hash) {
  location.hash = hash;
}

function setTitle(title) {
  $("#page-title").textContent = title;
  $$('[data-nav]').forEach((link) => {
    const active = link.dataset.nav === location.hash.replace(/^#/, "")
      || (location.hash === "" && link.dataset.nav === "inicio");
    link.classList.toggle("active", active);
  });
}

function dashboard() {
  $("#view").removeAttribute("data-module");
  setTitle("Panel general");
  $("#view").innerHTML = `
    <section class="hero">
      <div class="hero-landscape" aria-hidden="true"><span class="hero-cabin"></span></div>
      <div class="hero-kicker">LABORATORIO DE MÉTODOS NUMÉRICOS</div>
      <h2>Un recorrido por los métodos que mueven el sistema.</h2>
      <p>Configura escenarios sintéticos, ejecuta métodos numéricos, compara errores y recupera tus experimentos.</p>
      <div class="hero-note">ⓘ Inspirado en Mi Teleférico · La Paz, Bolivia · Sin telemetría real</div>
    </section>
    <div class="section-head">
      <div><h2>Módulos del simulador</h2><p>Elige un caso para definir parámetros y ejecutar sus métodos.</p></div>
      <a class="card-link" href="#historial">Ver historial ↗</a>
    </div>
    <div id="case-grid" class="grid"></div>
    `;

  $("#case-grid").innerHTML = catalog.cases.map((item) => `
    <article class="module-card module-${item.code}">
      <div class="module-icon">${esc(item.label)}</div>
      <div>
        <h3>${esc(item.name)}</h3>
        <p>${esc(item.question)}</p>
        <div class="tags">${item.methods.slice(0, 3).map((method) => `<span class="tag">${esc(method)}</span>`).join("")}</div>
        <a class="card-link" href="#caso/${item.code}">Abrir módulo <span aria-hidden="true">→</span></a>
      </div>
    </article>`).join("");
}

function renderRoute() {
  const hash = location.hash.replace(/^#/, "");
  if (hash.startsWith("caso/")) return renderCase(hash.split("/")[1]);
  if (hash === "historial") return renderHistory();
  if (hash === "comparacion") return renderComparison();
  if (hash.startsWith("resultado/")) return renderHistory(Number(hash.split("/")[1]));
  dashboard();
}

function renderCase(code) {
  const item = catalog.cases.find((candidate) => candidate.code === code);
  if (!item) return dashboard();

  $("#view").dataset.module = code;
  setTitle(`${item.label} · ${item.name}`);
  const scenarios = catalog.scenarios;
  $("#view").innerHTML = `
    <div class="case-head"><span class="case-code">${esc(item.label)}</span><div><h2>${esc(item.name)}</h2><p>${esc(item.question)}</p></div></div>
    <div class="panel">
      <h3>Escenario y entradas</h3>
      <p class="panel-sub">Los escenarios se mantienen separados. Cada uno carga sus propios valores iniciales y puedes editarlos antes de ejecutar.</p>
      <form id="run-form">
        <div class="toolbar">
          <div class="field"><label for="scenario">Escenario experimental</label><select id="scenario" name="scenario">${scenarios.map((scenario) => `<option value="${scenario.code}">${esc(scenario.name)}</option>`).join("")}</select></div>
          <div class="scenario-row">${scenarios.map((scenario) => `<span class="scenario-chip${scenario.code === "normal" ? " active" : ""}" data-scenario-chip="${scenario.code}">${esc(scenario.name)}</span>`).join("")}</div>
        </div>
        <p class="panel-sub" id="scenario-description"></p>
        <div class="input-grid" id="field-grid"></div>
        <div class="form-validation" id="form-validation" role="status" aria-live="polite"></div>
        <div class="actions" style="margin-top:17px"><button class="btn" id="run-button" type="submit">▶ Ejecutar simulación</button><button class="btn secondary" type="reset" id="reset-button">Restablecer escenario</button></div>
      </form>
    </div>
    <div class="panel">
      <h3>Métodos incluidos</h3>
      <div class="method-list">${item.methods.map((method) => `<span class="method-pill">${esc(method)}</span>`).join("")}</div>
      <p class="small-note" style="margin-bottom:0">La teoría de errores se aplica de forma transversal. Cuando la referencia es cero, el error relativo se muestra como no definido.</p>
    </div>
    <div id="result-area"></div>`;

  const form = $("#run-form");
  const scenarioSelect = $("#scenario");

  function readParameters() {
    return Object.fromEntries(fields[code].map((field) => [field.key, Number(form.elements[field.key].value)]));
  }

  function updateValidation() {
    const parameters = readParameters();
    const errors = validateParameterSet(code, parameters);
    let manualError = null;

    fields[code].forEach((field) => {
      const status = $(`#status-${field.key}`);
      const error = errors[field.key];
      status.classList.toggle("invalid", Boolean(error));
      status.classList.toggle("valid", !error);
      $(".validation-icon", status).textContent = error ? "!" : "✓";
      $(".validation-text", status).textContent = error ? `No válido: ${error}` : "Válido para este cálculo";
    });

    if (code === "sensores") {
      manualError = validateManualPoints($("#manual-points")?.value || "");
      const manualStatus = $("#manual-points-status");
      if (manualStatus) {
        const hasManualPoints = Boolean($("#manual-points").value.trim());
        manualStatus.classList.toggle("invalid", Boolean(manualError));
        manualStatus.classList.toggle("valid", !manualError);
        $(".validation-icon", manualStatus).textContent = manualError ? "!" : "✓";
        $(".validation-text", manualStatus).textContent = manualError
          ? `No válido: ${manualError}`
          : hasManualPoints ? "Muestras válidas" : "Sin muestras manuales: se usarán los valores preconfigurados";
      }
    }

    const invalidCount = Object.keys(errors).length + (manualError ? 1 : 0);
    const summary = $("#form-validation");
    summary.classList.toggle("invalid", invalidCount > 0);
    summary.classList.toggle("valid", invalidCount === 0);
    summary.textContent = invalidCount > 0
      ? `Hay ${invalidCount} dato(s) por corregir antes de ejecutar.`
      : "Todos los parámetros están válidos para este cálculo.";

    const button = $("#run-button");
    button.dataset.invalid = invalidCount > 0 ? "true" : "false";
    button.disabled = invalidCount > 0 || button.dataset.running === "true";
    return invalidCount === 0;
  }

  function fillFields(scenarioCode) {
    const preset = item.presets[scenarioCode];
    const previousManualPoints = code === "sensores" ? $("#manual-points")?.value || "" : "";
    $("#field-grid").innerHTML = fields[code].map((field) => {
      const value = preset[field.key];
      const isLogarithmic = field.scale === "log" || field.scale === "log-zero";
      const sliderMinimum = isLogarithmic ? 0 : field.min;
      const sliderMaximum = isLogarithmic ? sliderResolution : field.max;
      const sliderStep = isLogarithmic ? 1 : field.step;
      const sliderPosition = positionForValue(field, value);
      const label = field.unit ? `${field.label} (${field.unit})` : field.label;
      return `
        <div class="field slider-field">
          <label for="f-${field.key}">${esc(label)}</label>
          <div class="parameter-readout"><output id="value-${field.key}">${fmt(value, field.digits)}</output></div>
          <input class="parameter-slider" id="f-${field.key}" type="range" min="${sliderMinimum}" max="${sliderMaximum}" step="${sliderStep}" value="${sliderPosition}" data-range-key="${field.key}" aria-describedby="status-${field.key}">
          <div class="slider-limits"><span>${fmtLimit(field.min, field.digits)}</span><span>${fmtLimit(field.max, field.digits)}</span></div>
          <input type="hidden" name="${field.key}" value="${value}">
          <div class="validation-status valid" id="status-${field.key}" role="status" aria-live="polite"><span class="validation-icon">✓</span><span class="validation-text">Válido para este cálculo</span></div>
        </div>`;
    }).join("");
    const description = scenarios.find((scenario) => scenario.code === scenarioCode)?.description || "";
    $("#scenario-description").textContent = description;
    $$('[data-scenario-chip]').forEach((chip) => {
      chip.classList.toggle("active", chip.dataset.scenarioChip === scenarioCode);
    });

    if (code === "sensores") {
      $("#field-grid").insertAdjacentHTML("beforeend", `
        <div class="field full-field">
          <label for="manual-points">Opcional · pegar muestras propias</label>
          <textarea id="manual-points" rows="5" placeholder="tiempo_s,lectura_mm&#10;0,0.0&#10;1,1.0&#10;2,0.0"></textarea>
          <div class="unit">Cada fila usa tiempo en segundos y lectura en milímetros. Deja vacío para usar el conjunto de referencia. Entre 4 y 40 filas.</div>
          <div class="validation-status valid" id="manual-points-status" role="status" aria-live="polite"><span class="validation-icon">✓</span><span class="validation-text">Sin muestras manuales: se usarán los valores preconfigurados</span></div>
          <label class="file-pick">O carga un CSV de dos columnas<input id="points-file" type="file" accept=".csv,text/csv"></label>
        </div>`);
      $("#manual-points").value = previousManualPoints;
    }
    updateValidation();
  }

  fillFields("normal");
  scenarioSelect.addEventListener("change", () => fillFields(scenarioSelect.value));
  form.addEventListener("input", (event) => {
    if (event.target.matches("[data-range-key]")) {
      const field = fields[code].find((candidate) => candidate.key === event.target.dataset.rangeKey);
      const value = valueForPosition(field, event.target.value);
      form.elements[field.key].value = String(value);
      $(`#value-${field.key}`).textContent = fmt(value, field.digits);
    }
    if (event.target.matches("[data-range-key]") || event.target.id === "manual-points") updateValidation();
  });
  $("#reset-button").addEventListener("click", (event) => {
    event.preventDefault();
    scenarioSelect.value = "normal";
    fillFields("normal");
    if (code === "sensores") $("#manual-points").value = "";
    updateValidation();
  });

  if (code === "sensores") {
    form.addEventListener("change", async (event) => {
      if (event.target.id !== "points-file") return;
      const file = event.target.files[0];
      if (file) {
        $("#manual-points").value = await file.text();
        updateValidation();
      }
    });
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!updateValidation()) return;
    const parameters = readParameters();
    if (code === "sensores") parameters.data_points = $("#manual-points").value;
    await execute({ case: code, scenario: scenarioSelect.value, parameters }, false);
  });
}

async function execute(request, isRerun) {
  const button = $("#run-button");
  if (button) {
    button.dataset.running = "true";
    button.disabled = true;
    button.innerHTML = '<span class="spinner"></span>Calculando…';
  }
  try {
    const result = await api(isRerun ? "/api/rerun" : "/api/execute", {
      method: "POST",
      body: JSON.stringify(request),
    });
    currentResult = result;
    displayResult(result);
    toast(`Simulación #${result.simulation_id} guardada en el historial.`);
  } catch (error) {
    toast(error.message, true);
  } finally {
    if (button) {
      button.dataset.running = "false";
      button.disabled = button.dataset.invalid === "true";
      button.textContent = "▶ Ejecutar simulación";
    }
  }
}

function displayResult(result, container = $("#result-area")) {
  if (!container) return;
  const methods = result.methods || [];
  container.innerHTML = `
    <div class="section-head"><div><h2>Resultados de la simulación #${result.simulation_id || "—"}</h2><p>${esc(scenarioNames[result.scenario] || result.scenario)} · ${esc(result.case_title)}</p></div><div class="actions"><button class="btn secondary" id="csv-button">Descargar tablas CSV</button><button class="btn ghost" onclick="window.print()">Imprimir</button></div></div>
    <div class="metric-grid">${(result.highlights || methods.slice(0, 4).map((method) => ({ label: `${method.name} · valor resumen`, value: method.summary_value, unit: method.unit }))).map((metric) => `<div class="metric-card"><span>${esc(metric.label)}</span><strong>${fmt(metric.value)}</strong><small>${esc(metric.unit || "")}</small></div>`).join("")}</div>
    <div class="results-layout">${(result.charts || []).map((chart, index) => `<div class="chart-card"><h3>${esc(chart.title)}</h3><canvas id="chart-${index}" aria-label="${esc(chart.title)}"></canvas></div>`).join("")}</div>
    <div class="panel" style="margin-top:15px"><h3>Comparación de métodos</h3><div class="table-wrap"><table><thead><tr><th>Método</th><th>Resultado</th><th>Referencia</th><th>Error absoluto</th><th>Error relativo</th><th>Residuo</th><th>Iteraciones / pasos</th><th>Convergencia</th></tr></thead><tbody>${methods.map((method) => `<tr><td class="result-method-name">${esc(method.name)}</td><td>${fmt(method.summary_value)} ${esc(method.unit || "")}</td><td>${fmt(method.reference_value)}</td><td>${fmt(method.error_abs)}</td><td>${method.error_rel == null ? "No definido" : `${fmt(100 * method.error_rel)} %`}</td><td>${fmt(method.residual)}</td><td>${fmt(method.iterations, 0)}</td><td>${method.converged == null ? "—" : `<span class="method-status ${method.converged ? "ok" : "warn"}">${method.converged ? "✓ Convergió" : "! No convergió"}</span>`}</td></tr>`).join("")}</tbody></table></div>${methods.some((method) => method.converged === false) ? `<div class="status-callout"><b>Atención:</b> ${esc(methods.filter((method) => method.converged === false).map((method) => method.name).join(", "))} no alcanzó la tolerancia. Se muestran la última aproximación, el residuo y el máximo de iteraciones; interpreta esos valores como no convergentes.</div>` : ""}</div>
    <div class="panel"><div class="step-tools"><h3 style="margin:0">Detalle de iteraciones y pasos</h3><label for="method-select">Método</label><select id="method-select">${methods.map((method, index) => `<option value="${index}">${esc(method.name)}</option>`).join("")}</select></div><div id="steps-table"></div></div>
    <div class="conclusion-grid"><article class="conclusion"><h4>Conclusión numérica</h4><p>${esc(result.conclusions?.numeric || "")}</p></article><article class="conclusion applied"><h4>Conclusión sobre el caso</h4><p>${esc(result.conclusions?.case || "")}</p></article></div>
    <p class="small-note">Entradas reproducibles, parámetros, tablas y puntos de las gráficas quedaron guardados. Puedes recuperar esta corrida desde Historial.</p>`;

  (result.charts || []).forEach((chart, index) => drawChart($(`#chart-${index}`), chart));
  const selector = $("#method-select");
  if (selector) {
    const showSteps = () => renderSteps(methods[Number(selector.value)]);
    selector.addEventListener("change", showSteps);
    showSteps();
  }
  $("#csv-button")?.addEventListener("click", () => downloadCSV(methods, result.simulation_id));
  container.scrollIntoView({ behavior: "smooth", block: "start" });
}

function renderSteps(method) {
  const element = $("#steps-table");
  if (!element) return;
  const rows = method?.steps || [];
  if (!rows.length) {
    element.innerHTML = '<div class="empty">Este método no generó pasos tabulados.</div>';
    return;
  }
  const keys = [...new Set(rows.flatMap((row) => Object.keys(row)))];
  element.innerHTML = `
    <div class="table-wrap"><table><thead><tr>${keys.map((key) => `<th>${esc(key)}</th>`).join("")}</tr></thead>
    <tbody>${rows.slice(0, 500).map((row) => `<tr>${keys.map((key) => `<td>${typeof row[key] === "object" ? esc(JSON.stringify(row[key])) : fmt(row[key])}</td>`).join("")}</tr>`).join("")}</tbody></table></div>
    ${rows.length > 500 ? '<p class="small-note">Se muestran los primeros 500 pasos; el historial conserva el resultado completo.</p>' : ""}`;
}

function drawChart(canvas, chart) {
  if (!canvas) return;
  const rect = canvas.getBoundingClientRect();
  const pixelRatio = window.devicePixelRatio || 1;
  canvas.width = Math.max(320, rect.width * pixelRatio);
  canvas.height = 250 * pixelRatio;
  const context = canvas.getContext("2d");
  context.scale(pixelRatio, pixelRatio);

  const width = canvas.width / pixelRatio;
  const height = canvas.height / pixelRatio;
  const chartSeries = chart.series || [];
  const legendColumns = Math.min(2, Math.max(1, chartSeries.length));
  const legendRows = Math.max(1, Math.ceil(chartSeries.length / legendColumns));
  const padding = { left: 54, right: 18, top: 19 + legendRows * 13, bottom: 43 };
  const points = (chart.series || []).flatMap((series) => series.data || [])
    .filter((point) => Array.isArray(point) && Number.isFinite(+point[0]) && Number.isFinite(+point[1]));
  if (!points.length) {
    context.fillStyle = "#718297";
    context.fillText("Sin puntos para graficar", 20, 40);
    return;
  }

  let xMinimum = Math.min(...points.map((point) => +point[0]));
  let xMaximum = Math.max(...points.map((point) => +point[0]));
  let yMinimum = Math.min(...points.map((point) => +point[1]));
  let yMaximum = Math.max(...points.map((point) => +point[1]));
  if (xMinimum === xMaximum) xMaximum = xMinimum + 1;
  if (yMinimum === yMaximum) {
    yMinimum -= 1;
    yMaximum += 1;
  }
  const yPadding = (yMaximum - yMinimum) * 0.1;
  yMinimum -= yPadding;
  yMaximum += yPadding;
  const xPixel = (value) => padding.left + (value - xMinimum) / (xMaximum - xMinimum) * (width - padding.left - padding.right);
  const yPixel = (value) => height - padding.bottom - (value - yMinimum) / (yMaximum - yMinimum) * (height - padding.top - padding.bottom);

  context.font = "10px DM Sans,Arial";
  context.strokeStyle = "#e5ebef";
  context.fillStyle = "#738696";
  context.lineWidth = 1;
  for (let index = 0; index <= 4; index += 1) {
    const y = padding.top + (height - padding.top - padding.bottom) * index / 4;
    context.beginPath();
    context.moveTo(padding.left, y);
    context.lineTo(width - padding.right, y);
    context.stroke();
    const value = yMaximum - (yMaximum - yMinimum) * index / 4;
    context.fillText(fmt(value, 3), 5, y + 3);
  }

  context.strokeStyle = "#9babb7";
  context.beginPath();
  context.moveTo(padding.left, padding.top);
  context.lineTo(padding.left, height - padding.bottom);
  context.lineTo(width - padding.right, height - padding.bottom);
  context.stroke();
  context.fillStyle = "#52697a";
  context.fillText(chart.x_label || "x", width / 2 - 15, height - 8);
  context.save();
  context.translate(13, height / 2);
  context.rotate(-Math.PI / 2);
  context.fillText(chart.y_label || "y", 0, 0);
  context.restore();

  const colors = ["#159c84", "#e59546", "#6077c5", "#cb6687", "#417eac", "#9a7ac4"];
  chartSeries.forEach((series, seriesIndex) => {
    const data = series.data || [];
    context.strokeStyle = colors[seriesIndex % colors.length];
    context.fillStyle = colors[seriesIndex % colors.length];
    context.lineWidth = 2;
    context.beginPath();
    data.forEach((point, index) => {
      if (!Number.isFinite(+point[0]) || !Number.isFinite(+point[1])) return;
      if (index === 0) context.moveTo(xPixel(+point[0]), yPixel(+point[1]));
      else context.lineTo(xPixel(+point[0]), yPixel(+point[1]));
    });
    context.stroke();
    if (data.length < 25) {
      data.forEach((point) => {
        context.beginPath();
        context.arc(xPixel(+point[0]), yPixel(+point[1]), 2.3, 0, Math.PI * 2);
        context.fill();
      });
    }
  });

  context.font = "10px DM Sans,Arial";
  const legendWidth = (width - padding.left - padding.right) / legendColumns;
  chartSeries.forEach((series, index) => {
    const legendColumn = index % legendColumns;
    const legendRow = Math.floor(index / legendColumns);
    const legendX = padding.left + legendColumn * legendWidth;
    const legendY = 11 + legendRow * 13;
    context.fillStyle = colors[index % colors.length];
    context.fillRect(legendX, legendY - 3, 8, 3);
    context.fillStyle = "#506778";
    const label = series.name || "";
    context.fillText(label, legendX + 12, legendY, Math.max(20, legendWidth - 16));
  });
}

async function renderComparison() {
  setTitle("Comparación global");
  const history = await api("/api/history");
  const latestByCase = new Map();
  for (const row of history) {
    if (!latestByCase.has(row.case_code)) latestByCase.set(row.case_code, row);
  }
  if (!latestByCase.size) {
    $("#view").innerHTML = '<div class="section-head"><div><h2>Comparación global</h2><p>Resumen de la última corrida guardada en cada módulo.</p></div></div><div class="empty">Todavía no hay resultados para comparar. Ejecuta una simulación en cualquier módulo.</div>';
    return;
  }

  const runs = await Promise.all([...latestByCase.values()].map((row) => api(`/api/history/${row.id}`)));
  $("#view").innerHTML = `
    <div class="section-head"><div><h2>Comparación global</h2><p>Última corrida guardada por módulo. Las magnitudes se interpretan dentro de cada caso y sus unidades.</p></div></div>
    <div class="grid" id="compare-grid"></div>`;
  const moduleLabels = { detencion: "M1", deterioro: "M2", oscilaciones: "M3", sensores: "M4" };
  $("#compare-grid").innerHTML = runs.map((run) => {
    const result = run.result;
    const metrics = (result.highlights || result.methods.slice(0, 2).map((method) => ({
      label: method.name,
      value: method.summary_value,
      unit: method.unit,
    }))).slice(0, 3);
    return `
      <article class="panel">
        <div class="case-head"><span class="case-code">${esc(moduleLabels[run.case_code] || run.case_code)}</span><div><h3>${esc(run.case_name)}</h3><p>${esc(scenarioNames[run.scenario] || run.scenario)} · ${esc(run.created_at)}</p></div></div>
        <div class="tags">${metrics.map((metric) => `<span class="tag">${esc(metric.label)}: <b>${fmt(metric.value)} ${esc(metric.unit || "")}</b></span>`).join("")}</div>
        <a class="card-link" href="#resultado/${run.id}">Abrir resultados →</a>
      </article>`;
  }).join("");
}

async function renderHistory(openId = null) {
  setTitle("Historial de simulaciones");
  const rows = await api("/api/history");
  $("#view").innerHTML = `
    <div class="section-head"><div><h2>Experimentos guardados</h2><p>Abre una corrida para revisar parámetros, tablas, gráficas y conclusiones, o repítela.</p></div>
      <div class="filter"><label for="history-filter">Módulo</label><select id="history-filter"><option value="">Todos</option>${catalog.cases.map((item) => `<option value="${item.code}">${item.label} · ${esc(item.name)}</option>`).join("")}</select></div>
    </div>
    <div class="history-list" id="history-list"></div><div id="opened-result"></div>`;

  const select = $("#history-filter");
  const paint = (list) => {
    $("#history-list").innerHTML = list.length ? list.map((row) => `
      <article class="history-row"><div><h3>#${row.id} · ${esc(row.case_name)}</h3><p>${esc(scenarioNames[row.scenario] || row.scenario)} · ${esc(row.created_at)} · ${esc(row.status)}</p></div>
        <div class="actions history-actions"><button class="btn secondary" data-open="${row.id}">Abrir</button><button class="btn ghost" data-repeat="${row.id}">Repetir</button><button class="btn danger" data-delete="${row.id}">Borrar</button></div>
      </article>`).join("") : '<div class="empty">Aún no hay simulaciones guardadas. Abre un módulo y ejecuta el primer escenario.</div>';
    $$('[data-open]').forEach((button) => {
      button.onclick = () => openHistory(Number(button.dataset.open));
    });
    $$('[data-repeat]').forEach((button) => {
      button.onclick = () => repeatHistory(Number(button.dataset.repeat));
    });
    $$('[data-delete]').forEach((button) => {
      button.onclick = async () => {
        const id = Number(button.dataset.delete);
        if (!await confirmDeleteSimulation(id)) return;
        button.disabled = true;
        try {
          await api(`/api/history/${id}`, { method: "DELETE" });
          toast(`Simulación #${id} borrada.`);
          const refreshed = await api(`/api/history${select.value ? `?case=${encodeURIComponent(select.value)}` : ""}`);
          paint(refreshed);
          if (Number(openId) === id) $("#opened-result").replaceChildren();
        } catch (error) {
          button.disabled = false;
          toast(error.message, true);
        }
      };
    });
  };

  paint(rows);
  select.onchange = async () => paint(await api(`/api/history${select.value ? `?case=${encodeURIComponent(select.value)}` : ""}`));
  if (openId) await openHistory(openId);
}

function confirmDeleteSimulation(id) {
  return new Promise((resolve) => {
    const overlay = document.createElement("div");
    overlay.className = "modal-backdrop";
    overlay.innerHTML = `
      <section class="confirm-dialog" role="alertdialog" aria-modal="true" aria-labelledby="delete-title" aria-describedby="delete-description">
        <h2 id="delete-title">Borrar simulación #${id}</h2>
        <p id="delete-description">Se eliminarán esta corrida y sus resultados guardados del historial. Esta acción no se puede deshacer.</p>
        <div class="actions"><button type="button" class="btn secondary" data-cancel-delete>Cancelar</button><button type="button" class="btn danger" data-confirm-delete>Borrar simulación</button></div>
      </section>`;
    document.body.append(overlay);
    const cancel = $("[data-cancel-delete]", overlay);
    const confirm = $("[data-confirm-delete]", overlay);
    const previousFocus = document.activeElement;
    const finish = (answer) => {
      document.removeEventListener("keydown", onKeyDown);
      overlay.remove();
      if (previousFocus?.isConnected) previousFocus.focus();
      resolve(answer);
    };
    const onKeyDown = (event) => {
      if (event.key === "Escape") finish(false);
      if (event.key === "Tab") {
        event.preventDefault();
        (document.activeElement === cancel ? confirm : cancel).focus();
      }
    };
    cancel.addEventListener("click", () => finish(false));
    confirm.addEventListener("click", () => finish(true));
    overlay.addEventListener("click", (event) => {
      if (event.target === overlay) finish(false);
    });
    document.addEventListener("keydown", onKeyDown);
    cancel.focus();
  });
}

async function openHistory(id) {
  try {
    const item = await api(`/api/history/${id}`);
    const area = $("#opened-result");
    area.innerHTML = `<div class="panel"><h3>Corrida recuperada · #${id}</h3><div id="recovered"></div></div>`;
    displayResult({ ...item.result, simulation_id: item.id, scenario: item.scenario }, $("#recovered"));
  } catch (error) {
    toast(error.message, true);
  }
}

async function repeatHistory(id) {
  try {
    const item = await api(`/api/history/${id}`);
    navigate(`caso/${item.case_code}`);
    setTimeout(() => execute({
      case: item.case_code,
      scenario: item.scenario,
      parameters: item.parameters,
    }, true), 80);
  } catch (error) {
    toast(error.message, true);
  }
}

function downloadCSV(methods, id) {
  const rows = [["metodo", "numero", "datos"]];
  methods.forEach((method) => (method.steps || []).forEach((step, index) => {
    rows.push([method.name, index + 1, JSON.stringify(step)]);
  }));
  const csv = rows.map((row) => row.map((value) => `"${String(value).replaceAll('"', '""')}"`).join(",")).join("\n");
  const anchor = document.createElement("a");
  anchor.href = URL.createObjectURL(new Blob(["\ufeff" + csv], { type: "text/csv;charset=utf-8" }));
  anchor.download = `SIMTELE_RISK_${id || "resultado"}_iteraciones.csv`;
  anchor.click();
  URL.revokeObjectURL(anchor.href);
}

window.addEventListener("hashchange", renderRoute);
window.addEventListener("resize", () => {
  if (currentResult) currentResult.charts.forEach((chart, index) => drawChart($(`#chart-${index}`), chart));
});

(async () => {
  try {
    catalog = await api("/api/catalog");
    renderRoute();
  } catch (error) {
    $("#view").innerHTML = `<div class="empty">No se pudo cargar el catálogo: ${esc(error.message)}</div>`;
  }
})();
