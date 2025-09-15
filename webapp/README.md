DuckDB Viewer Webapp
====================

A minimal FastAPI app to upload a `.duckdb` file and run SQL queries from the browser.

Quickstart
----------

1. Create a virtual environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r webapp/requirements.txt
```

2. Run the app:

```bash
uvicorn webapp.main:app --reload
```

3. Open the browser at `http://127.0.0.1:8000`.

Notes
-----
- This demo keeps the last uploaded DB in-process state; for multi-user, store per-session.
- Uploaded files are written to `webapp/uploads/` and not auto-cleaned.
- For production, run behind a hardened ASGI server and add auth/rate limits.


