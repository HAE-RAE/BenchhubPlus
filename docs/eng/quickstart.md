# Quick Start Guide

Welcome to BenchHub Plus! This guide walks you through the fastest way to run the full evaluation stack on your machine. Every step is designed for newcomers—no infrastructure background required.

---

## 🧭 What you'll set up

BenchHub Plus is made of several services that communicate with each other:

| Component | Purpose | Default dev port |
|-----------|---------|------------------|
| Streamlit Frontend | Web interface for creating and browsing evaluations | `8502` |
| FastAPI Backend | REST API that orchestrates evaluations | `8001` |
| Celery Worker | Executes evaluation jobs in the background | – |
| PostgreSQL | Stores evaluation plans and results | `5433` |
| Redis | Message broker + cache for Celery | `6380` |
| Flower (optional) | Celery monitoring dashboard | `5556` |

The quickest path is to let Docker Compose start and wire these services together for you.

---

## ✅ Before you begin

| Requirement | Notes |
|-------------|-------|
| **Operating system** | macOS, Linux, or Windows (via WSL2) |
| **Git** | Download from [git-scm.com](https://git-scm.com/downloads) |
| **Docker Desktop / Engine** | Includes Docker Compose v2 |
| **Model API key** | An OpenAI API key or another supported model provider key |

> ℹ️ If Docker is not available you can still follow the "Local Python environment" path at the end of this guide.

---

## 🚀 Step 1 – Clone the repository

```bash
git clone https://github.com/HAE-RAE/BenchhubPlus.git
cd BenchhubPlus
```

---

## 🛠️ Step 2 – Create and edit your `.env`

1. Copy the example file:

   ```bash
   cp .env.example .env
   ```

2. Open `.env` in your editor and set at least these values:
   - `OPENAI_API_KEY`: paste your key (or set the right variables for another provider)
   - `POSTGRES_PASSWORD`: choose any strong password for the bundled database
   - Optional: adjust ports if the defaults conflict with other apps

All other defaults are safe to keep for a first run.

---

## 🧪 Step 3 – Launch everything with one command

The helper script wraps Docker Compose so you do not have to remember long commands.

```bash
./scripts/deploy.sh development
```

What the script does for you:

1. Checks Docker & Docker Compose availability.
2. Builds the backend, worker, and frontend images.
3. Starts `docker-compose.dev.yml` in the background.
4. Waits until PostgreSQL, Redis, API, and frontend are healthy.
5. Initializes the database schema.

The first run can take a few minutes while Docker downloads base images.

---

## 🔍 Step 4 – Verify the services

Once the script finishes you should see a success summary with useful URLs. You can double-check manually:

```bash
# Backend health endpoint
curl http://localhost:8001/api/v1/health
```

- Open the Flower dashboard in your browser: http://localhost:5556

If the curl command returns JSON that includes `"status": "healthy"`, the backend is ready.

---

## 🕹️ Step 5 – Open the web app

Visit **http://localhost:8502** in your browser. You should land on the "Evaluate" tab where you can submit your first natural-language evaluation request. The [User Manual](./user-manual.md) explains each field in detail.

---

## ⏹️ Stopping and restarting

```bash
# Stop the development stack
docker-compose -f docker-compose.dev.yml down

# Restart it later
./scripts/deploy.sh development
```

Docker keeps the PostgreSQL and Redis data volumes so you will not lose previous results between restarts.

---

## 🧑‍💻 Alternative: Local Python environment

Prefer running services directly on your machine? Use the provided setup script (requires Python 3.11+):

```bash
./scripts/setup.sh
source venv/bin/activate
```

Then start each component in a separate terminal:

```bash
# Terminal 1 – FastAPI backend
python -m uvicorn apps.backend.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 – Celery worker
celery -A apps.worker.celery_app worker --loglevel=info

# Terminal 3 – Streamlit frontend
streamlit run apps/frontend/streamlit_app.py --server.port 8501 --server.address 0.0.0.0
```

For this mode you must provide your own PostgreSQL and Redis instances that match the connection details in `.env` (or switch to SQLite/Redis alternatives).

---

## 📚 Next steps

- Follow the [User Manual](./user-manual.md) for a guided tour of the interface.
- Review the [Setup Guide](./SETUP_GUIDE.md) if you need production-grade deployment tips.
- Explore the [API Reference](./api-reference.md) to integrate BenchHub Plus into your own tooling.

Happy benchmarking! 🎉
