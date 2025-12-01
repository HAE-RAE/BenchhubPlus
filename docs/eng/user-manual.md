# User Manual

This manual explains how to operate BenchHub Plus after you have started the stack with the [Quick Start Guide](./quickstart.md). It focuses on practical, beginner-friendly instructions so that anyone can run evaluations and interpret the results with confidence.

---

## 1. Launching & signing in

BenchHub Plus does not require user accounts. Once the services are running, open your browser and go to the frontend URL:

- **Development (docker-compose.dev.yml)**: http://localhost:3000
- **Production (docker-compose.yml)**: http://localhost:3000 (or via Nginx on http://localhost)

You should see the BenchHub Plus header and a horizontal navigation menu with four tabs: **Evaluate**, **Status**, **Browse**, and **System**.

> 💡 If the page does not load, verify that Docker containers are running (`docker-compose -f docker-compose.dev.yml ps`) and that the backend health check returns `{"status": "healthy"}`.

---

## 2. Evaluate tab – Create a new evaluation

The Evaluate tab is the starting point for every run.

### 2.1 Describe your evaluation

- **Natural Language Query** – Explain what you want to test in plain language. Examples:
  - "Compare GPT-4 and Claude 3 on Korean high school math problems"
  - "Evaluate coding assistance for Python bug fixes"
  - "Assess multilingual translation quality between English and Japanese"
- Tips for better plans:
  - Mention the subject area (math, science, code, etc.).
  - Specify the language and difficulty level when relevant.
  - Include the target task (QA, reasoning, generation, translation, …).

### 2.2 Configure the models

BenchHub Plus can evaluate one or more models at the same time. The UI guides you through the required fields for each model:

| Field | Description |
|-------|-------------|
| **Model Name** | Friendly name that will appear in the leaderboard (e.g. `gpt-4`, `claude-3`) |
| **API Base URL** | Endpoint for the provider (`https://api.openai.com/v1`, `https://api.anthropic.com`, …) |
| **API Key** | Secret token for the provider. Stored only in memory during the session. |
| **Model Type** | Choose from `openai`, `anthropic`, `huggingface`, or `custom`. Determines backend handling. |

Additional details:

- Use the **Number of models to evaluate** control above the forms to add more models (up to 10).
- Password inputs hide the API key while typing.
- BenchHub validates that each model has a name, base URL, and key before submission.

> 🔐 Security tip: API keys are never written to disk by the frontend. Close the browser when you finish your session to clear them from memory.

### 2.3 Submit the evaluation

1. Double-check the query and model details.
2. Click **🚀 Start Evaluation** (centered under the form).
3. The interface shows a spinner while the request is sent to the backend (`/api/v1/leaderboard/generate`).
4. On success you will see a green message with the generated **Task ID**. BenchHub automatically redirects you to the **Status** tab to monitor progress.

If validation fails (missing query, missing model information, or an API error) the page displays a red error message describing the problem.

---

## 3. Status tab – Track progress in real time

The Status tab is split into two sections: the current task and recent history.

### 3.1 Current task panel

- Shows the **Task ID** and a **Refresh Status** button.
- Fetches live data from `/api/v1/tasks/<task_id>`.
- Displays the current state with emojis:
  - 🟡 `PENDING` – queued, waiting for a worker.
  - 🔵 `STARTED` – running on a worker (auto-refreshes every 5 seconds).
  - 🟢 `SUCCESS` – finished successfully and results are ready.
  - 🔴 `FAILURE` – finished with an error (the error message is printed).
- When the task succeeds, the tab automatically renders the evaluation results (see next section).
- Expand **Task Details** for the raw JSON payload returned by the backend.

### 3.2 Task history table

- Lists the 10 most recent tasks submitted during this browser session.
- Columns include `Task ID`, `Query`, `Models`, `Submitted`, and `Status`.
- Useful for jumping back to earlier results without re-running evaluations.

---

## 4. Understanding the results

When a task completes successfully, the Status tab displays a rich results dashboard.

### 4.1 Leaderboard table

- Ranks each model by the `Score` returned by the backend.
- Includes additional columns such as `Accuracy`, `Samples`, and `Execution Time`.
- Scores are color-coded with a gradient to highlight the best performers.

### 4.2 Visual comparisons

- **Bar chart** – Model performance comparison (`Score` on the y-axis).
- **Radar chart** – Multi-metric snapshot (Score, Accuracy, and relative sample count). Only shown when two or more models are present.

### 4.3 Detailed JSON

Expand the **Detailed Results** section to inspect the full JSON response. This is helpful if you want to export raw metrics or debug a custom integration.

> 💾 Want to save results? Use the copy button next to the JSON block or download the API response directly via `/api/v1/tasks/<task_id>`.

---

## 5. Browse tab – Explore past leaderboards

The Browse tab queries the backend’s historical leaderboard API (`/api/v1/leaderboard/browse`).

1. Pick filters for **Language**, **Subject**, **Task Type**, and **Max Results**.
2. Click **🔍 Search Leaderboard** to execute the query.
3. Review the results table (rank, model name, score, metadata, and last updated date).
4. A horizontal bar chart highlights the top 10 models for quick comparison.

If no entries match the filters, the app shows a friendly message instead of an empty table.

---

## 6. System tab – Check health and capacity

Use this tab whenever something looks off.

- Calls `/api/v1/health` to summarize system health:
  - Database and Redis connectivity.
  - API availability status.
- Calls `/api/v1/stats` for live metrics:
  - Pending / running / completed / failed task counts.
  - Number of cached leaderboard entries.
  - Planner agent availability flag.

If any component shows as disconnected, inspect container logs (`docker-compose -f docker-compose.dev.yml logs <service>`) or retry the deploy script.

---

## 7. Troubleshooting quick answers

| Symptom | Recommended actions |
|---------|---------------------|
| **API error shown in Evaluate tab** | Confirm your API key is valid and has sufficient quota. Check backend logs for provider-specific errors. |
| **Task stuck in PENDING** | Ensure the worker container is running (`docker ps` should show `benchhub_worker_dev`). Restart with `docker-compose -f docker-compose.dev.yml restart worker`. |
| **Task fails immediately** | Expand the Task Details to read the error message. Common causes: typo in API base URL, unsupported model type, or provider outage. |
| **Frontend cannot reach backend** | Verify `API_BASE_URL` (default `http://localhost:8001`) matches the backend port you exposed. |
| **Metrics look empty** | Smaller sample sizes may yield sparse metrics; consider increasing the sample size or verifying that the evaluation plan generated questions successfully. |

---

## 8. Where data and logs live

- **Docker volumes**: PostgreSQL and Redis data persist in `postgres_dev_data` and `redis_dev_data` volumes.
- **Application logs**: Mounted inside the repository under the `logs/` directory.
- **Temporary files**: Workers use `/tmp` inside the container for intermediate artifacts.

Clean up with:

```bash
docker-compose -f docker-compose.dev.yml down -v   # removes containers and volumes
rm -rf logs/*                                       # clears application logs
```

---

## 9. Integrate programmatically

Everything the UI does is backed by REST endpoints. Useful ones include:

| Endpoint | Description |
|----------|-------------|
| `POST /api/v1/leaderboard/generate` | Submit a new evaluation (same payload as the UI form). |
| `GET /api/v1/tasks/<task_id>` | Poll task progress and fetch results. |
| `GET /api/v1/leaderboard/browse` | Retrieve historical leaderboard entries. |
| `GET /api/v1/health` | Check service health (used in System tab). |

See the [API Reference](./api-reference.md) for request/response schemas.

---

## 10. Getting more help

- **Documentation**: Quick Start, Setup Guide, API Reference, and this manual cover most workflows.
- **GitHub Issues**: https://github.com/HAE-RAE/BenchhubPlus/issues – report bugs or request features.
- **Discussions**: Share ideas or ask usage questions with the community.
- **Enterprise support**: Contact the BenchHub Plus maintainers for bespoke integrations or training.

Happy benchmarking! 🎉
