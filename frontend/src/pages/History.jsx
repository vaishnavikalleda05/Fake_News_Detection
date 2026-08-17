import { useEffect, useState } from "react";
import {
  Clock3,
  ShieldCheck,
  Trash2,
  ExternalLink,
  AlertCircle,
  Loader2,
} from "lucide-react";

import {
  getAnalysisHistory,
  deleteAnalysis,
} from "../services/api";

function History({ onViewAnalysis }) {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadHistory = async () => {
    setLoading(true);
    setError("");

    try {
      const data = await getAnalysisHistory("anonymous", 20);

      // Backend may return either an array or an object containing history.
      const items = Array.isArray(data)
        ? data
        : data.history || data.analyses || data.items || [];

      setHistory(items);
    } catch (err) {
      console.error("Failed to load analysis history:", err);

      if (err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else {
        setError(
          "Unable to load analysis history. Make sure the FastAPI server is running.",
        );
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHistory();
  }, []);

  const handleDelete = async (analysisId) => {
    const confirmed = window.confirm(
      "Are you sure you want to delete this analysis?",
    );

    if (!confirmed) {
      return;
    }

    try {
      await deleteAnalysis(analysisId);

      setHistory((current) =>
        current.filter(
          (item) => item.analysis_id !== analysisId,
        ),
      );
    } catch (err) {
      console.error("Failed to delete analysis:", err);

      setError(
        err.response?.data?.detail ||
          "Unable to delete this analysis.",
      );
    }
  };

  const formatDate = (value) => {
    if (!value) {
      return "Date unavailable";
    }

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
      return "Date unavailable";
    }

    return date.toLocaleString();
  };

  const getDecisionClass = (decision) => {
    const value = String(decision || "").toUpperCase();

    if (value === "REAL") {
      return "history-decision real";
    }

    if (value === "FAKE") {
      return "history-decision fake";
    }

    return "history-decision";
  };

  if (loading) {
    return (
      <main className="history-page">
        <section className="history-card history-loading">
          <Loader2 className="history-spinner" size={42} />

          <h1>Loading Analysis History</h1>

          <p>
            Retrieving your previous analyses from the database...
          </p>
        </section>
      </main>
    );
  }

  return (
    <main className="history-page">
      <section className="history-header">
        <div className="history-icon">
          <Clock3 size={32} />
        </div>

        <div>
          <span className="section-eyebrow">
            ANALYSIS HISTORY
          </span>

          <h1>Previous Analyses</h1>

          <p>
            Review and manage your previous fake news
            verification results.
          </p>
        </div>
      </section>

      {error && (
        <div className="history-error">
          <AlertCircle size={20} />
          <span>{error}</span>
        </div>
      )}

      {!error && history.length === 0 ? (
        <section className="history-card history-empty">
          <ShieldCheck size={52} />

          <h2>No analyses yet</h2>

          <p>
            Your completed article analyses will appear here.
          </p>
        </section>
      ) : (
        <section className="history-list">
          {history.map((item) => {
            const analysisId = item.analysis_id;

            return (
              <article
                className="history-item"
                key={analysisId}
              >
                <div className="history-item-main">
                  <div className="history-item-icon">
                    <ShieldCheck size={24} />
                  </div>

                  <div className="history-item-content">
                    <h2>
                      {item.headline ||
                        "Untitled News Analysis"}
                    </h2>

                    <div className="history-meta">
                      <span>
                        <Clock3 size={15} />
                        {formatDate(item.created_at)}
                      </span>

                      <span>
                        ID: {analysisId}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="history-item-result">
                  <div
                    className={getDecisionClass(
                      item.final_decision,
                    )}
                  >
                    {item.final_decision || "N/A"}
                  </div>

                  {item.final_confidence !==
                    undefined &&
                    item.final_confidence !== null && (
                      <span className="history-confidence">
                        {(
                          Number(item.final_confidence) * 100
                        ).toFixed(1)}
                        %
                      </span>
                    )}
                </div>

                <div className="history-actions">
                  <button
                    type="button"
                    className="history-view-button"
                    onClick={() =>
                      onViewAnalysis?.(analysisId)
                    }
                  >
                    <ExternalLink size={17} />
                    View
                  </button>

                  <button
                    type="button"
                    className="history-delete-button"
                    onClick={() =>
                      handleDelete(analysisId)
                    }
                    aria-label={`Delete ${analysisId}`}
                  >
                    <Trash2 size={17} />
                  </button>
                </div>
              </article>
            );
          })}
        </section>
      )}
    </main>
  );
}

export default History;