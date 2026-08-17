# FactCheck AI
### AI-Powered Fake News Detection & Multi-Source Verification

FactCheck AI is a full-stack AI-powered fake news detection and news verification system.

It combines machine learning, factual claim extraction, multi-source evidence retrieval, claim-level verification, and a hybrid decision engine to provide transparent REAL/FAKE/UNCERTAIN assessments with confidence scores and supporting evidence.

---

## 1. Project Overview

FactCheck AI allows users to analyze news articles in two ways:

- Article text
- Public article URL

The system processes the submitted content through multiple analysis stages:

1. Machine Learning Classification
2. Factual Claim Extraction
3. Multi-Source Evidence Retrieval
4. Claim-Level Verification
5. Source Scoring
6. Hybrid Decision Engine
7. Human-Readable Explanation
8. MongoDB Persistence

Users can also review previous analyses through the Analysis History page.

---

## 2. Key Features

### Article Analysis

- Analyze news using headline and article text.
- Analyze a publicly accessible news article directly from its URL.
- Validate empty and invalid inputs.
- Handle inaccessible webpages gracefully.

### Machine Learning

- TF-IDF text feature extraction.
- Logistic Regression classification.
- Fake-news probability estimation.
- Confidence scoring.
- REAL / FAKE decision output.

### Claim Verification

- Automatically extract factual claims.
- Retrieve evidence for extracted claims.
- Compare claims against retrieved sources.
- Classify claim-level verification status.
- Calculate relevance and source-quality scores.

### Evidence Analysis

Each evidence source can include:

- Source name
- Source type
- Provider
- Article snippet
- Relevance score
- Source quality score
- Stance
- External source URL

Users can open evidence sources directly from the results page.

### Explainable Results

The system provides:

- Final decision
- Confidence percentage
- Claims analyzed
- Evidence items
- Verification summary
- Decision factors
- Human-readable explanation

### Analysis History

Completed analyses are stored in MongoDB.

Users can:

- View previous analyses
- Open complete saved results
- Review claims and evidence
- Delete previous analyses

---

## 3. System Architecture

```text
                    FACTCHECK AI
                         |
              +----------+----------+
              |                     |
        Article Text           Article URL
              |                     |
              +----------+----------+
                         |
                         v
                 React Frontend
                         |
                         v
                  FastAPI Backend
                         |
          +--------------+--------------+
          |              |              |
          v              v              v
        ML Model     Claim Extraction  URL Extraction
          |              |
          |              v
          |       Evidence Retrieval
          |              |
          |              v
          |       Claim Verification
          |              |
          +------+-------+
                 |
                 v
          Hybrid Decision Engine
                 |
        +--------+--------+
        |                 |
        v                 v
   Final Decision     Explanation
        |
        v
      MongoDB
        |
        v
   Analysis History