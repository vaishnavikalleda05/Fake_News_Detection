"""ML Inference Service wrapping the existing TF-IDF + Logistic Regression pipeline."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.app.config import find_project_root, settings
from backend.app.utils.logger import logger

# Ensure project root and src/ directory are in sys.path for joblib TextCleaner unpickling
_PROJECT_ROOT = find_project_root()
_SRC_DIR = _PROJECT_ROOT / "src"

if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

try:
    from model_compat import load_pipeline
except ImportError:
    # Fallback to direct import if running from different directory
    sys.path.insert(0, str(_SRC_DIR))
    from model_compat import load_pipeline  # type: ignore


class MLService:
    """Singleton service for managing and running inference with the trained ML pipeline."""

    def __init__(self, model_path: Path | None = None) -> None:
        self.model_path: Path = model_path or settings.resolve_model_path()
        self.pipeline: Any = None
        self.is_loaded: bool = False
        self.load_error: str | None = None
        self.model_name: str = "TF-IDF + Logistic Regression"

    def load_model(self) -> bool:
        """Load the serialized pipeline from disk with integrity checks."""
        try:
            if not self.model_path.exists():
                err_msg = f"Model artifact not found at: {self.model_path.resolve()}"
                logger.error(err_msg)
                self.load_error = err_msg
                self.is_loaded = False
                return False

            logger.info("Loading ML pipeline from: %s", self.model_path)
            self.pipeline = load_pipeline(self.model_path, verify=True)
            self.is_loaded = True
            self.load_error = None
            logger.info("ML pipeline loaded successfully and verified.")
            return True
        except Exception as exc:
            err_msg = f"Failed to load ML pipeline: {exc}"
            logger.exception(err_msg)
            self.load_error = str(exc)
            self.is_loaded = False
            return False

    def predict(
        self,
        headline: str | None = None,
        article_text: str | None = None,
    ) -> dict[str, Any]:
        """Perform classification prediction on headline and/or article text.

        Combines headline and article text consistently with the training protocol.
        Returns:
            dict containing prediction ('FAKE' or 'REAL'), confidence, raw probability,
            and input text metadata.
        """
        if not self.is_loaded or self.pipeline is None:
            raise RuntimeError(
                f"ML model is not loaded. Details: {self.load_error or 'Model artifact missing.'}"
            )

        # Build combined text identically to training: "title body"
        parts: list[str] = []
        if headline and headline.strip():
            parts.append(headline.strip())
        if article_text and article_text.strip():
            parts.append(article_text.strip())

        combined_text = " ".join(parts).strip()
        if not combined_text:
            raise ValueError("Input text cannot be empty.")

        # Predict probability of FAKE (class index 1)
        prob_matrix = self.pipeline.predict_proba([combined_text])
        prob_fake = float(prob_matrix[0, 1])

        # Classification decision: FAKE if prob_fake >= 0.5 else REAL
        if prob_fake >= 0.5:
            prediction = "FAKE"
            confidence = prob_fake
        else:
            prediction = "REAL"
            confidence = 1.0 - prob_fake

        char_count = len(combined_text)
        word_count = len(combined_text.split())

        return {
            "prediction": prediction,
            "confidence": round(confidence, 4),
            "prob_fake": round(prob_fake, 4),
            "model": self.model_name,
            "char_count": char_count,
            "word_count": word_count,
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
        }


# Singleton instance
ml_service = MLService()