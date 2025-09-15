IFC2DuckDB Webapp Deployment
============================

This document covers multiple ways to deploy the FastAPI web app located in `webapp/`.

Local Development
-----------------
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -U pip
pip install -r webapp/requirements.txt
uvicorn webapp.main:app --host 0.0.0.0 --port 8000 --reload
```

Docker
------
Build and run:
```bash
docker build -t ifc2duckdb-webapp -f webapp/Dockerfile webapp
docker run --rm -p 8000:8000 -v $(pwd)/webapp/uploads:/app/webapp/uploads ifc2duckdb-webapp
```

Docker Compose
--------------
```bash
docker-compose up --build
```

Render.com
----------
1. Push to GitHub.
2. Create a new Web Service:
   - Repo: this repository
   - Environment: Python
   - Build Command: `pip install -r webapp/requirements.txt`
   - Start Command: `uvicorn webapp.main:app --host 0.0.0.0 --port $PORT --workers 2`
3. Health check path: `/healthz`

Nginx + systemd (Ubuntu example)
--------------------------------
1. Copy app to `/opt/ifc2duckdb` and create venv:
```bash
sudo mkdir -p /opt/ifc2duckdb
sudo cp -r . /opt/ifc2duckdb
cd /opt/ifc2duckdb
python3 -m venv .venv && source .venv/bin/activate
pip install -r webapp/requirements.txt
```
2. Install systemd unit:
```bash
sudo cp deploy/ifc2duckdb-web.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now ifc2duckdb-web
```
3. Nginx reverse proxy:
```bash
sudo cp deploy/nginx.conf /etc/nginx/sites-available/ifc2duckdb
sudo ln -s /etc/nginx/sites-available/ifc2duckdb /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

Notes
-----
- Uploaded `.duckdb` files are saved to `webapp/uploads/`.
- Consider storage quotas and cleanup for production.
- Add HTTPS via Let's Encrypt (Certbot) for public-facing deployments.


