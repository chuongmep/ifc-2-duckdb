import * as duckdb from "https://cdn.jsdelivr.net/npm/@duckdb/duckdb-wasm@1.28.0/+esm";

const WORKER_URL = "/static/duckdb/duckdb-browser-mvp.worker.js";
const WASM_URL = "/static/duckdb/duckdb-browser-mvp.wasm";

let db = null;
let conn = null;
let initPromise = null;

function setRunEnabled(enabled) {
  const btn = document.getElementById("run");
  if (btn) btn.disabled = !enabled;
}

async function init() {
  const worker = new Worker(WORKER_URL);
  const logger = new duckdb.ConsoleLogger();
  const workerDB = new duckdb.AsyncDuckDB(logger, worker);
  await workerDB.instantiate(WASM_URL, null);
  db = workerDB;
  conn = await db.connect();

  const sqlInput = document.getElementById("sql");
  if (sqlInput) {
    sqlInput.value = "SELECT * FROM information_schema.tables LIMIT 50;";
  }
  setRunEnabled(true);
}

async function loadDatabaseFile(file) {
  const buffer = await file.arrayBuffer();
  const bytes = new Uint8Array(buffer);
  const name = `uploaded-${Date.now()}.duckdb`;
  await db.registerFileBuffer(name, bytes);
  if (conn) await conn.close();
  conn = await db.connect({ database: name });
}

function renderTable(columns, rows) {
  const table = document.getElementById("table");
  table.innerHTML = "";
  const thead = document.createElement("thead");
  const trh = document.createElement("tr");
  for (const c of columns) {
    const th = document.createElement("th");
    th.textContent = c;
    trh.appendChild(th);
  }
  thead.appendChild(trh);
  table.appendChild(thead);

  const tbody = document.createElement("tbody");
  for (const r of rows) {
    const tr = document.createElement("tr");
    for (const cell of r) {
      const td = document.createElement("td");
      td.textContent = cell === null ? "NULL" : String(cell);
      tr.appendChild(td);
    }
    tbody.appendChild(tr);
  }
  table.appendChild(tbody);
}

async function runQuery() {
  const errorEl = document.getElementById("error");
  errorEl.style.display = "none";
  const sql = document.getElementById("sql").value;
  // Ensure initialization finished
  if (!db || !conn) {
    if (!initPromise) initPromise = init();
    await initPromise.catch(() => {});
  }
  if (!conn) {
    errorEl.textContent = "Database not ready. Upload a .duckdb file or wait for init.";
    errorEl.style.display = "block";
    return;
  }
  try {
    const result = await conn.query(sql);
    const cols = result.schema.fields.map((f) => f.name);
    const rows = result.toArray().map((r) => cols.map((c) => r[c]));
    renderTable(cols, rows);
  } catch (e) {
    console.error(e);
    errorEl.textContent = String(e?.message || e);
    errorEl.style.display = "block";
  }
}

document.addEventListener("DOMContentLoaded", () => {
  setRunEnabled(false);
  initPromise = init();
  document.getElementById("file").addEventListener("change", async (ev) => {
    const file = ev.target.files?.[0];
    if (!file) return;
    document.getElementById("fileInfo").textContent = `Loaded: ${file.name}`;
    await loadDatabaseFile(file);
  });
  document.getElementById("run").addEventListener("click", runQuery);
});


