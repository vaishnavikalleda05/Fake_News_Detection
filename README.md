# FactCheck AI

**AI-powered fake news detection and multi-source claim verification system**

![Python](https://img.shields.io/badge/Python-3.10%2B-3776ab?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-19.2-61dafb?logo=react&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)
![Tests](https://img.shields.io/badge/Tests-pytest-blue)

---

## Overview

FactCheck AI is an educational full-stack system that detects fake news by combining **machine learning classification** with **multi-source evidence verification**. Instead of relying solely on text patterns, it:

1. **Classifies articles** as REAL/FAKE using a trained ML model (TF-IDF + Logistic Regression)
2. **Extracts verifiable claims** from article text automatically
3. **Retrieves evidence** from multiple sources (Google Fact Check API, web search, Wikipedia)
4. **Verifies claims** by comparing them against retrieved evidence
5. **Generates transparent explanations** combining ML confidence with evidence analysis
6. **Persists results** in MongoDB for historical review

The system achieves **99.64% accuracy** on its holdout test set and provides end-to-end transparency through decision factors, evidence citations, and human-readable explanations.

---

## Features

- **Multi-Input Analysis**
  - Analyze articles by headline + body text
  - Analyze public articles directly from URL
  - Input validation and graceful error handling

- **Machine Learning**
  - TF-IDF vectorization + Logistic Regression classifier
  - Probability estimation with confidence scores
  - REAL / FAKE classification with 99.64% accuracy
  - Cross-validation and honest holdout evaluation

- **Claim Extraction**
  - Automatic factual claim identification
  - Heuristic sentence segmentation with abbreviation protection
  - Boilerplate and opinion filtering
  - Numeric fact detection and deduplication
  - Configurable claim limits

- **Multi-Source Evidence Retrieval**
  - Concurrent queries across multiple providers
  - Google Fact Check Tools API integration
  - Web search provider support
  - Wikipedia encyclopedia lookups
  - Automatic deduplication and relevance ranking

- **Claim Verification**
  - Stance classification (SUPPORTED / CONTRADICTED / INSUFFICIENT)
  - Relevance scoring based on lexical overlap
  - Source quality evaluation
  - Confidence aggregation

- **Hybrid Decision Engine**
  - Combines ML prediction (35%) with evidence verification (65%)
  - Transparent decision factors and reasoning
  - Confidence-adjusted final verdict

- **Analysis Explainability**
  - Human-readable explanations grounded in data
  - Decision breakdown (supporting/contradicted/insufficient claims)
  - Evidence citations with source URLs
  - Transparency into ML and verification signals

- **History & Persistence**
  - MongoDB-backed analysis history
  - Graceful degradation if database unavailable
  - User-specific analysis retrieval
  - Delete historical analyses

- **Web Interface**
  - React SPA with modern UI
  - Dashboard showing model metrics
  - Analyze page with real-time results display
  - Interactive evidence and claim browsing

---

## Tech Stack

### Backend
- **Framework**: FastAPI >= 0.110.0 (async Python web framework)
- **Server**: Uvicorn >= 0.28.0 (ASGI)
- **Validation**: Pydantic 2.6+ (data schemas & settings)
- **Database**: MongoDB + Motor (async driver) + PyMongo
- **ML Pipeline**: scikit-learn (TF-IDF, Logistic Regression)
- **Data Processing**: pandas >= 2.0, numpy >= 1.25
- **HTTP Client**: httpx >= 0.27.0 (async)
- **Article Extraction**: trafilatura
- **Configuration**: python-dotenv >= 1.0.0

### Frontend
- **Framework**: React 19.2.8
- **Build Tool**: Vite 8.2.0
- **Routing**: react-router-dom 7.18.2
- **HTTP Client**: axios 1.19.0
- **Icons**: lucide-react 1.31.0
- **Linter**: oxlint 1.75.0

### Development & Testing
- **Testing**: pytest >= 8.0
- **Linting**: ruff >= 0.4
- **Model Serialization**: joblib >= 1.3
- **Plotting**: matplotlib >= 3.7 (training visualizations)

---

## Prerequisites

- **Python 3.10 or higher**
- **Node.js & npm** (for frontend development)
- **MongoDB** (optional; application runs without persistence if unavailable)
- **git**

### Optional (for external evidence providers)
- Google Fact Check API key
- Tavily or SerpAPI key (web search)
- Bing Search API key

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/Fake_News_Detection.git
cd Fake_News_Detection
```

### 2. Set Up Python Environment

```bash
# Create a virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
# Install core dependencies
pip install -r requirements.txt

# Install backend-specific dependencies
pip install -r backend/requirements.txt

# Install dev dependencies (for testing and linting)
pip install -r requirements-dev.txt
```

### 4. Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

### 5. Verify Installation

```bash
# Compile check (Python files)
python -m compileall src tests backend

# Run tests
pytest -q
```

---

## Configuration

### Environment Variables

Create a `.env` file in the project root (copy from `.env.example`):

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# Server Configuration
HOST=127.0.0.1
PORT=8000
DEBUG=False

# Project
PROJECT_NAME=Fake News Detection API
VERSION=1.0.0
API_PREFIX=/api

# Model Path (relative to project root)
MODEL_PATH=outputs/pipeline.joblib

# CORS (Frontend URLs)
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000

# Database
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=fake_news_detection

# Optional API Keys (leave empty to skip provider)
GOOGLE_FACTCHECK_API_KEY=
TAVILY_API_KEY=
SERPAPI_API_KEY=
BING_SEARCH_API_KEY=

# Evidence & Claim Settings
EVIDENCE_TIMEOUT_SECONDS=5.0
MAX_CLAIMS_PER_ANALYSIS=5
MAX_EVIDENCE_PER_CLAIM=5
WIKIPEDIA_USER_AGENT=FakeNewsDetectionFactChecker/1.0 (your-email@example.com)
```

Also create `backend/.env` (copy from `backend/.env.example`):

```bash
cp backend/.env.example backend/.env
```

The same configuration applies; both files are checked by the application.

### MongoDB Setup (Optional)

If you want to persist analysis history:

```bash
# Start MongoDB (ensure it's installed)
mongod --dbpath ./db_data

# Or use a MongoDB service/container
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

If MongoDB is unavailable, the application continues without persistence.

---

## Usage

### 1. Prepare ML Model

If the trained model doesn't exist in `outputs/pipeline.joblib`, train it:

```bash
python src/train_model.py \
  --real data/true.csv \
  --fake data/fake.csv \
  --outdir outputs \
  --cv-folds 3 \
  --max-features 5000
```

This generates:
- `outputs/pipeline.joblib` - Serialized TF-IDF + Logistic Regression pipeline
- `outputs/vectorizer.joblib` - Fitted TF-IDF vectorizer
- `outputs/model.joblib` - Trained model
- `outputs/metrics.json` - Performance metrics
- `outputs/data_profile.json` - Dataset statistics
- `outputs/holdout_predictions.csv` - Test set predictions

### 2. Start the Backend API

```bash
# From project root with virtual environment activated
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload

# Or with Makefile
make app  # (Note: uses default settings from .env)
```

The API will be available at:
- **Base URL**: http://localhost:8000
- **API Docs (Swagger UI)**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 3. Start the Frontend Development Server

```bash
cd frontend
npm run dev
```

Navigate to http://localhost:5173 in your browser.

### 4. Test the System

In another terminal:

```bash
# Run the full test suite
pytest -q

# Run specific test file
pytest tests/test_backend_api.py -v

# Run with coverage
pytest --cov=backend --cov=src tests/
```

### 5. Use the CLI (Optional)

Analyze articles directly without the web interface:

```bash
python src/detect_fake_news.py \
  --pipeline outputs/pipeline.joblib \
  --text "Reuters reported that lawmakers passed a new budget bill." \
  --json
```

---

## Project Structure

```
Fake_News_Detection/
├── data/                              # Training datasets
│   ├── true.csv                       # Real news articles
│   └── fake.csv                       # Fake news articles
│
├── src/                               # ML scripts & utilities
│   ├── train_model.py                 # Training pipeline with CLI
│   ├── detect_fake_news.py            # CLI inference tool
│   ├── evaluate.py                    # Evaluation metrics
│   ├── model_compat.py                # Model serialization
│   ├── text_clean.py                  # Text preprocessing
│   └── evaluation.py                  # Detailed evaluation reports
│
├── backend/                           # FastAPI backend
│   ├── requirements.txt               # Backend dependencies
│   ├── .env.example                   # Configuration template
│   └── app/
│       ├── main.py                    # FastAPI entry point
│       ├── config.py                  # Settings (Pydantic)
│       ├── api/                       # Route handlers
│       │   ├── routes_analysis.py     # Analysis endpoints
│       │   ├── routes_feedback.py     # Feedback collection
│       │   ├── routes_health.py       # Health check
│       │   ├── routes_history.py      # History management
│       │   └── routes_metrics.py      # Model metrics
│       ├── database/                  # MongoDB integration
│       │   ├── connection.py          # Async connection
│       │   └── repositories.py        # Data access layer
│       ├── models/                    # Pydantic schemas
│       │   └── schemas.py             # Request/response models
│       ├── providers/                 # External API providers
│       │   ├── base_provider.py       # Abstract base class
│       │   ├── google_factcheck.py    # Google Fact Check API
│       │   ├── web_search.py          # Web search provider
│       │   └── wikipedia_provider.py  # Wikipedia extraction
│       ├── services/                  # Business logic
│       │   ├── ml_service.py          # ML model wrapper
│       │   ├── claim_extractor.py     # Claim extraction
│       │   ├── claim_verification_service.py
│       │   ├── decision_engine.py     # Hybrid decision logic
│       │   ├── evidence_retriever.py  # Multi-source retrieval
│       │   ├── evidence_analyzer.py   # Evidence analysis
│       │   ├── evidence_aggregation_service.py
│       │   ├── explanation_service.py # Explanation generation
│       │   ├── article_url_service.py # URL extraction
│       │   └── source_scoring_service.py
│       └── utils/
│           └── logger.py              # Logging setup
│
├── frontend/                          # React SPA
│   ├── package.json                   # Dependencies & scripts
│   ├── vite.config.js                 # Build config
│   ├── index.html                     # HTML entry
│   └── src/
│       ├── main.jsx                   # React entry
│       ├── App.jsx                    # Main component & router
│       ├── index.css                  # Global styles
│       ├── pages/
│       │   └── Analyze.jsx            # Analysis page
│       ├── services/
│       │   └── api.js                 # API client (axios)
│       └── assets/
│
├── tests/                             # Test suite (pytest)
│   ├── test_backend_api.py            # API integration tests
│   ├── test_claim_extraction.py       # Claim extraction tests
│   ├── test_cli_predict.py            # CLI tests
│   ├── test_decision_and_verification.py
│   ├── test_evaluation.py             # Metrics tests
│   ├── test_evidence_providers.py     # Provider tests
│   ├── test_model_compat.py           # Serialization tests
│   ├── test_pipeline.py               # Pipeline integration
│   ├── test_text_clean.py             # Preprocessing tests
│   └── test_training_smoke_artifacts.py
│
├── outputs/                           # ML artifacts (generated)
│   ├── pipeline.joblib                # Trained model
│   ├── vectorizer.joblib              # TF-IDF vectorizer
│   ├── model.joblib                   # Logistic Regression
│   ├── metrics.json                   # Performance metrics
│   ├── data_profile.json              # Dataset info
│   ├── leakage_report.json            # Data leakage analysis
│   └── charts/                        # Visualizations
│
├── .github/
│   └── workflows/
│       └── ci.yml                     # GitHub Actions CI/CD
│
├── Makefile                           # Build commands
├── pyproject.toml                     # Project metadata & tool config
├── .env.example                       # Backend config template
├── requirements.txt                   # Core dependencies
├── requirements-dev.txt               # Dev dependencies
├── requirements-lock.txt              # Locked versions
└── LICENSE                            # MIT License
```

---

## API Documentation

### Key Endpoints

#### Health Check
```
GET /api/health
```
Returns server status, ML model status, and database connection status.

**Response**:
```json
{
  "status": "healthy",
  "service": "Fake News Detection API",
  "ml_model_loaded": true,
  "version": "1.0.0"
}
```

#### ML Classification Only
```
POST /api/analyze/ml-only
```
Perform stylistic ML classification without evidence retrieval.

**Request**:
```json
{
  "headline": "Federal Reserve signals policy adjustment",
  "article_text": "WASHINGTON - Central bankers outlined their projections..."
}
```

**Response**:
```json
{
  "prediction": "REAL",
  "confidence": 0.954,
  "prob_fake": 0.046,
  "model": "TF-IDF + Logistic Regression",
  "char_count": 450,
  "word_count": 85,
  "analyzed_at": "2026-08-18T12:00:00Z"
}
```

#### Complete Analysis
```
POST /api/analyze/complete
```
Full end-to-end analysis: ML classification + claim extraction + evidence retrieval + verification.

**Request**:
```json
{
  "headline": "Federal Reserve signals policy adjustment",
  "article_text": "WASHINGTON - Central bankers outlined their projections..."
}
```

**Response**:
```json
{
  "analysis_id": "abc123-def456",
  "ml_analysis": {
    "prediction": "REAL",
    "confidence": 0.954,
    "prob_fake": 0.046
  },
  "verified_claims": [
    {
      "claim_id": "claim_1",
      "text": "Central bankers outlined their projections",
      "importance_score": 0.85,
      "verification": {
        "status": "SUPPORTED",
        "confidence": 0.92,
        "support_score": 0.92,
        "contradiction_score": 0.0
      }
    }
  ],
  "evidence_map": {
    "claim_1": [
      {
        "source": "Reuters",
        "snippet": "Federal Reserve officials stated...",
        "url": "https://example.com/article",
        "relevance_score": 0.88,
        "source_quality": 0.95,
        "provider": "web_search"
      }
    ]
  },
  "final_result": {
    "decision": "REAL",
    "confidence": 0.96,
    "predicted_at": "2026-08-18T12:00:00Z"
  },
  "decision_factors": {
    "supporting_claims": 3,
    "contradicted_claims": 0,
    "insufficient_claims": 1,
    "ml_confidence": 0.954,
    "evidence_strength": 0.89
  },
  "explanation": "Stylistic ML analysis evaluated the text as REAL (95% confidence). Supporting evidence was found for 3 key claims including 'Central bankers outlined their projections'. No contradicting evidence was identified."
}
```

#### URL Analysis
```
POST /api/analyze/url
```
Analyze a public article directly from its URL.

**Request**:
```json
{
  "url": "https://example.com/news/article-title"
}
```

**Response**: Same as complete analysis

#### Analysis History
```
GET /api/history
```
Retrieve previous analyses.

**Query Parameters**:
- `user_id` (optional): User identifier (default: "anonymous")
- `limit` (optional): Max results (default: 20)

**Response**:
```json
[
  {
    "analysis_id": "abc123",
    "headline": "Article headline",
    "final_decision": "REAL",
    "final_confidence": 0.96,
    "created_at": "2026-08-18T12:00:00Z"
  }
]
```

#### Model Metrics
```
GET /api/metrics
```
Retrieve ML model performance metrics.

**Response**:
```json
{
  "model": "TF-IDF + Logistic Regression",
  "accuracy": 0.9964,
  "precision": 0.9983,
  "recall": 0.9961,
  "f1_score": 0.9972,
  "roc_auc": 0.9995
}
```

**Full API documentation available at** `/docs` when backend is running (Swagger UI).

---

## Testing

### Run All Tests
```bash
pytest -q
```

### Run Specific Test File
```bash
pytest tests/test_backend_api.py -v
```

### Run with Coverage Report
```bash
pytest --cov=backend --cov=src tests/
```

### Test Modules Included

- **test_backend_api.py** - API endpoint integration
- **test_claim_extraction.py** - Claim extraction logic
- **test_cli_predict.py** - CLI inference
- **test_decision_and_verification.py** - Decision engine & verification
- **test_evaluation.py** - Metrics calculation
- **test_evidence_providers.py** - Evidence retrieval providers
- **test_model_compat.py** - Model serialization
- **test_pipeline.py** - ML pipeline integration
- **test_text_clean.py** - Text preprocessing
- **test_training_smoke_artifacts.py** - Training output validation

### Continuous Integration

GitHub Actions CI/CD runs on push and pull requests (`.github/workflows/ci.yml`):
- Dependency installation
- Source code compilation
- Full test suite execution
- Ruff linting
- Model training (smoke test)
- Artifact validation

---

## Building the Frontend for Production

```bash
cd frontend
npm run build
```

This creates an optimized production build in `frontend/dist/`. Serve this directory with a static HTTP server:

```bash
# Example with Python
cd frontend/dist
python -m http.server 3000

# Or with Node http-server
npx http-server frontend/dist -p 3000
```

Then access the application at http://localhost:3000.

---

## Deployment

### Quick Start (Development)

```bash
# Terminal 1: Backend API
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000

# Terminal 2: Frontend dev server
cd frontend && npm run dev

# Terminal 3 (optional): MongoDB
mongod --dbpath ./db_data
```

### Production Deployment

1. **Set Up Environment**
   - Ensure Python 3.10+ and Node.js are installed
   - Create `.env` file with production settings

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt backend/requirements.txt
   cd frontend && npm install && npm run build && cd ..
   ```

3. **Train/Verify ML Model**
   ```bash
   python src/train_model.py --real data/true.csv --fake data/fake.csv --outdir outputs
   ```

4. **Start Services**
   - **Backend**: `python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000`
   - **Frontend**: Serve `frontend/dist/` with a web server (nginx, Apache, etc.)
   - **Database**: Ensure MongoDB is running and accessible

5. **Verify Health**
   - Check `http://your-domain:8000/api/health`
   - Frontend should load at `http://your-domain`

### Note on Containerization

This project does not currently include Docker or Kubernetes configurations. For containerized deployment, you would need to:
- Create a `Dockerfile` for the backend (Python 3.10 base image)
- Create a `Dockerfile` for the frontend (Node build stage + nginx serving)
- Create a `docker-compose.yml` to orchestrate services and MongoDB

---

## Development Workflow

### Using Makefile

```bash
make install       # Install core dependencies
make install-dev   # Install dev dependencies
make train        # Train ML model
make test         # Run pytest
make lint         # Run ruff linter on src/ and tests/
make predict      # Example CLI prediction
```

### Code Quality

**Linting**:
```bash
ruff check src tests backend
```

**Auto-Fix**:
```bash
ruff check --fix src tests backend
```

**Configuration**: See `pyproject.toml` (line length: 100, target: Python 3.10+)

---

## Model Performance

**Holdout Test Set Accuracy**: **99.64%**

| Metric | Value |
|--------|-------|
| Accuracy | 99.64% |
| Precision (FAKE) | 99.83% |
| Recall (FAKE) | 99.61% |
| F1 Score (FAKE) | 99.72% |
| ROC-AUC | 99.95%+ |

**Dataset**: 38,829 deduplicated articles (20,929 REAL, 17,900 FAKE)

**Cross-Validation** (3-fold on training set):
- Accuracy: 99.21% ± 0.07%
- Macro F1: 99.20% ± 0.07%
- ROC-AUC: 99.94% ± 0.01%

---

## Data

### Training Datasets

Located in `data/`:
- **true.csv** (21,418 rows) - Real news articles
- **fake.csv** (23,490 rows) - Fake news articles

**Note**: Raw data contains 44,898 articles; after deduplication, 38,829 are used for training.

### Data Leakage Mitigation

The original dataset contains **Reuters wire-source artifacts** (e.g., "WASHINGTON (Reuters) -") that appear primarily in REAL articles. These are stripped during training (`text_clean.py`) to force the model to learn misinformation patterns rather than source markers.

See `outputs/leakage_report.json` for detailed leakage analysis.

---

## Troubleshooting

### Model Loading Fails

**Error**: "ML Service failed to load pipeline"

**Solutions**:
1. Verify `outputs/pipeline.joblib` exists
2. Ensure Python 3.10+ is installed
3. Check that scikit-learn and joblib are installed
4. Train a new model: `python src/train_model.py --real data/true.csv --fake data/fake.csv --outdir outputs`

### MongoDB Connection Error

**Message**: "MongoDB unavailable. Application will continue without persistence."

**Solutions**:
1. Start MongoDB: `mongod --dbpath ./db_data`
2. Verify connection string in `.env` (default: `mongodb://localhost:27017`)
3. App functions normally without DB; just no persistence

### CORS Errors in Browser

**Error**: "Cross-Origin Request Blocked"

**Solution**: Update `CORS_ORIGINS` in `.env` to include your frontend URL, then restart the backend.

### Evidence Provider Timeouts

**Solutions**:
1. Increase `EVIDENCE_TIMEOUT_SECONDS` in `.env`
2. Check internet connectivity
3. Verify API keys for configured providers
4. Note: One provider timeout doesn't block others (error isolation)

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Commit changes (`git commit -am 'Add my feature'`)
4. Push to the branch (`git push origin feature/my-feature`)
5. Open a pull request

**Code Quality**: All code must pass `ruff` linting and `pytest` tests.

---

## License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- Training data: Kaggle Fake and Real News Dataset
- Fact-checking providers: Google Fact Check Tools, Wikipedia
- ML framework: scikit-learn
- Web framework: FastAPI
- Frontend framework: React

---

## Citation

If you use this project in research or applications, please cite:

```bibtex
@software{factcheck_ai_2026,
  title={FactCheck AI: AI-Powered Fake News Detection and Multi-Source Verification},
  author={FactCheck AI Team},
  year={2026},
  url={https://github.com/your-org/Fake_News_Detection}
}
```

---

**Last Updated**: August 18, 2026  
**Version**: 1.0.0  
**Python**: 3.10+  
**Status**: Active Development
