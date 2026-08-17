#!/usr/bin/env python3
"""Command-line inference for the FactCheck AI text classifier."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from model_compat import load_pipeline

DEFAULT_THRESHOLD = 0.50
DEFAULT_UNCERTAINTY_MARGIN = 0.05


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Classify news text as REAL, FAKE, or UNCERTAIN."
    )

    parser.add_argument(
        "--pipeline",
        required=True,
        help="Path to the trained pipeline.joblib artifact.",
    )

    parser.add_argument(
        "--text",
        required=True,
        help="News headline or article text to analyze.",
    )

    parser.add_argument(
        "--threshold",
        type=float,
        default=DEFAULT_THRESHOLD,
        help="Probability threshold for FAKE classification.",
    )

    parser.add_argument(
        "--uncertainty-margin",
        type=float,
        default=DEFAULT_UNCERTAINTY_MARGIN,
        help="Margin around the threshold used for UNCERTAIN predictions.",
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the prediction as JSON.",
    )

    return parser.parse_args()


def validate_arguments(
    threshold: float,
    uncertainty_margin: float,
) -> None:
    """Validate prediction threshold configuration."""
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("threshold must be between 0.0 and 1.0.")

    if uncertainty_margin < 0.0:
        raise ValueError("uncertainty-margin must be >= 0.0.")

    if threshold - uncertainty_margin < 0.0:
        raise ValueError(
            "threshold - uncertainty-margin must not be below 0.0."
        )

    if threshold + uncertainty_margin > 1.0:
        raise ValueError(
            "threshold + uncertainty-margin must not exceed 1.0."
        )


def get_probability_fake(pipeline: Any, text: str) -> float:
    """Return the probability assigned to the FAKE class."""
    probabilities = pipeline.predict_proba([text])[0]

    classes = getattr(pipeline, "classes_", None)

    if classes is None and hasattr(pipeline, "named_steps"):
        classifier = pipeline.named_steps.get("classifier")
        classes = getattr(classifier, "classes_", None)

    if classes is None:
        raise ValueError(
            "The loaded pipeline does not expose classifier classes."
        )

    for index, class_name in enumerate(classes):
        if str(class_name).upper() == "FAKE":
            return float(probabilities[index])

    # Support the project's documented numeric label mapping:
    # 0 = REAL, 1 = FAKE.
    for index, class_name in enumerate(classes):
        if str(class_name) == "1":
            return float(probabilities[index])

    raise ValueError("The loaded model does not contain a FAKE class.")


def classify_probability(
    prob_fake: float,
    threshold: float,
    uncertainty_margin: float,
) -> str:
    """Convert fake probability into REAL, FAKE, or UNCERTAIN."""
    lower_bound = threshold - uncertainty_margin
    upper_bound = threshold + uncertainty_margin

    if lower_bound <= prob_fake <= upper_bound:
        return "UNCERTAIN"

    if prob_fake > upper_bound:
        return "FAKE"

    return "REAL"


def build_prediction(
    pipeline: Any,
    text: str,
    model_path: Path,
    threshold: float,
    uncertainty_margin: float,
) -> dict[str, object]:
    """Generate the structured prediction result."""
    prob_fake = get_probability_fake(pipeline, text)

    label = classify_probability(
        prob_fake,
        threshold,
        uncertainty_margin,
    )

    return {
        "label": label,
        "prob_fake": round(prob_fake, 6),
        "threshold": threshold,
        "uncertainty_margin": uncertainty_margin,
        "model_path": str(model_path),
    }


def main() -> None:
    """Run CLI inference."""
    args = parse_args()

    validate_arguments(
        args.threshold,
        args.uncertainty_margin,
    )

    model_path = Path(args.pipeline)

    if not model_path.exists():
        raise FileNotFoundError(
            f"Pipeline file was not found: {model_path}"
        )

    text = args.text.strip()

    if not text:
        raise ValueError("Text cannot be empty.")

    pipeline = load_pipeline(model_path)

    prediction = build_prediction(
        pipeline=pipeline,
        text=text,
        model_path=model_path,
        threshold=args.threshold,
        uncertainty_margin=args.uncertainty_margin,
    )

    if args.json:
        print(json.dumps(prediction, indent=2))
    else:
        print(f"Prediction: {prediction['label']}")
        print(f"Fake probability: {prediction['prob_fake']:.4f}")
        print(f"Threshold: {prediction['threshold']:.4f}")
        print(
            "Uncertainty margin: "
            f"{prediction['uncertainty_margin']:.4f}"
        )
        print(f"Model: {prediction['model_path']}")


if __name__ == "__main__":
    main()