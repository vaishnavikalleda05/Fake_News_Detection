import { useEffect, useState } from "react";
import {
  AlertCircle,
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  ExternalLink,
  FileText,
  Info,
  Search,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  XCircle,
} from "lucide-react";

import {
  analyzeArticle,
  analyzeArticleUrl,
  getAnalysisById,
} from "../services/api";

function getDecisionInfo(decision) {
  const normalized = String(decision || "").toUpperCase();

  if (
    normalized === "REAL" ||
    normalized === "TRUE" ||
    normalized === "SUPPORTED"
  ) {
    return {
      label: "REAL",
      description: "The available analysis supports this content.",
      className: "decision-positive",
      icon: CheckCircle2,
    };
  }

  if (
    normalized === "FAKE" ||
    normalized === "FALSE" ||
    normalized === "CONTRADICTED"
  ) {
    return {
      label: "FAKE",
      description:
        "The machine-learning analysis indicates that this content may be unreliable.",
      className: "decision-negative",
      icon: ShieldAlert,
    };
  }

  return {
    label: "FAKE",
    description:
      "The analysis indicates that this content may be unreliable.",
    className: "decision-negative",
    icon: ShieldAlert,
  };
}

function getVerificationInfo(status) {
  const normalized = String(status || "").toUpperCase();

  if (normalized === "SUPPORTED") {
    return {
      className: "verification-supported",
      icon: CheckCircle2,
    };
  }

  if (normalized === "CONTRADICTED") {
    return {
      className: "verification-contradicted",
      icon: XCircle,
    };
  }

  return {
    className: "verification-insufficient",
    icon: Info,
  };
}

function formatPercentage(value) {
  const number = Number(value);

  if (!Number.isFinite(number)) {
    return "0%";
  }

  return `${(number * 100).toFixed(1)}%`;
}

function formatDate(value) {
  if (!value) {
    return "Not available";
  }

  try {
    return new Date(value).toLocaleString();
  } catch {
    return String(value);
  }
}

function ConfidenceMeter({ confidence }) {
  const percentage = Math.max(
    0,
    Math.min(100, Number(confidence || 0) * 100),
  );

  const radius = 62;
  const circumference = 2 * Math.PI * radius;
  const offset =
    circumference - (percentage / 100) * circumference;

  return (
    <div className="confidence-meter">
      <svg
        className="confidence-ring"
        viewBox="0 0 160 160"
      >
        <circle
          className="confidence-ring-background"
          cx="80"
          cy="80"
          r={radius}
        />

        <circle
          className="confidence-ring-progress"
          cx="80"
          cy="80"
          r={radius}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
        />
      </svg>

      <div className="confidence-value">
        <strong>{percentage.toFixed(1)}%</strong>
        <span>confidence</span>
      </div>
    </div>
  );
}

function Analyze() {
  const [inputMode, setInputMode] = useState("text");


  const [articleText, setArticleText] = useState("");
  const [articleUrl, setArticleUrl] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  // Load an existing analysis when opened from History
  useEffect(() => {
    const params = new URLSearchParams(
      window.location.search,
    );

    const analysisId = params.get("analysis_id");

    if (!analysisId) {
      return;
    }

    const loadSavedAnalysis = async () => {
      try {
        setLoading(true);
        setError("");

        const data = await getAnalysisById(analysisId);

        setResult(data);
      } catch (err) {
        console.error(
          "Failed to load saved analysis:",
          err,
        );

        setError(
          err.response?.data?.detail ||
            "Unable to load this saved analysis.",
        );
      } finally {
        setLoading(false);
      }
    };

    loadSavedAnalysis();
  }, []);



  const handleAnalyze = async (event) => {
  event.preventDefault();

  setError("");
  setResult(null);

  // URL mode
  if (inputMode === "url") {
    if (!articleUrl.trim()) {
      setError("Please enter a news article URL.");
      return;
    }

    setLoading(true);

    try {
      const data = await analyzeArticleUrl(articleUrl.trim());
      setResult(data);
    } catch (err) {
      console.error("URL analysis failed:", err);

      if (err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else {
        setError(
          "Unable to analyze this URL. Make sure the article is publicly accessible and the FastAPI server is running.",
        );
      }
    } finally {
      setLoading(false);
    }

    return;
  }

  // Text mode
  if (!articleText.trim()) {
  setError("Please enter the article text.");
  return;
}

  setLoading(true);

  try {
    const data = await analyzeArticle(
  articleText.trim(),
);

    setResult(data);
  } catch (err) {
    console.error("Analysis failed:", err);

    if (err.response?.data?.detail) {
      setError(err.response.data.detail);
    } else {
      setError(
        "Unable to connect to the Fake News Detection API. Make sure the FastAPI server is running.",
      );
    }
  } finally {
    setLoading(false);
  }
};

  const handleAnalyzeAnother = () => {
    setResult(null);
    setError("");
setArticleText("");
setArticleUrl("");
setInputMode("text");

    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  };

  const handleDashboard = () => {
    window.location.href = "/";
  };

  const renderResult = () => {
    if (!result) {
      return null;
    }

    const finalResult = result.final_result || {};
    const decisionFactors = result.decision_factors || {};
    const claims = Array.isArray(result.claims)
      ? result.claims
      : [];

    const decisionInfo = getDecisionInfo(
      finalResult.decision,
    );

    const DecisionIcon = decisionInfo.icon;

    const evidenceCount = claims.reduce(
      (total, claim) =>
        total +
        (Array.isArray(claim.evidence)
          ? claim.evidence.length
          : 0),
      0,
    );

    return (
      <section className="results-dashboard">

        {/* Result Hero */}
        <div
          className={`result-hero ${decisionInfo.className}`}
        >
          <div className="result-hero-main">

            <div className="result-status-icon">
              <DecisionIcon size={32} />
            </div>

            <div className="result-title-area">
              <span className="result-overline">
                ANALYSIS COMPLETE
              </span>

              <span className="result-overline">
  VERIFICATION RESULT
</span>

<h2>
  {decisionInfo.label}
</h2>

<div className="result-confidence-text">
  Confidence{" "}
  <strong>
    {formatPercentage(finalResult.confidence)}
  </strong>
</div>

              <p>
                {decisionInfo.description}
              </p>
            </div>

            <ConfidenceMeter
              confidence={finalResult.confidence}
            />
          </div>

          <div className="result-meta">
            <span>
              Analysis ID:
            </span>

            <code>
              {result.analysis_id}
            </code>

            <span className="meta-divider"></span>

            <span>
              Analyzed:
            </span>

            <span>
              {formatDate(result.analyzed_at)}
            </span>
          </div>
        </div>

        {/* Summary cards */}
        <div className="result-summary-grid">

          <div className="result-stat-card">
            <div className="result-stat-icon blue">
              <ShieldCheck size={20} />
            </div>

            <div>
              <span>Final Decision</span>
              <strong>
                {finalResult.decision || "N/A"}
              </strong>
            </div>
          </div>

          

          <div className="result-stat-card">
            <div className="result-stat-icon green">
              <Search size={20} />
            </div>

            <div>
              <span>Claims Analyzed</span>
              <strong>
                {claims.length}
              </strong>
            </div>
          </div>

          <div className="result-stat-card">
            <div className="result-stat-icon orange">
              <FileText size={20} />
            </div>

            <div>
              <span>Evidence Items</span>
              <strong>
                {evidenceCount}
              </strong>
            </div>
          </div>

        </div>

        {/* Explanation */}
        {result.explanation && (
          <div className="result-section explanation-section">
            <div className="section-heading">
              <div className="section-heading-icon">
                <Sparkles size={19} />
              </div>

              <div>
                <span>AI ASSESSMENT</span>
                <h3>Why this result?</h3>
              </div>
            </div>

            <p className="explanation-text">
              {result.explanation}
            </p>
          </div>
        )}


        <div className="result-section verification-summary">

  <div className="section-heading">
    <div className="section-heading-icon">
      <ShieldCheck size={19} />
    </div>

    <div>
      <span>VERIFICATION SUMMARY</span>
      <h3>Evidence Overview</h3>
    </div>
  </div>

  <div className="verification-summary-grid">

    <div className="verification-summary-item">
      <span>Claims Found</span>
      <strong>{claims.length}</strong>
    </div>

    <div className="verification-summary-item">
      <span>Evidence Sources</span>
      <strong>{evidenceCount}</strong>
    </div>

    <div className="verification-summary-item">
      <span>Supported</span>
      <strong>
        {decisionFactors.supporting_claims ?? 0}
      </strong>
    </div>

    <div className="verification-summary-item">
      <span>Contradicted</span>
      <strong>
        {decisionFactors.contradicted_claims ?? 0}
      </strong>
    </div>

    <div className="verification-summary-item">
      <span>Insufficient</span>
      <strong>
        {decisionFactors.insufficient_claims ?? 0}
      </strong>
    </div>

  </div>

</div>


        

        {/* Claims */}
        <div className="result-section">

          <div className="section-heading">
            <div className="section-heading-icon">
              <Search size={19} />
            </div>

            <div>
              <span>FACT VERIFICATION</span>
              <h3>Claims & Evidence</h3>
            </div>

            <span className="section-count">
              {claims.length}{" "}
              {claims.length === 1
                ? "claim"
                : "claims"}
            </span>
          </div>

          <div className="claims-list">

            {claims.length === 0 ? (
              <div className="empty-state">
                No claims were identified in this article.
              </div>
            ) : (
              claims.map((claim, index) => {
                const verification =
                  claim.verification || {};

                const verificationInfo =
                  getVerificationInfo(
                    verification.status,
                  );

                const VerificationIcon =
                  verificationInfo.icon;

                const evidence =
                  Array.isArray(claim.evidence)
                    ? claim.evidence
                    : [];

                return (
                  <article
                    className="claim-card"
                    key={
                      claim.claim_id ||
                      `claim-${index}`
                    }
                  >

                    <div className="claim-header">

                      <div className="claim-number">
                        {String(index + 1).padStart(
                          2,
                          "0",
                        )}
                      </div>

                      <div className="claim-content">

                        <div className="claim-top-row">
                          <span className="claim-label">
                            CLAIM
                          </span>

                          <span
                            className={`verification-badge ${verificationInfo.className}`}
                          >
                            <VerificationIcon size={14} />
                            {verification.status ||
                              "INSUFFICIENT"}
                          </span>
                        </div>

                        <h4 className="claim-text">
                       “{claim.claim_text}”
                             </h4>

                        <div className="claim-metrics">

  <div className="claim-metric">
    <span>Importance</span>
    <strong>
      {formatPercentage(claim.importance_score)}
    </strong>
  </div>

  <div className="claim-metric">
    <span>Confidence</span>
    <strong>
      {formatPercentage(verification.confidence)}
    </strong>
  </div>

  <div className="claim-metric">
    <span>Sources</span>
    <strong>
      {verification.independent_sources ?? 0}
    </strong>
  </div>

</div>

                        {verification.reason && (
                          <div className="verification-reason">
                            <Info size={15} />
                            <span>
                              {verification.reason}
                            </span>
                          </div>
                        )}

                      </div>

                    </div>

                    {/* Evidence */}
                    {evidence.length > 0 && (
                      <div className="evidence-container">

                        <div className="evidence-heading">
                          <span>
                            EVIDENCE SOURCES
                          </span>

                          <span>
                            {evidence.length}
                          </span>
                        </div>

                        <div className="evidence-list">

                          {evidence.map(
                            (item, evidenceIndex) => (
                              <div
                                className="evidence-card"
                                key={`${claim.claim_id}-${evidenceIndex}`}
                              >

                                <div className="evidence-main">

                                  <div className="evidence-source-icon">
                                    <FileText
                                      size={16}
                                    />
                                  </div>

                                  <div className="evidence-content">

                                    <h5>
  {item.source_name || "Unknown source"}
</h5>

                                    <div className="evidence-source">
  {item.source_type && (
    <span>
      {item.source_type}
    </span>
  )}

  {item.provider && (
    <>
      <span>•</span>
      <span>
        via {item.provider}
      </span>
    </>
  )}
</div>

                                    {item.snippet && (
                                      <p>
                                        {item.snippet}
                                      </p>
                                    )}

                                    <div className="evidence-meta">

                                      <span>
                                        Relevance:{" "}
                                        <strong>
                                          {formatPercentage(
                                            item.relevance_score,
                                          )}
                                        </strong>
                                      </span>

                                      {item.source_quality_score != null && (
  <span>
    Quality:{" "}
    <strong>
      {item.source_quality_score}/100
    </strong>
  </span>
)}

                                      {item.stance && (
                                        <span>
                                          Stance:{" "}
                                          <strong>
                                            {item.stance}
                                          </strong>
                                        </span>
                                      )}

                                    </div>

                                  </div>

                                </div>

                                {item.url && (
                                  <a
                                    className="evidence-link"
                                    href={item.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    aria-label={`Open ${item.source_name || "source"}`}
                                  >
                                    <ExternalLink
                                      size={17}
                                    />
                                  </a>
                                )}

                              </div>
                            ),
                          )}

                        </div>
                      </div>
                    )}

                  </article>
                );
              })
            )}

          </div>
        </div>

        {/* Actions */}
        <div className="result-actions">

          <button
            type="button"
            className="secondary-action"
            onClick={handleDashboard}
          >
            <ArrowLeft size={17} />
            Back to Dashboard
          </button>

          <button
            type="button"
            className="primary-action"
            onClick={handleAnalyzeAnother}
          >
            Analyze Another Article
            <ArrowRight size={17} />
          </button>

        </div>

      </section>
    );
  };

  return (
    <main className="analyze-page">

      {!result && (
        <>
          <section className="analyze-header">

            <div className="hero-badge">
              <span className="status-dot"></span>
              AI News Analysis
            </div>

            <h1>
              Analyze a news
              <span> article.</span>
            </h1>

            <p>
              Submit a headline and article text.
              Fake News Detection will analyze the content
              using machine learning, claims, evidence,
              and verification.
            </p>

          </section>

          <form
            className="analysis-form"
            onSubmit={handleAnalyze}
          >
            <div className="form-card">

              <div className="form-card-header">

                <div className="form-icon">
                  <FileText size={21} />
                </div>

                <div>
                  <h2>News Article</h2>
                  <p>
                    Provide the content you want to
                    verify.
                  </p>
                </div>

              </div>

              <div className="input-mode-toggle">
  <button
    type="button"
    className={inputMode === "text" ? "mode-button active" : "mode-button"}
    onClick={() => {
      setInputMode("text");
      setError("");
    }}
  >
    <FileText size={18} />
    Article Text
  </button>

  <button
    type="button"
    className={inputMode === "url" ? "mode-button active" : "mode-button"}
    onClick={() => {
      setInputMode("url");
      setError("");
    }}
  >
    <ExternalLink size={18} />
    Article URL
  </button>
</div>


              {inputMode === "text" ? (
  <>
    

    {/* ARTICLE TEXT */}
    <div className="form-group">
      <div className="label-row">
        <label htmlFor="articleText">
          Article text
        </label>

        <span>
          {articleText.length.toLocaleString()} characters
        </span>
      </div>

      <textarea
        id="articleText"
        value={articleText}
        onChange={(event) =>
          setArticleText(event.target.value)
        }
        placeholder="Paste the complete news article here..."
        disabled={loading}
      />
    </div>
  </>
) : (
  /* URL MODE */
  <div className="form-group">
    <label htmlFor="articleUrl">
      Article URL
    </label>

    <input
      id="articleUrl"
      type="url"
      value={articleUrl}
      onChange={(event) =>
        setArticleUrl(event.target.value)
      }
      placeholder="https://example.com/news-article"
      disabled={loading}
    />

    <p className="input-help">
      Enter a publicly accessible news article URL.
      The article content will be extracted automatically.
    </p>
  </div>
)}

              {error && (
                <div className="error-message">
                  <AlertCircle size={18} />
                  <span>{error}</span>
                </div>
              )}

              <button
                type="submit"
                className="analyze-button"
                disabled={loading}
              >
                {loading ? (
                  <>
                    <span className="loading-spinner"></span>
                    Analyzing article...
                  </>
                ) : (
                  <>
                    <Sparkles size={19} />
                    Analyze Article
                    <ArrowRight size={18} />
                  </>
                )}
              </button>

            </div>
          </form>
        </>
      )}

      {loading && (
        <section className="analysis-loading">

          <div className="loading-orb">
            <Sparkles size={28} />
          </div>

          <h2>
            Analyzing your article
          </h2>

          <p>
            Fake News Detection is processing the article
            and checking available evidence.
          </p>

          <div className="loading-steps">

            <div className="loading-step active">
              <span></span>
              Analyzing content
            </div>

            <div className="loading-step active">
              <span></span>
              Extracting claims
            </div>

            <div className="loading-step active">
              <span></span>
              Retrieving evidence
            </div>

            <div className="loading-step active">
              <span></span>
              Preparing assessment
            </div>

          </div>

        </section>
      )}

      {result && renderResult()}

    </main>
  );
}

export default Analyze;