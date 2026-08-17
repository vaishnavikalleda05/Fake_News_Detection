import axios from "axios";

const API_BASE_URL = "http://127.0.0.1:8000/api";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// ============================================================
// TEXT ARTICLE ANALYSIS
// ============================================================

export async function analyzeArticle(headline, articleText) {
  const response = await api.post("/analyze", {
    headline,
    article_text: articleText,
  });

  return response.data;
}

// ============================================================
// URL ARTICLE ANALYSIS
// ============================================================

export async function analyzeArticleUrl(url) {
  const response = await api.post("/analyze/url", {
    url,
  });

  return response.data;
}

// ============================================================
// ANALYSIS HISTORY
// ============================================================

export async function getAnalysisHistory(
  userId = "anonymous",
  limit = 20,
) {
  const response = await api.get("/history", {
    params: {
      user_id: userId,
      limit,
    },
  });

  return response.data;
}

export async function getAnalysisById(analysisId) {
  const response = await api.get(`/history/${analysisId}`);

  return response.data;
}

export async function deleteAnalysis(analysisId) {
  const response = await api.delete(`/history/${analysisId}`);

  return response.data;
}

// ============================================================
// MODEL PERFORMANCE METRICS
// ============================================================

export async function getModelMetrics() {
  const response = await api.get("/metrics");
  return response.data;
}

// ============================================================
// FEEDBACK
// ============================================================

export async function submitFeedback(
  analysisId,
  helpful,
  comment = null,
  userId = "anonymous",
) {
  const response = await api.post("/feedback", {
    analysis_id: analysisId,
    helpful,
    comment,
    user_id: userId,
  });

  return response.data;
}

export default api;