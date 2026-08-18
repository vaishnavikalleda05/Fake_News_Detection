# Fake News Detection - Complete Project Analysis

**Project Name:** Fake News Detection  
**Version:** 1.0.0 (Backend), 0.3.0 (Data Science)  
**Architecture:** Full-Stack AI Application (Backend API + React Frontend + ML Pipeline)  
**Status:** Functional educational/hackathon project

---

## 1. PROJECT OVERVIEW

Fake News Detection is an **AI-powered fake news detection and claim verification system** that combines machine learning with multi-source evidence retrieval. It provides transparent FAKE/REAL assessments with confidence scores, verified claims, and supporting evidence.

### Core Capabilities

- **Analyze news** from article text or public URLs
- **ML Classification** using TF-IDF + Logistic Regression
- **Claim Extraction** to identify verifiable factual statements
- **Multi-Source Evidence Retrieval** from fact-check APIs, web search, and encyclopedias
- **Claim-Level Verification** comparing extracted claims against evidence
- **Hybrid Decision Engine** combining ML signals with evidence verification
- **Analysis History** persisted in MongoDB
- **Web Interface** for interactive analysis with React frontend

---

## 2. SYSTEM ARCHITECTURE

### 2.1 High-Level Data Flow

```
User Input (Headline + Article Text or URL)
    ↓
Article Extraction (if URL)
    ↓
[Parallel Processing]
├─→ ML Classification (TF-IDF + Logistic Regression)
├─→ Claim Extraction (heuristic sentence splitting + factuality indicators)
└─→ Evidence Retrieval (multi-source concurrent queries)
    ↓
Claim Verification (compare claims vs. evidence)
    ↓
Decision Engine (hybrid: ML + evidence weights)
    ↓
Explanation Generation (human-readable rationale)
    ↓
MongoDB Persistence (optional, if connected)
    ↓
Response to Frontend (JSON)
```

### 2.2 Technology Stack

**Backend:**
- FastAPI (async Python web framework)
- Uvicorn (ASGI server)
- Pydantic v2 (data validation & settings)
- scikit-learn (ML model)
- Motor (async MongoDB driver)
- httpx (async HTTP client)
- trafilatura (web article extraction)

**Frontend:**
- React 19.2.8 (UI framework)
- Vite 8.2.0 (build tool)
- React Router 7.18.2 (navigation)
- Axios (HTTP client)
- Lucide React (icons)

**Database:**
- MongoDB (document persistence of analyses)

**ML Pipeline:**
- TF-IDF vectorization (scikit-learn)
- Logistic Regression classifier
- Joblib serialization for model artifacts

**Utilities:**
- Python 3.10+ required
- Ruff (linter/formatter)
- pytest (testing framework)

---

## 3. DIRECTORY STRUCTURE & COMPONENTS

### 3.1 Root Directory

```
c:\Users\kalle\OneDrive\Desktop\Fake_News_Detection/
├── LICENSE                          # MIT License
├── Makefile                         # Build commands (train, test, lint, app, predict)
├── pyproject.toml                   # Project metadata & tool config (ruff, pytest)
├── README.md                        # Project documentation
├── requirements.txt                 # Core dependencies
├── requirements-dev.txt             # Dev dependencies (pytest, ruff)
├── requirements-lock.txt            # Locked dependency versions
├── data/                            # Training datasets
├── backend/                         # FastAPI backend application
├── frontend/                        # React SPA frontend
├── src/                             # ML/data science scripts
├── tests/                           # Test suite
├── docs/                            # Documentation
└── outputs/                         # ML artifacts & metrics
```

### 3.2 Backend (`backend/app/`)

**Main Application:**
- `main.py` - FastAPI app entry point with lifespan management (model & DB initialization)
- `config.py` - Settings management using Pydantic (CORS, MongoDB, model path, API keys)

**API Routes:**
- `api/routes_analysis.py` - `/api/analyze/*` endpoints (ML-only, complete analysis, URL analysis)
- `api/routes_feedback.py` - User feedback collection
- `api/routes_health.py` - Health check & status monitoring
- `api/routes_history.py` - Analysis history retrieval & deletion
- `api/routes_metrics.py` - ML model performance metrics

**Data Layer:**
- `models/schemas.py` - Pydantic models for request/response validation
- `database/connection.py` - MongoDB async connection management
- `database/repositories.py` - Data access layer (Analysis, Claim, Evidence repositories)

**Services (Business Logic):**
- `services/ml_service.py` - Loads and wraps the TF-IDF + LR pipeline for inference
- `services/claim_extractor.py` - Heuristic factual claim extraction (sentence splitting, filtering)
- `services/evidence_retriever.py` - Orchestrates multi-provider concurrent evidence queries
- `services/claim_verification_service.py` - Compares extracted claims against evidence
- `services/decision_engine.py` - Hybrid decision logic (35% ML + 65% evidence weights)
- `services/explanation_service.py` - Generates human-readable analysis rationales
- `services/source_scoring_service.py` - Evaluates source credibility
- `services/article_url_service.py` - Extracts article text from URLs using trafilatura
- `services/evidence_analyzer.py` - Analyzes evidence relevance and stance
- `services/evidence_aggregation_service.py` - Aggregates multi-source evidence

**Evidence Providers:**
- `providers/base_provider.py` - Abstract base class & utility functions (relevance scoring)
- `providers/google_factcheck.py` - Integrates Google Fact Check Tools API
- `providers/web_search.py` - Generic web search provider
- `providers/wikipedia_provider.py` - Wikipedia knowledge base queries

**Utilities:**
- `utils/logger.py` - Structured logging configuration

### 3.3 Frontend (`frontend/`)

**Entry Points:**
- `index.html` - HTML template
- `main.jsx` - React entry point
- `App.jsx` - Main component with router setup (Navbar, Dashboard, Analyze pages)

**Pages:**
- `pages/Analyze.jsx` - Main news analysis interface
- `pages/Dashboard.jsx` - Model performance metrics display (accuracy, precision, recall, F1)

**Services:**
- `services/api.js` - Axios-based API client for backend communication

**Styling:**
- `index.css` - Global styles

### 3.4 ML/Data Science (`src/`)

**Core Scripts:**
- `train_model.py` - Model training pipeline (TF-IDF + Logistic Regression)
  - Data loading, deduplication, stratified split
  - 3-fold cross-validation on training set
  - Evaluation metrics & visualization
  - Artifact serialization (model, vectorizer, pipeline)

- `detect_fake_news.py` - CLI prediction interface
- `evaluation.py` - Evaluation metrics & analysis (ROC-AUC, confusion matrix, etc.)
- `model_compat.py` - Model serialization with checksums & compatibility layer
- `text_clean.py` - Text preprocessing (removes Reuters datelines/mentions to prevent leakage)

### 3.5 Tests (`tests/`)

- `test_backend_api.py` - FastAPI integration tests (endpoints, health checks, ML inference)
- `test_claim_extraction.py` - Claim extraction unit tests
- `test_cli_predict.py` - CLI interface tests
- `test_decision_and_verification.py` - Decision engine & verification logic
- `test_evaluation.py` - Metrics evaluation tests
- `test_evidence_providers.py` - Evidence provider tests
- `test_model_compat.py` - Model serialization & checksum tests
- `test_pipeline.py` - End-to-end pipeline tests
- `test_text_clean.py` - Text cleaning unit tests
- `test_training_smoke_artifacts.py` - Artifact integrity tests

### 3.6 Outputs (`outputs/`)

**ML Artifacts:**
- `pipeline.joblib` - Serialized TF-IDF + Logistic Regression pipeline
- `pipeline.joblib.sha256` - Checksum for artifact integrity verification
- `model.joblib` - Trained model object
- `vectorizer.joblib` - Fitted TF-IDF vectorizer

**Metrics & Analysis:**
- `metrics.json` - Model performance metrics (accuracy, precision, recall, F1, ROC-AUC)
- `data_profile.json` - Dataset statistics & deduplication report
- `holdout_predictions.csv` - Test set predictions
- `artifact_environment.json` - Environment details (Python version, dependencies)
- `leakage_report.json` - Data leakage analysis (Reuters artifact detection)
- `source_confounding_report.json` - Confounding variable analysis

---

## 4. DATA

### 4.1 Training Datasets

Located in `data/`:
- **true.csv** - 21,418 real news articles (REAL class)
- **fake.csv** - 23,490 fake news articles (FAKE class)

**Original Dataset:** 44,908 rows
**After Deduplication:** 38,829 rows (6,069 duplicates removed)
**Final Distribution:** 20,929 REAL, 17,900 FAKE

### 4.2 Data Columns

Typically contain:
- `title` / `headline` - Article headline
- `text` - Article body
- `label` - Classification (REAL/FAKE)
- `date` - Publication date (optional)
- `subject` - Topic category (optional)

### 4.3 Data Quality Issues

**Leakage Control:**
- Dataset contains Reuters dateline artifacts in REAL articles ("WASHINGTON (Reuters) -")
- Almost no FAKE articles have Reuters mentions
- **Mitigation:** `text_clean.py` strips these artifacts to force the model to learn misinformation signals rather than wire-source patterns
- **Analysis:** `leakage_report.json` documents this issue

---

## 5. MACHINE LEARNING MODEL

### 5.1 Architecture

**Pipeline:** TF-IDF Vectorizer → Logistic Regression

**TF-IDF Configuration:**
- Extracts text features using term frequency-inverse document frequency
- Vectorizes combined text: `"{headline} {article_text}"`
- Scikit-learn default parameters with customizable hyperparameters

**Logistic Regression:**
- Binary classifier (FAKE vs REAL)
- Probability threshold: 0.5
- Generates confidence scores (0.0 to 1.0)

### 5.2 Training Protocol

**Data Split:**
- 80% training, 20% holdout test (stratified by class)

**Validation:**
- 3-fold StratifiedKFold cross-validation on **training split only** (not test)
- Prevents test set leakage

**Text Preprocessing:**
```
Raw Text
  ↓
Normalize (lowercase, remove extra whitespace)
  ↓
Remove URLs, emails, non-ASCII characters
  ↓
Strip Reuters artifacts (datelines, mentions)
  ↓
Custom TextCleaner transformer (Sklearn-compatible)
  ↓
TF-IDF Vectorization
  ↓
Logistic Regression Prediction
```

### 5.3 Performance Metrics

**Cross-Validation (Train Only):**
- Accuracy: 99.21% ± 0.07%
- Macro F1: 99.20% ± 0.07%
- ROC-AUC: 99.94% ± 0.01%

**Holdout Test Set:**
- Accuracy: 99.64%
- Precision (FAKE): 99.83%
- Recall (FAKE): 99.61%
- F1 (FAKE): 99.72%
- ROC-AUC: ~99%+

**Training Set:**
- Accuracy: 99.74%

### 5.4 Model Artifacts

All serialized with Joblib and checksummed for integrity:
- `pipeline.joblib` - Complete sklearn Pipeline object
- `model.joblib` - Logistic Regression classifier
- `vectorizer.joblib` - Fitted TF-IDF vectorizer
- `*.sha256` - SHA256 checksum files

**Serialization:** `model_compat.py` handles loading with compatibility checks

---

## 6. BACKEND API

### 6.1 Endpoints

**Health & Status:**
- `GET /` - Service info & documentation links
- `GET /api/health` - Health check (ML model loaded, DB connected)
- `GET /api/metrics` - Model performance metrics

**News Analysis:**
- `POST /api/analyze/ml-only` - ML classification only
  - Input: `{ headline, article_text }`
  - Output: ML prediction + confidence + probabilities

- `POST /api/analyze/complete` - Full end-to-end analysis
  - Input: `{ headline, article_text }`
  - Output: ML analysis + extracted claims + verified claims + final decision + explanation

- `POST /api/analyze/url` - Analyze article from URL
  - Input: `{ url }`
  - Extracts article text → runs complete analysis

**History Management:**
- `GET /api/history` - Retrieve previous analyses (paginated)
- `GET /api/history/{analysis_id}` - Get specific analysis details
- `DELETE /api/history/{analysis_id}` - Delete analysis record

**Feedback:**
- `POST /api/feedback` - User feedback on analysis results

### 6.2 Request/Response Schema

**MLAnalyzeRequest:**
```json
{
  "headline": "string (optional, non-empty)",
  "article_text": "string (optional, non-empty)"
}
```

**MLAnalyzeResponse:**
```json
{
  "prediction": "FAKE | REAL",
  "confidence": 0.0-1.0,
  "prob_fake": 0.0-1.0,
  "model": "TF-IDF + Logistic Regression",
  "char_count": 0,
  "word_count": 0,
  "analyzed_at": "ISO8601 timestamp"
}
```

**CompleteAnalysisRequest:**
```json
{
  "headline": "string (optional)",
  "article_text": "string (optional)"
}
```

**CompleteAnalysisResponse:**
```json
{
  "analysis_id": "uuid",
  "ml_analysis": { /* MLAnalysisSummary */ },
  "verified_claims": [ /* ClaimItem[] */ ],
  "evidence_map": { /* claim_id → EvidenceItem[] */ },
  "final_result": {
    "decision": "FAKE | REAL",
    "confidence": 0.0-1.0,
    "predicted_at": "ISO8601"
  },
  "explanation": "string (human-readable rationale)"
}
```

### 6.3 CORS Configuration

Default allowed origins (configurable via `.env`):
- `http://localhost:5173` (Vite dev server)
- `http://127.0.0.1:5173`
- `http://localhost:3000` (alternative dev)
- `http://127.0.0.1:3000`

### 6.4 Configuration (Settings)

Loaded from `config.py` and `.env` files:

```python
PROJECT_NAME = "Fake News Detection API"
VERSION = "1.0.0"
API_PREFIX = "/api"

# Model
MODEL_PATH = "outputs/pipeline.joblib"

# Server
HOST = "127.0.0.1"
PORT = 8000
DEBUG = False

# Database
MONGODB_URI = "mongodb://localhost:27017"
MONGODB_DATABASE = "fake_news_detection"

# Evidence Providers (optional API keys)
GOOGLE_FACTCHECK_API_KEY = None
TAVILY_API_KEY = None
SERPAPI_API_KEY = None
BING_SEARCH_API_KEY = None

# Limits
EVIDENCE_TIMEOUT_SECONDS = 5.0
MAX_CLAIMS_PER_ANALYSIS = 5
MAX_EVIDENCE_PER_CLAIM = 5
```

---

## 7. FRONTEND APPLICATION

### 7.1 Page Structure

**Navbar (Global):**
- Fake News Detection branding
- Navigation links (Dashboard, Analyze)
- Icons from Lucide React

**Dashboard (`/`):**
- Displays ML model performance metrics
- Shows accuracy, precision, recall, F1 score
- Fetches `/api/metrics` on mount

**Analyze (`/analyze`):**
- Main interface for news analysis
- Input forms for:
  - Headline
  - Article text
  - URL input
- Tabs for different analysis modes
- Results display:
  - Final decision (FAKE/REAL) with confidence
  - Extracted claims with verification status
  - Supporting evidence with source links
  - Human-readable explanation
  - Analysis metadata (timestamps, etc.)

### 7.2 API Client (`services/api.js`)

Axios-based wrapper for backend endpoints:
- `analyzeML()` - Call ML-only endpoint
- `analyzeComplete()` - Full analysis
- `analyzeURL()` - Analyze from URL
- `getHistory()` - Fetch analysis history
- `getAnalysis()` - Retrieve specific analysis
- `deleteAnalysis()` - Delete previous analysis
- `getModelMetrics()` - Fetch model performance metrics

### 7.3 Build & Development

**Package Scripts:**
- `npm run dev` - Start Vite dev server (http://localhost:5173)
- `npm run build` - Production build
- `npm run lint` - Lint with oxlint
- `npm run preview` - Preview production build

---

## 8. EVIDENCE RETRIEVAL SYSTEM

### 8.1 Multi-Source Architecture

Three concurrent evidence providers (async):

**Google Fact Check Tools API:**
- Searches verified claims from professional fact-checkers
- Requires API key (optional)
- Provides fact-check ratings and citations

**Web Search Provider:**
- Generic web search (via configured API if available)
- Falls back to query-based results

**Wikipedia Provider:**
- Queries Wikipedia for encyclopedic information
- No API key required (public)
- Custom user-agent for compliance

### 8.2 Claim Extraction Flow

1. **Sentence Segmentation:** Split text into sentences while protecting abbreviations
2. **Boilerplate Filtering:** Remove navigation, ads, greetings
3. **Factuality Detection:** Identify sentences with factual indicators:
   - Action verbs: "announced", "reported", "discovered", "passed", etc.
   - Numeric facts: percentages, dollar amounts, years
4. **Deduplication:** Merge near-duplicate claims (token-based normalization)
5. **Importance Scoring:** Weight claims by occurrence frequency and keyword specificity
6. **Limiting:** Return max N claims (default: 5, configurable)

### 8.3 Evidence Retrieval Flow

For each claim:
1. **Concurrent Queries:** Launch all active providers simultaneously
2. **Aggregation:** Combine results from all providers
3. **Deduplication:** Remove duplicate/near-duplicate evidence by URL and content
4. **Ranking:** Sort by relevance score (lexical overlap with claim)
5. **Limiting:** Return max M evidence items (default: 5, configurable)
6. **Relevance Scoring:** 
   - Tokenize claim and evidence title/snippet
   - Filter stopwords
   - Compute Jaccard similarity
   - Normalize to 0.0-1.0 range

### 8.4 Claim Verification

For each claim + evidence pair:
1. **Stance Classification:** Determine if evidence supports, contradicts, or is insufficient
2. **Relevance Scoring:** How relevant is the evidence to the claim?
3. **Source Quality:** Score source credibility
4. **Confidence:** Aggregate stance probability
5. **Status Assignment:** Map to SUPPORTED/CONTRADICTED/INSUFFICIENT

---

## 9. DECISION ENGINE

### 9.1 Hybrid Decision Logic

Combines ML baseline with evidence verification:

**Weights:**
- ML Component: 35%
- Evidence Component: 65%

**ML Signal:**
- Converts `prob_fake` to "realness" score: `1.0 - prob_fake`
- Maps to 0.0 (fake style) to 1.0 (real style)

**Evidence Signal:**
- Per claim:
  - SUPPORTED → confidence score (e.g., 0.85)
  - CONTRADICTED → (1.0 - confidence) (inverted)
  - INSUFFICIENT → 0.50 (neutral)
- Weighted average by claim importance scores
- Final evidence "realness" score: 0.0 to 1.0

**Final Decision:**
```
Combined Score = 0.35 * ML_Signal + 0.65 * Evidence_Signal

if Combined_Score >= 0.5:
    Decision = "REAL"
else:
    Decision = "FAKE"
```

**Confidence Calculation:**
- Distance from threshold (0.5)
- Adjusted by evidence strength
- Clipped to 0.5-1.0 range for confidence reporting

### 9.2 Decision Factors

Persisted/returned for transparency:
- Supporting claims (count)
- Contradicted claims (count)
- Insufficient evidence claims (count)
- ML confidence
- Evidence strength metric
- Average support/contradiction scores

---

## 10. MONGODB PERSISTENCE

### 10.1 Data Model

**Collections:**

**analyses:**
```javascript
{
  "_id": ObjectId,
  "analysis_id": "uuid",
  "user_id": "anonymous | user_id",
  "headline": "string",
  "article_text": "string",
  "url": "string | null",
  
  // ML Analysis
  "ml_prediction": "FAKE | REAL",
  "ml_confidence": 0.0-1.0,
  "ml_prob_fake": 0.0-1.0,
  
  // Extracted Claims
  "claims": [ { claim_id, text, importance_score, ... } ],
  
  // Verified Claims
  "verified_claims": [ { claim_id, claim_text, verification, ... } ],
  
  // Evidence Mapping
  "evidence_map": { claim_id: [ { source, snippet, url, relevance_score, ... } ] },
  
  // Final Decision
  "final_decision": "FAKE | REAL",
  "final_confidence": 0.0-1.0,
  "decision_factors": { supporting_claims, contradicted_claims, ... },
  
  // Explanation
  "explanation": "string",
  
  "created_at": ISODate,
  "updated_at": ISODate
}
```

**claims** (optional normalized collection):
```javascript
{
  "_id": ObjectId,
  "claim_id": "string",
  "analysis_id": "string",
  "text": "string",
  "importance_score": 0.0-1.0,
  "created_at": ISODate
}
```

**evidence** (optional normalized collection):
```javascript
{
  "_id": ObjectId,
  "evidence_id": "string",
  "claim_id": "string",
  "analysis_id": "string",
  "source": "string",
  "snippet": "string",
  "url": "string",
  "relevance_score": 0.0-1.0,
  "source_quality": 0.0-1.0,
  "provider": "google_factcheck | web_search | wikipedia",
  "created_at": ISODate
}
```

### 10.2 Repositories

**AnalysisRepository:**
- `create(document)` - Insert analysis
- `get_by_id(analysis_id)` - Retrieve full analysis
- `get_history(user_id, limit)` - List previous analyses
- `delete(analysis_id)` - Remove analysis

**ClaimRepository:**
- CRUD operations on claims (optional normalization)

**EvidenceRepository:**
- CRUD operations on evidence (optional normalization)

### 10.3 Graceful Degradation

- If MongoDB unavailable, app continues without persistence
- All analysis logic runs normally
- Results returned but not stored
- Warning logged to indicate DB status

---

## 11. TESTING STRATEGY

### 11.1 Test Coverage

**Unit Tests:**
- `test_text_clean.py` - Text preprocessing
- `test_model_compat.py` - Serialization & checksums
- `test_claim_extraction.py` - Claim extraction logic
- `test_evidence_providers.py` - Provider functionality

**Integration Tests:**
- `test_backend_api.py` - API endpoint integration
- `test_pipeline.py` - End-to-end ML pipeline
- `test_decision_and_verification.py` - Decision engine logic
- `test_evaluation.py` - Metrics calculation

**Smoke Tests:**
- `test_training_smoke_artifacts.py` - Artifact integrity
- `test_cli_predict.py` - CLI interface

### 11.2 Running Tests

```bash
# All tests
pytest -q

# Specific file
pytest tests/test_backend_api.py -v

# With coverage (if installed)
pytest --cov=backend --cov=src tests/
```

---

## 12. DEPLOYMENT & RUNNING

### 12.1 Training the Model

```bash
# Prerequisites
pip install -r requirements.txt

# Train
python src/train_model.py \
  --real data/true.csv \
  --fake data/fake.csv \
  --outdir outputs

# Outputs: pipeline.joblib, metrics.json, visualizations, etc.
```

### 12.2 Running Backend Server

```bash
# Install dependencies
pip install -r backend/requirements.txt

# Start FastAPI server
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000

# Swagger UI: http://localhost:8000/docs
# ReDoc: http://localhost:8000/redoc
```

**Environment Variables (.env):**
```
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=fake_news_detection
GOOGLE_FACTCHECK_API_KEY=your_key_here
TAVILY_API_KEY=your_key_here
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

### 12.3 Running Frontend

```bash
# Install dependencies
cd frontend
npm install

# Development server
npm run dev
# Navigate to http://localhost:5173

# Production build
npm run build
# Output in frontend/dist/
```

### 12.4 CLI Inference

```bash
python src/detect_fake_news.py \
  --text "Reuters reported that lawmakers passed a new budget bill."
```

---

## 13. KEY FEATURES & DESIGN DECISIONS

### 13.1 Strengths

1. **Comprehensive Pipeline:**
   - ML baseline + multi-source evidence retrieval
   - Avoids over-reliance on single signal

2. **Explainability:**
   - Decision factors & reasoning
   - Human-readable explanations
   - Evidence citations with source URLs

3. **Scalability:**
   - Async/concurrent provider queries
   - MongoDB for historical persistence
   - Efficient TF-IDF + Logistic Regression (fast inference)

4. **Resilience:**
   - Error isolation (provider failures don't crash pipeline)
   - Graceful DB degradation
   - Timeout protection on external queries

5. **Data Quality:**
   - Leakage detection & mitigation
   - Artifact stripping (Reuters patterns)
   - Deduplication in training & analysis

6. **Transparent Evaluation:**
   - Honest validation (train/test split + CV)
   - Cross-validation only on training set
   - Confusion matrices, ROC curves, metrics

### 13.2 Design Decisions

1. **Evidence Weight > ML Weight:**
   - 65% evidence vs 35% ML
   - Prioritizes external verification over stylistic patterns
   - Reduces over-reliance on potentially biased ML model

2. **Heuristic Claim Extraction:**
   - No LLM/NLP models (lightweight, deterministic)
   - Rule-based filtering (boilerplate, questions)
   - Factuality indicators (action verbs, numbers)

3. **Multi-Provider Approach:**
   - Reduces single-source bias
   - Redundancy & reliability
   - Concurrent async queries

4. **No Source Artifacts in Production:**
   - Reuters strips applied during training for honest evaluation
   - Prevents false confidence in fake news detectors

5. **Stratified Train/Test Split:**
   - Preserves class distribution
   - Cross-validation on training only
   - Prevents overfitting estimates

---

## 14. LIMITATIONS & FUTURE IMPROVEMENTS

### 14.1 Current Limitations

1. **No Real-Time Updates:** Training data is static (2019-era articles)
2. **No Fine-Tuning:** Can't adapt to new fake news patterns
3. **Limited Claim Extraction:** Heuristic-based, not ML-based
4. **Evidence Quality:** Depends on API availability & quality
5. **Language:** English-only text processing
6. **Semantic Understanding:** TF-IDF lacks semantic nuance
7. **No User Feedback Loop:** Analyses not used for model improvement

### 14.2 Potential Improvements

1. **Advanced NLP:**
   - Use transformer-based models (BERT, RoBERTa) for classification
   - Neural claim extraction with fine-tuned language models
   - Semantic similarity for evidence matching

2. **Ensemble Methods:**
   - Combine multiple classifiers
   - Weight by domain-specific performance
   - Adaptive confidence intervals

3. **Real-Time Updates:**
   - Scheduled retraining on new data
   - Online learning / incremental updates
   - Concept drift detection

4. **Feedback Loop:**
   - User corrections to claims/verification
   - Expert annotations on edge cases
   - Active learning for high-uncertainty cases

5. **Multilingual Support:**
   - Translate or train models for multiple languages
   - Cross-lingual transfer learning

6. **Explainability Tools:**
   - SHAP values for feature importance
   - Attention visualizations for claim extraction
   - Interactive explanation dashboards

7. **Performance Optimization:**
   - Model compression / quantization
   - Caching for repeated claims
   - Batch processing for multiple articles

---

## 15. DEVELOPMENT WORKFLOW

### 15.1 Makefile Commands

```bash
make install          # Install core dependencies
make install-dev      # Install dev dependencies
make train            # Train ML model
make test             # Run test suite
make lint             # Lint code (ruff)
make app              # Run Streamlit app (deprecated)
make predict          # CLI prediction example
```

### 15.2 Code Style & Quality

**Linting:**
```bash
ruff check src tests backend --line-length 100
```

**Target Version:** Python 3.10+

**Standards:**
- Ruff rules: E (errors), F (pyflakes), I (isort), UP (upgrades), B (flake8-bugbear)
- Ignore E501 (line length) - handled separately
- Line length limit: 100 characters

---

## 16. CONFIGURATION & ENVIRONMENT

### 16.1 Environment Variables

Load order: `.env` → `backend/.env` → defaults in `config.py`

```
# Server
HOST=127.0.0.1
PORT=8000
DEBUG=False

# Paths
MODEL_PATH=outputs/pipeline.joblib

# Database
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=fake_news_detection

# API Keys (optional, for evidence providers)
GOOGLE_FACTCHECK_API_KEY=
TAVILY_API_KEY=
SERPAPI_API_KEY=
BING_SEARCH_API_KEY=

# CORS
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000

# Extraction & Verification Limits
EVIDENCE_TIMEOUT_SECONDS=5.0
MAX_CLAIMS_PER_ANALYSIS=5
MAX_EVIDENCE_PER_CLAIM=5
WIKIPEDIA_USER_AGENT=FakeNewsDetectionFactChecker/1.0 (email@example.com)
```

### 16.2 Project Discovery

`config.py` automatically finds project root by locating `outputs/` and `src/` directories, ensuring portability across environments.

---

## 17. PROJECT METRICS & STATISTICS

### 17.1 Codebase

- **Language Breakdown:**
  - Python (backend + ML): ~8,000 LOC
  - JavaScript/JSX (frontend): ~1,500 LOC
  - JSON/YAML config: ~500 LOC

- **Files:**
  - Backend modules: 20+
  - Frontend components: 5+
  - Test files: 10+

### 17.2 Model Performance

- **Holdout Accuracy:** 99.64%
- **Precision:** 99.83%
- **Recall:** 99.61%
- **F1 Score:** 99.72%
- **ROC-AUC:** ~99%+
- **Cross-Validation:** 99.21% ± 0.07% (train only)

### 17.3 Data

- **Total Samples:** 44,898
- **After Deduplication:** 38,829
- **REAL Articles:** 20,929 (53.8%)
- **FAKE Articles:** 17,900 (46.2%)

---

## 18. API DOCUMENTATION

### 18.1 Auto-Generated Docs

- **Swagger UI:** `GET /docs`
- **ReDoc:** `GET /redoc`
- **OpenAPI Schema:** `GET /openapi.json`

### 18.2 Example Requests

**ML-Only Analysis:**
```bash
curl -X POST "http://localhost:8000/api/analyze/ml-only" \
  -H "Content-Type: application/json" \
  -d '{
    "headline": "Breaking: New Climate Agreement Signed",
    "article_text": "WASHINGTON - Officials announced a landmark climate accord..."
  }'
```

**Complete Analysis:**
```bash
curl -X POST "http://localhost:8000/api/analyze/complete" \
  -H "Content-Type: application/json" \
  -d '{
    "headline": "Breaking: New Climate Agreement Signed",
    "article_text": "WASHINGTON - Officials announced a landmark climate accord..."
  }'
```

**URL Analysis:**
```bash
curl -X POST "http://localhost:8000/api/analyze/url" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/news/article"
  }'
```

---

## 19. TROUBLESHOOTING & COMMON ISSUES

### 19.1 Model Loading Issues

**Error:** "ML Service failed to load pipeline"

**Solutions:**
1. Verify `outputs/pipeline.joblib` exists
2. Check Python version (3.10+ required)
3. Ensure scikit-learn, joblib installed
4. Verify checksum: `outputs/pipeline.joblib.sha256`

### 19.2 MongoDB Connection Issues

**Error:** "MongoDB unavailable. Application will continue without persistence."

**Solutions:**
1. Start MongoDB: `mongod --dbpath /path/to/db`
2. Verify connection string in `.env`
3. Check if MongoDB server is running on port 27017
4. App continues gracefully without DB

### 19.3 CORS Errors

**Error:** Cross-Origin requests blocked

**Solutions:**
1. Add frontend URL to `CORS_ORIGINS` in `.env`
2. Restart backend server
3. Verify frontend dev server URL matches configuration

### 19.4 Evidence Provider Timeouts

**Error:** Evidence retrieval times out

**Solutions:**
1. Increase `EVIDENCE_TIMEOUT_SECONDS` in `.env`
2. Check internet connectivity
3. Verify API keys for configured providers
4. One provider timeout doesn't block others (error isolation)

---

## 20. CONCLUSION

Fake News Detection is a **sophisticated, production-ready educational project** demonstrating:
- **Full-stack development** (backend API + frontend SPA)
- **ML engineering** (honest evaluation, artifact control, leakage prevention)
- **Explainable AI** (decision factors, evidence citations, human-readable explanations)
- **Scalable architecture** (async concurrency, multi-source resilience, graceful degradation)
- **Data science best practices** (stratified splits, CV-on-train-only, confusion matrices)

**Ideal for:**
- Educational demonstrations
- Hackathon showcases
- Portfolio projects
- Foundation for production fake news detection systems

---

**Project Last Updated:** 2026-08-18  
**Maintainer:** Fake News Detection Team  
**License:** MIT
