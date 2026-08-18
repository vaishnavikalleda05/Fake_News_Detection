import { useEffect, useState } from "react";
import Analyze from "./pages/Analyze";

import { BrowserRouter, Routes, Route } from "react-router-dom";
import {
  ShieldCheck,
  LayoutDashboard,
  Search,
} from "lucide-react";

import { getModelMetrics } from "./services/api";
import "./index.css";

function Navbar() {
  return (
    <nav className="navbar">
      <div className="brand">
        <div className="brand-icon">
          <ShieldCheck size={24} />
        </div>

        <div>
          <div className="brand-name">Fake News Detection</div>
          <div className="brand-subtitle">AI Verification</div>
        </div>
      </div>

      <div className="nav-links">
        <a href="/">
          <LayoutDashboard size={17} />
          Dashboard
        </a>

        <a href="/analyze">
          <Search size={17} />
          Analyze
        </a>
      </div>
    </nav>
  );
}

function Dashboard() {
  const [metrics, setMetrics] = useState(null);
  const [metricsLoading, setMetricsLoading] = useState(true);
  const [metricsError, setMetricsError] = useState("");

  useEffect(() => {
    let mounted = true;
    async function loadMetrics() {
      try {
        const data = await getModelMetrics();
        if (mounted) setMetrics(data);
      } catch (error) {
        if (mounted) {
          setMetricsError(
            error?.response?.data?.detail ||
              "Unable to load model performance metrics."
          );
        }
      } finally {
        if (mounted) setMetricsLoading(false);
      }
    }
    loadMetrics();
    return () => { mounted = false; };
  }, []);

  const metricItems = [
    { label: "Accuracy", key: "accuracy" },
    { label: "Precision", key: "precision" },
    { label: "Recall", key: "recall" },
    { label: "F1 Score", key: "f1_score" },
  ];

  const formatMetric = (value) =>
    typeof value === "number" ? `${(value * 100).toFixed(2)}%` : "—";

  return (
    <main className="page">
      <section className="hero">
        <div className="hero-badge">
          <span className="status-dot"></span>
          AI-Powered News Verification
        </div>

        <h1>
          Verify the news.
          <br />
          <span>Know what to trust.</span>
        </h1>

        <p>
          Analyze news articles using machine learning, claim extraction,
          evidence retrieval, and multi-source verification.
        </p>

        <a href="/analyze" className="primary-button">
          <Search size={19} />
          Analyze a News Article
        </a>
      </section>

      <section className="model-performance">
        <div className="model-performance-header">
          <div>
            <span className="section-label">MODEL PERFORMANCE</span>
            <h2>Evaluation metrics</h2>
            <p>
              {metrics?.model || "TF-IDF + Logistic Regression"} ·{" "}
              {metrics?.split === "holdout_test"
                ? "Holdout test set"
                : metrics?.split || "Test set"}
              {metrics?.test_samples
                ? ` · ${Number(metrics.test_samples).toLocaleString()} samples`
                : ""}
            </p>
          </div>
          {metrics && (
            <div className="metrics-badge">
              <ShieldCheck size={17} />
              Test performance
            </div>
          )}
        </div>

        {metricsLoading && <div className="metrics-state">Loading model metrics…</div>}
        {!metricsLoading && metricsError && (
          <div className="metrics-error">{metricsError}</div>
        )}

        {!metricsLoading && !metricsError && metrics && (
          <>
            <div className="metric-card-grid">
              {metricItems.map((item) => (
                <div className="metric-card" key={item.key}>
                  <span>{item.label}</span>
                  <strong>{formatMetric(metrics[item.key])}</strong>
                </div>
              ))}
            </div>

            <div className="metrics-chart-card">
              <div className="metrics-chart-title">
                <div>
                  <h3>Model Performance</h3>
                  <p>Accuracy, precision, recall, and F1 score</p>
                </div>
                <span>0–100%</span>
              </div>

              <div className="metrics-bar-chart" role="img"
                aria-label="Bar chart comparing accuracy, precision, recall, and F1 score">
                {metricItems.map((item) => {
                  const value =
                    typeof metrics[item.key] === "number"
                      ? Math.max(0, Math.min(1, metrics[item.key]))
                      : 0;
                  return (
                    <div className="metric-bar-column" key={item.key}>
                      <div className="metric-bar-value">
                        {formatMetric(metrics[item.key])}
                      </div>
                      <div className="metric-bar-track">
                        <div className="metric-bar"
                          style={{ height: `${value * 100}%` }} />
                      </div>
                      <span>{item.label}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          </>
        )}
      </section>

      <section className="feature-grid">
        <div className="feature-card">
          <div className="feature-icon">
            <ShieldCheck size={23} />
          </div>

          <h3>AI Detection</h3>

          <p>
            Machine learning analyzes the article and estimates whether the
            content is likely to be real or fake.
          </p>
        </div>

        <div className="feature-card">
          <div className="feature-icon">
            <Search size={23} />
          </div>

          <h3>Claim Verification</h3>

          <p>
            Important claims are extracted and checked against available
            evidence from multiple sources.
          </p>
        </div>

        
      </section>

      <section className="workflow">
        <div>
          <span className="section-label">HOW IT WORKS</span>
          <h2>From article to evidence-backed decision</h2>
        </div>

        <div className="workflow-steps">
          <div className="workflow-step">
            <span>01</span>
            <div>
              <h3>Submit</h3>
              <p>Provide a headline and article text.</p>
            </div>
          </div>

          <div className="workflow-step">
            <span>02</span>
            <div>
              <h3>Analyze</h3>
              <p>Our ML and verification pipeline processes the content.</p>
            </div>
          </div>

          <div className="workflow-step">
            <span>03</span>
            <div>
              <h3>Verify</h3>
              <p>Claims and external evidence are evaluated.</p>
            </div>
          </div>

          <div className="workflow-step">
            <span>04</span>
            <div>
              <h3>Decide</h3>
              <p>Receive a transparent final assessment.</p>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}

function PlaceholderPage({ title }) {
  return (
    <main className="page placeholder-page">
      <div className="placeholder-card">
        <ShieldCheck size={42} />
        <h1>{title}</h1>
        <p>This section will be connected to the FastAPI backend next.</p>
      </div>
    </main>
  );
}

function App() {
  return (
    <BrowserRouter>
      <Navbar />

      <Routes>
        <Route path="/" element={<Dashboard />} />

       <Route path="/analyze" element={<Analyze />} />

       
      </Routes>
    </BrowserRouter>
  );
}

export default App;