# FactCheck AI

> AI-powered fake news detection with multi-source claim verification and a React frontend.

---

## Overview

FactCheck AI is a full-stack application that classifies news articles as **REAL**, **FAKE**, or **UNCERTAIN**. It combines a trained TF-IDF + Logistic Regression model with a multi-stage claim verification pipeline that retrieves evidence from Google Fact Check, Bing, Tavily, SerpAPI, and Wikipedia.

Users can submit article text or a public URL. Each submission runs through ML classification, factual claim extraction, evidence retrieval, claim-level verification, a hybrid decision engine, and explanation generation. Completed analyses are persisted to MongoDB and accessible via an analysis history page.

A Streamlit demo interface is also available for local experimentation without the full frontend stack.

---

## Features

- **Dual input modes** — analyze by article text/headline or by public URL
- **ML classification** — TF-IDF vectorization + Logistic Regression with calibrated fake-news probability
- **Factual claim extraction** — automatically identifies verifiable statements in the submitted text
- **Multi-source evidence retrieval** — queries Google Fact Check API, Bing, Tavily, SerpAPI, and Wikipedia
- **Claim-level verification** — scores each claim against retrieved evidence and assigns a stance
- **Hybrid decision engine** — combines ML confidence and claim verification results into a final verdict
- **Human-readable explanation** — generates a summary of why the decision was reached
- **Analysis history** — MongoDB-backed persistence; users can review, open, and delete past analyses
- **User feedback** — users can rate whether an analysis was helpful
- **Model metrics endpoint** — exposes holdout-test accuracy, precision, recall, and F1 via the API
- **CLI inference** — run predictions directly from the command line without the server
- **Streamlit app** — lightweight local demo interface

---

## Tech Stack

### Backend

| Layer | Technology |
|---|---|
| API framework | FastAPI ≥ 0.110 |
| ASGI server | Uvicorn ≥ 0.28 |
| ML pipeline | scikit-learn ≥ 1.4 (TF-IDF + Logistic Regression) |
| Data processing | pandas ≥ 2.0, NumPy ≥ 1.25 |
| Model serialization | joblib ≥ 1.3 |
| Database driver | Motor ≥ 3.3 (async MongoDB), PyMongo ≥ 4.6 |
| HTTP client | httpx ≥ 0.27 |
| Article extraction | trafilatura |
| Settings | pydantic-settings ≥ 2.2 |
| Python | ≥ 3.10 |

### Frontend

| Layer | Technology |
|---|---|
| UI library | React 19 |
| Bundler | Vite 8 |
| Routing | React Router DOM 7 |
| HTTP client | Axios 1.x |
| Icons | Lucide React |
| Linter | oxlint |

### Dev / CI

| Tool | Purpose |
|---|---|
| pytest ≥ 8 | Unit and integration tests |
| Ruff ≥ 0.4 | Python linting and import sorting |
| GitHub Actions | CI — lint, test, training smoke, CLI smoke |

---

## Prerequisites

- **Python ≥ 3.10**
- **Node.js ≥ 18** (for the React frontend)
- **MongoDB** — local instance or a remote URI (the backend degrades gracefully if unavailable; analysis results are still returned but not persisted)

---

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd Fake_News_Detection
```

### 2. Install Python dependencies

```bash
# Production dependencies (ML pipeline + backend)
pip install -r requirements.txt
pip install -r backend/requirements.txt

# Dev dependencies (pytest, ruff) — optional
pip install -r requirements-dev.txt
```

Or use the Makefile shortcuts:

```bash
make install       # installs requirements.txt
make install-dev   # installs requirements-dev.txt
```

### 3. Train the ML model

The `data/` directory contains `true.csv` and `fake.csv`. Run training to produce model artifacts in `outputs/`:

```bash
make train
# expands to:
python src/train_model.py --real data/True.csv --fake data/Fake.csv --outdir outputs
```

Pre-trained artifacts (`outputs/pipeline.joblib`, `outputs/vectorizer.joblib`, `outputs/metrics.json`) are already present if you cloned the full repository.

### 4. Install frontend dependencies

```bash
cd frontend
npm install
```

---

## Configuration

Copy the example env file and fill in values:

```bash
cp .env.example backend/.env
```

Key variables (`backend/.env`):

```env
# Project metadata
PROJECT_NAME="Fake News Detection API"
VERSION="1.0.0"
API_PREFIX="/api"

# Path to the trained model artifact (relative to project root or absolute)
MODEL_PATH=outputs/pipeline.joblib

# CORS origins for the React frontend
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000

# Server
HOST=127.0.0.1
PORT=8000
DEBUG=false

# MongoDB (optional — app runs without it but history won't be saved)
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=fake_news_detection

# Evidence provider API keys (all optional; unused providers are skipped)
GOOGLE_FACTCHECK_API_KEY=
TAVILY_API_KEY=
SERPAPI_API_KEY=
BING_SEARCH_API_KEY=

# Pipeline limits
EVIDENCE_TIMEOUT_SECONDS=5.0
MAX_CLAIMS_PER_ANALYSIS=5
MAX_EVIDENCE_PER_CLAIM=5
```

> The backend reads `.env` from the project root and `backend/.env`. All API keys are optional — the system falls back to Wikipedia evidence if no external providers are configured.

---

## Usage

### Start the FastAPI backend

```bash
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

API docs are served automatically at:
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

### Start the React frontend

```bash
cd frontend
npm run dev
```

The frontend runs at `http://localhost:5173` by default.

### Streamlit demo (standalone, no backend required)

```bash
make app
# expands to:
streamlit run src/streamlit_app.py
```

### CLI inference

Run a single prediction against the trained pipeline without starting the server:

```bash
python src/detect_fake_news.py \
  --pipeline outputs/pipeline.joblib \
  --text "Reuters reported that officials released a policy statement." \
  --json
```

CLI options:

| Flag | Default | Description |
|---|---|---|
| `--pipeline` | *(required)* | Path to `pipeline.joblib` |
| `--text` | *(required)* | News text to classify |
| `--threshold` | `0.50` | Probability threshold for FAKE |
| `--uncertainty-margin` | `0.05` | Margin around threshold for UNCERTAIN |
| `--json` | off | Output result as JSON |

---

## Project Structure

```
Fake_News_Detection/
├── backend/                   # FastAPI application
│   ├── app/
│   │   ├── api/               # Route handlers
│   │   │   ├── routes_analysis.py   # /api/analyze endpoints
│   │   │   ├── routes_feedback.py   # /api/feedback endpoints
│   │   │   ├── routes_health.py     # /api/health endpoint
│   │   │   ├── routes_history.py    # /api/history endpoints
│   │   │   └── routes_metrics.py    # /api/metrics endpoint
│   │   ├── database/          # MongoDB connection and repositories
│   │   ├── models/            # Pydantic schemas
│   │   ├── providers/         # Evidence providers (Google, Bing, Tavily, SerpAPI, Wikipedia)
│   │   ├── services/          # Business logic
│   │   │   ├── ml_service.py
│   │   │   ├── claim_extractor.py
│   │   │   ├── evidence_retriever.py
│   │   │   ├── claim_verification_service.py
│   │   │   ├── decision_engine.py
│   │   │   ├── explanation_service.py
│   │   │   ├── source_scoring_service.py
│   │   │   └── article_url_service.py
│   │   ├── utils/             # Logger and helpers
│   │   ├── config.py          # Pydantic settings
│   │   └── main.py            # FastAPI app entrypoint
│   └── requirements.txt       # Backend-only dependencies
├── frontend/                  # React + Vite application
│   ├── src/
│   │   ├── pages/Analyze.jsx  # Main analysis page
│   │   ├── App.jsx            # Routes and layout
│   │   └── services/          # Axios API client
│   └── package.json
├── src/                       # ML pipeline scripts
│   ├── train_model.py         # Training, evaluation, artifact export
│   ├── detect_fake_news.py    # CLI inference tool
│   ├── text_clean.py          # Custom text preprocessing (TextCleaner)
│   ├── evaluation.py          # Out-of-source evaluation helpers
│   └── model_compat.py        # Pipeline serialization and checksum
├── data/
│   ├── true.csv               # Real news dataset
│   └── fake.csv               # Fake news dataset
├── outputs/                   # Generated model artifacts
│   ├── pipeline.joblib        # Full sklearn pipeline (vectorizer + classifier)
│   ├── vectorizer.joblib      # Standalone TF-IDF vectorizer
│   ├── model.joblib           # Standalone classifier
│   ├── metrics.json           # Holdout-test evaluation metrics
│   └── charts/                # Training evaluation plots
├── tests/                     # pytest test suite
├── .env.example               # Environment variable template
├── Makefile                   # Common task shortcuts
├── pyproject.toml             # Python project metadata and tool config
└── requirements.txt           # Core Python dependencies
```

---

## API Documentation

All routes are prefixed with `/api`. Interactive documentation is available at `/docs`.

### Analysis

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/analyze` | Full pipeline: ML + claim extraction + evidence + decision engine |
| `POST` | `/api/analyze/ml-only` | ML classification only (no claim verification) |
| `POST` | `/api/analyze/claims` | Claim extraction + evidence retrieval only |
| `POST` | `/api/analyze/url` | Fetch a public URL and run the full analysis pipeline |

**Request body for `/api/analyze` and `/api/analyze/ml-only`:**

```json
{
  "headline": "Officials passed a new budget bill",
  "article_text": "Full article text here..."
}
```

**Request body for `/api/analyze/url`:**

```json
{
  "url": "https://example.com/news-article"
}
```

### History

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/history` | List recent analyses (`user_id`, `limit` query params) |
| `GET` | `/api/history/{analysis_id}` | Get a single analysis with claims and evidence |
| `DELETE` | `/api/history/{analysis_id}` | Delete an analysis and all associated data |

### Feedback

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/feedback` | Submit feedback for an analysis |
| `GET` | `/api/feedback/{analysis_id}` | Get feedback for an analysis |

### Health & Metrics

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/health` | API status, ML model readiness, and DB connection state |
| `GET` | `/api/metrics` | Holdout-test model metrics (accuracy, precision, recall, F1) |

---

## Testing

Run the full test suite:

```bash
make test
# expands to:
pytest -q
```

Run linting:

```bash
make lint
# expands to:
ruff check src tests
```

Test coverage in `tests/`:

| File | What it covers |
|---|---|
| `test_text_clean.py` | TextCleaner preprocessing |
| `test_model_compat.py` | Pipeline serialization and checksum |
| `test_cli_predict.py` | CLI inference (`detect_fake_news.py`) |
| `test_evaluation.py` | Evaluation helper functions |
| `test_claim_extraction.py` | Claim extractor service |
| `test_evidence_providers.py` | Evidence provider integrations |
| `test_decision_and_verification.py` | Decision engine and claim verification |
| `test_backend_api.py` | FastAPI endpoint integration tests |
| `test_pipeline.py` | End-to-end pipeline smoke test |
| `test_training_smoke_artifacts.py` | Validates training output artifacts |

---

## CI/CD

GitHub Actions runs on every push and pull request to `main` (`.github/workflows/ci.yml`):

1. Install all Python dependencies (core, dev, backend)
2. Compile all source files (`python -m compileall`)
3. Run the full pytest suite
4. Run Ruff linting
5. Run a training smoke with reduced hyperparameters
6. Run a leakage-controlled training smoke (`--strip-source-artifacts --eval-out-of-source`)
7. Run a CLI prediction smoke check
8. Validate smoke output artifacts
9. Upload smoke outputs as a GitHub Actions artifact

---

## License

MIT License — see [LICENSE](LICENSE) for full text.