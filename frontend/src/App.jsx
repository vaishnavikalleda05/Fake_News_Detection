import Analyze from "./pages/Analyze";
import HistoryPage from "./pages/History";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import {
  ShieldCheck,
  LayoutDashboard,
  Search,
  History,
} from "lucide-react";

import "./index.css";

function Navbar() {
  return (
    <nav className="navbar">
      <div className="brand">
        <div className="brand-icon">
          <ShieldCheck size={24} />
        </div>

        <div>
          <div className="brand-name">FactCheck AI</div>
          <div className="brand-subtitle">Fake News Detection</div>
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

        <a href="/history">
          <History size={17} />
          History
        </a>
      </div>
    </nav>
  );
}

function Dashboard() {
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

        <div className="feature-card">
          <div className="feature-icon">
            <History size={23} />
          </div>

          <h3>Analysis History</h3>

          <p>
            Save and review previous analyses through the MongoDB-backed
            history system.
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

        <Route
  path="/history"
  element={
    <HistoryPage
      onViewAnalysis={(analysisId) => {
        window.location.href =
          `/analyze?analysis_id=${encodeURIComponent(analysisId)}`;
      }}
    />
  }
/>
      </Routes>
    </BrowserRouter>
  );
}

export default App;