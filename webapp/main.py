from pathlib import Path
import uuid
from typing import Any, List, Optional

import duckdb
from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import urllib.request
import mimetypes
import logging


BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
STATIC_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="DuckDB Viewer")

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
# Ensure local DuckDB WASM assets are available to avoid CORS on workers
DUCKDB_ASSETS_DIR = STATIC_DIR / "duckdb"
DUCKDB_ASSETS_DIR.mkdir(parents=True, exist_ok=True)
MVP_WORKER = DUCKDB_ASSETS_DIR / "duckdb-browser-mvp.worker.js"
MVP_WASM = DUCKDB_ASSETS_DIR / "duckdb-browser-mvp.wasm"


def ensure_duckdb_assets() -> None:
    logging.getLogger(__name__).info("Ensuring DuckDB WASM assets are present...")
    # Ensure proper content-type for wasm
    mimetypes.add_type("application/wasm", ".wasm")

    assets = {
        MVP_WORKER: "https://cdn.jsdelivr.net/npm/@duckdb/duckdb-wasm@1.28.0/dist/duckdb-browser-mvp.worker.js",
        MVP_WASM: "https://cdn.jsdelivr.net/npm/@duckdb/duckdb-wasm@1.28.0/dist/duckdb-browser-mvp.wasm",
    }
    for path, url in assets.items():
        if not path.exists() or path.stat().st_size == 0:
            try:
                tmp_path = str(path) + ".tmp"
                urllib.request.urlretrieve(url, tmp_path)
                os.replace(tmp_path, path)
                logging.getLogger(__name__).info("Downloaded %s", path.name)
            except Exception as exc:  # noqa: BLE001
                logging.getLogger(__name__).warning(
                    "Failed to download %s: %s", path.name, exc
                )


ensure_duckdb_assets()


# Simple single-user state. For multi-user, use signed sessions keyed by cookie.
current_db_path: Optional[Path] = None


def execute_query(database_path: Path, sql: str) -> dict:
    with duckdb.connect(database=str(database_path), read_only=False) as conn:
        try:
            cursor = conn.execute(sql)
            try:
                rows: List[List[Any]] = cursor.fetchall()
                columns = [d[0] for d in cursor.description] if cursor.description else []
            except duckdb.Error:
                rows = []
                columns = []
            conn.commit()
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": str(exc), "columns": [], "rows": []}
    return {"ok": True, "error": None, "columns": columns, "rows": rows}


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    ctx = {
        "request": request,
        "db_loaded": current_db_path is not None,
        "db_name": current_db_path.name if current_db_path else None,
        "columns": [],
        "rows": [],
        "error": None,
        "sql": "SELECT * FROM information_schema.tables LIMIT 50;" if current_db_path else "",
    }
    return templates.TemplateResponse("index.html", ctx)


@app.get("/client", response_class=HTMLResponse)
async def client(request: Request):
    return templates.TemplateResponse("client.html", {"request": request})


@app.post("/upload")
async def upload_db(file: UploadFile = File(...)):
    global current_db_path
    if not file.filename.lower().endswith(".duckdb"):
        return RedirectResponse(url="/?error=Please+upload+a+.duckdb+file", status_code=303)

    file_id = uuid.uuid4().hex
    dest_path = UPLOAD_DIR / f"{file_id}.duckdb"
    with dest_path.open("wb") as f:
        f.write(await file.read())

    # Basic sanity check: try to open
    try:
        with duckdb.connect(database=str(dest_path), read_only=True):
            pass
    except Exception:  # noqa: BLE001
        dest_path.unlink(missing_ok=True)
        return RedirectResponse(url="/?error=Invalid+DuckDB+file", status_code=303)

    current_db_path = dest_path
    return RedirectResponse(url="/", status_code=303)


@app.post("/query", response_class=HTMLResponse)
async def run_query(request: Request, sql: str = Form("")):
    if current_db_path is None:
        return RedirectResponse(url="/?error=Upload+a+DuckDB+file+first", status_code=303)

    result = execute_query(current_db_path, sql)
    ctx = {
        "request": request,
        "db_loaded": True,
        "db_name": current_db_path.name,
        "columns": result["columns"],
        "rows": result["rows"],
        "error": result["error"],
        "sql": sql,
    }
    return templates.TemplateResponse("index.html", ctx)


@app.get("/healthz")
async def healthz():
    return {"status": "ok", "db_loaded": current_db_path is not None}


