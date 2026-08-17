#!/usr/bin/env python3
"""Streamlit app for FactCheck AI."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import streamlit as st

from detect_fake_news import classify_probability
from model_compat import load_pipeline as load_model_pipeline


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def default_pipeline_path() -> Path:
    return project_root() / "outputs" / "pipeline.joblib"


def default_metrics_path() -> Path:
    return project_root() / "outputs" / "metrics.json"


@st.cache_resource
def load_pipeline(path: str):
    return load_model_pipeline(path)


def load_metrics(path: Path) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def is_short_input(text: str) -> bool:
    tokens = [token for token in text.strip().split() if token]
    return len(tokens) < 8 or len(text.strip()) < 50


def main() -> None:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--pipeline", default=str(default_pipeline_path()))
    args, _ = parser.parse_known_args()

    pipeline_path = Path(args.pipeline).resolve()
    metrics_path = default_metrics_path()

    # Set page layout and config
    st.set_page_config(page_title="FactCheck AI", layout="centered")

    # Inject premium typography and UI glossy CSS theme
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

        /* Typography overrides for text-bearing elements only (prevents overriding icon fonts) */
        html, body, p, h1, h2, h3, h4, h5, h6, label, textarea, button, input, [data-testid="stMarkdownContainer"] {
            font-family: 'Plus Jakarta Sans', sans-serif !important;
        }

        /* App View Background (Main Canvas Gradient) */
        [data-testid="stAppViewContainer"] {
            background: linear-gradient(135deg, #F8FAFC 0%, #E2E8F0 100%) !important;
        }

        /* Sidebar Background Gradient */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0F172A 0%, #1E293B 100%) !important;
        }

        /* Light text inside sidebar */
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] h4,
        [data-testid="stSidebar"] h5,
        [data-testid="stSidebar"] h6,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] span,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] div,
        [data-testid="stSidebar"] .stMarkdown {
            color: #F1F5F9 !important;
        }

        /* Dark sidebar divider */
        [data-testid="stSidebar"] hr {
            border-color: rgba(255, 255, 255, 0.08) !important;
        }

        /* Glassmorphic cards for containers */
        div[data-testid="stVerticalBlock"] > div > div[data-testid="element-container"] > div > div[style*="border"] {
            background-color: rgba(255, 255, 255, 0.75) !important;
            backdrop-filter: blur(12px) !important;
            -webkit-backdrop-filter: blur(12px) !important;
            border: 1px solid rgba(255, 255, 255, 0.6) !important;
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.03), inset 0 1px 1px 0 rgba(255, 255, 255, 0.8) !important;
            border-radius: 12px !important;
            padding: 24px !important;
        }

        /* Text area styling */
        .stTextArea textarea {
            background-color: rgba(255, 255, 255, 0.9) !important;
            border: 1px solid rgba(15, 23, 42, 0.08) !important;
            color: #0F172A !important;
            font-size: 15px !important;
            border-radius: 8px !important;
            padding: 14px !important;
            line-height: 1.6 !important;
            transition: all 0.25s ease-in-out !important;
            box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.02) !important;
        }
        .stTextArea textarea:focus {
            border-color: #2563EB !important;
            box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.08), inset 0 1px 2px rgba(0, 0, 0, 0.02) !important;
            background-color: #FFFFFF !important;
        }

        /* Metric text inside sidebar */
        [data-testid="stSidebar"] [data-testid="stMetricValue"] {
            color: #FFFFFF !important;
            font-size: 26px !important;
            font-weight: 700 !important;
            text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2) !important;
        }
        [data-testid="stSidebar"] [data-testid="stMetricLabel"] {
            color: #94A3B8 !important;
            font-size: 13px !important;
        }

        /* Glossy Primary Button Styling */
        div.stButton > button:first-child {
            background: linear-gradient(180deg, #3B82F6 0%, #2563EB 100%) !important;
            color: #FFFFFF !important;
            font-weight: 600 !important;
            font-size: 15px !important;
            border-radius: 8px !important;
            border-top: 1px solid rgba(255, 255, 255, 0.35) !important;
            border-left: 1px solid rgba(255, 255, 255, 0.15) !important;
            border-right: 1px solid rgba(255, 255, 255, 0.15) !important;
            border-bottom: 1px solid rgba(15, 23, 42, 0.2) !important;
            padding: 12px 24px !important;
            transition: all 0.2s ease-in-out !important;
            box-shadow: 0 4px 14px rgba(37, 99, 235, 0.15), inset 0 1px 0 rgba(255, 255, 255, 0.1) !important;
            cursor: pointer !important;
        }
        div.stButton > button:first-child:hover {
            background: linear-gradient(180deg, #2563EB 0%, #1D4ED8 100%) !important;
            transform: translateY(-1px) !important;
            box-shadow: 0 6px 18px rgba(37, 99, 235, 0.22), inset 0 1px 0 rgba(255, 255, 255, 0.1) !important;
            border-color: transparent !important;
        }
        div.stButton > button:first-child:active {
            transform: translateY(1px) !important;
            box-shadow: 0 2px 6px rgba(37, 99, 235, 0.1) !important;
        }

        /* Slider Custom Styling */
        .stSlider {
            margin-bottom: 10px !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # Sidebar setup
    with st.sidebar:
        st.markdown("""
            <h2 style='color: #FFFFFF; font-family: "Plus Jakarta Sans", sans-serif; margin-bottom: 0px; font-weight: bold;'>FACTCHECK AI</h2>
            <p style='color: #94A3B8; font-family: "Plus Jakarta Sans", sans-serif; font-size: 14px; margin-top: 0px;'>AI-powered fake news detection</p>
        """, unsafe_allow_html=True)
        st.divider()

        st.markdown("<h3 style='color: #FFFFFF; font-family: \"Plus Jakarta Sans\", sans-serif; font-size: 18px; margin-bottom: 5px; font-weight: 600;'>Model</h3>", unsafe_allow_html=True)
        if pipeline_path.exists():
            st.markdown("<p style='color: #34D399; font-size: 15px; font-weight: bold; margin-top: 0px;'>✓ Model loaded</p>", unsafe_allow_html=True)
        else:
            st.markdown("<p style='color: #F87171; font-size: 15px; font-weight: bold; margin-top: 0px;'>✗ Model missing</p>", unsafe_allow_html=True)

        metrics = load_metrics(metrics_path)
        if metrics:
            test = metrics.get("holdout_test", {})
            st.markdown("<h3 style='color: #FFFFFF; font-family: \"Plus Jakarta Sans\", sans-serif; font-size: 18px; margin-top: 20px; margin-bottom: 10px; font-weight: 600;'>Performance</h3>", unsafe_allow_html=True)
            st.metric(label="Accuracy", value=f"{test.get('accuracy', 0):.3f}")
            st.metric(label="Macro F1", value=f"{test.get('macro_f1', 0):.3f}")
            st.metric(label="ROC-AUC", value=f"{test.get('roc_auc', 0):.3f}")

        st.divider()
        st.markdown("<h3 style='color: #FFFFFF; font-family: \"Plus Jakarta Sans\", sans-serif; font-size: 18px; margin-bottom: 5px; font-weight: 600;'>Important</h3>", unsafe_allow_html=True)
        st.markdown(
            "<p style='color: #94A3B8; font-size: 13px; line-height: 1.4; margin-top: 0px;'>This model provides a risk-based prediction and should not be treated as a definitive source of truth.</p>",
            unsafe_allow_html=True
        )

    # Main page title header
    st.markdown("""
        <h1 style='color: #0F172A; font-family: "Plus Jakarta Sans", sans-serif; font-weight: 800; margin-top: 0px; margin-bottom: 5px; font-size: 42px;'>FactCheck AI</h1>
        <p style='color: #2563EB; font-family: "Plus Jakarta Sans", sans-serif; font-size: 18px; font-weight: 500; margin-top: 0px; margin-bottom: 30px;'>
            AI-Powered Fake News Detection with Explainable Results
        </p>
    """, unsafe_allow_html=True)

    # Check for model existence
    if not pipeline_path.exists():
        st.error(
            "Model artifact not found. Run `python src/train_model.py` from the project root, "
            "then restart Streamlit."
        )
        st.stop()

    pipeline = load_pipeline(str(pipeline_path))

    # Main input section
    with st.container(border=True):
        text = st.text_area("Paste a headline or article excerpt:", height=200)

    # Sliders section
    st.write("")
    with st.container(border=True):
        st.markdown("<h4 style='color: #0F172A; font-family: \"Plus Jakarta Sans\", sans-serif; margin-top: 0px; margin-bottom: 15px; font-weight: 600;'>Prediction Settings</h4>", unsafe_allow_html=True)
        threshold = st.slider("Fake threshold", 0.05, 0.95, 0.50, 0.01)
        uncertainty_margin = st.slider(
            "Uncertain band",
            0.00,
            0.30,
            0.10,
            0.01,
            help="A band around the threshold where the app refuses to force a REAL/FAKE label.",
        )

    st.write("")
    # Primary action trigger
    if st.button("Analyze", type="primary", use_container_width=True):
        if not text.strip():
            st.warning("Paste some text first.")
            st.stop()

        # Calculate prediction values
        prob_fake = float(pipeline.predict_proba([text])[0, 1])
        label = classify_probability(prob_fake, threshold, uncertainty_margin)
        half_margin = uncertainty_margin / 2
        lower = max(0.0, threshold - half_margin)
        upper = min(1.0, threshold + half_margin)

        # Calculate confidence metric
        if label == "FAKE":
            confidence = prob_fake
        elif label == "REAL":
            confidence = 1.0 - prob_fake
        else:  # UNCERTAIN
            confidence = max(prob_fake, 1.0 - prob_fake)

        # Set color scheme based on prediction label (Glossy Semantics)
        if label == "REAL":
            bg_color = "rgba(236, 253, 245, 0.85)"      # Light green
            border_color = "rgba(16, 185, 129, 0.5)"  # Green
            text_color = "#065F46"    # Dark green
        elif label == "FAKE":
            bg_color = "rgba(254, 242, 242, 0.85)"      # Light red
            border_color = "rgba(239, 68, 68, 0.5)"  # Red
            text_color = "#991B1B"    # Dark red
        else:  # UNCERTAIN
            bg_color = "rgba(255, 251, 235, 0.85)"      # Light amber
            border_color = "rgba(245, 158, 11, 0.5)"  # Amber
            text_color = "#92400E"    # Dark amber

        # Render semantic result card (Glossy glassmorphism treatment)
        st.markdown(f"""
            <div style="
                background-color: {bg_color};
                backdrop-filter: blur(8px);
                -webkit-backdrop-filter: blur(8px);
                border: 1px solid {border_color};
                padding: 24px;
                border-radius: 12px;
                margin-top: 25px;
                margin-bottom: 20px;
                font-family: 'Plus Jakarta Sans', sans-serif;
                box-shadow: 0 8px 24px 0 rgba(0, 0, 0, 0.02), inset 0 1px 1px 0 rgba(255, 255, 255, 0.6);
            ">
                <h4 style="margin: 0; color: #475569; font-weight: 500; font-size: 13px; letter-spacing: 0.05em; text-transform: uppercase;">Prediction</h4>
                <h2 style="margin: 8px 0 16px 0; color: {text_color}; font-size: 36px; font-weight: 800;">{label}</h2>
                <div style="display: flex; gap: 40px; margin-bottom: 12px;">
                    <div>
                        <span style="font-size: 14px; color: #475569;">Fake probability:</span>
                        <span style="font-size: 18px; font-weight: bold; color: #1E293B; margin-left: 5px;">{prob_fake:.1%}</span>
                    </div>
                    <div>
                        <span style="font-size: 14px; color: #475569;">Confidence:</span>
                        <span style="font-size: 18px; font-weight: bold; color: #1E293B; margin-left: 5px;">{confidence:.1%}</span>
                    </div>
                </div>
                <p style="margin: 0; font-size: 13px; color: #64748B;">
                    Decision rule: REAL &lt; {lower:.0%}, UNCERTAIN = {lower:.0%}–{upper:.0%}, FAKE &gt; {upper:.0%}.
                </p>
            </div>
        """, unsafe_allow_html=True)

        # Render warnings / notices compactly
        if label == "UNCERTAIN":
            st.markdown("""
                <div style="background-color: rgba(255, 251, 235, 0.85); backdrop-filter: blur(4px); -webkit-backdrop-filter: blur(4px); border-left: 4px solid #F59E0B; padding: 12px; border-radius: 4px; margin-bottom: 15px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.01);">
                    <p style="margin: 0; font-size: 13px; color: #92400E; font-family: 'Plus Jakarta Sans', sans-serif;">
                        ⚠️ <strong>Uncertain Prediction:</strong> The model is close to the decision boundary. Treat this as low confidence and provide a longer excerpt if possible.
                    </p>
                </div>
            """, unsafe_allow_html=True)

        if is_short_input(text):
            st.markdown("""
                <div style="background-color: rgba(255, 251, 235, 0.85); backdrop-filter: blur(4px); -webkit-backdrop-filter: blur(4px); border-left: 4px solid #F59E0B; padding: 12px; border-radius: 4px; margin-bottom: 15px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.01);">
                    <p style="margin: 0; font-size: 13px; color: #92400E; font-family: 'Plus Jakarta Sans', sans-serif;">
                        ⚠️ <strong>Short Input Notice:</strong> The input is very short. The model works better with full headlines or article excerpts.
                    </p>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("""
            <div style="background-color: rgba(248, 250, 252, 0.85); backdrop-filter: blur(4px); -webkit-backdrop-filter: blur(4px); border: 1px solid rgba(226, 232, 240, 0.8); padding: 12px; border-radius: 6px; margin-top: 15px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.01);">
                <p style="margin: 0; font-size: 13px; color: #475569; font-family: 'Plus Jakarta Sans', sans-serif;">
                    ℹ️ <strong>Notice:</strong> For real-world use, verify claims against primary sources. This model was trained on a limited educational dataset.
                </p>
            </div>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()