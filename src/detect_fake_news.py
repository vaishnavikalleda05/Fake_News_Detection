#!/usr/bin/env python3
"""Command-line inference for the Fake News Detection text classifier."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from model_compat import load_pipeline

DEFAULT_THRESHOLD = 0.50


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Classify news text as REAL or FAKE."
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
        "--json",
        action="store_true",
        help="Print the prediction as JSON.",
    )

    return parser.parse_args()


def validate_arguments(threshold: float) -> None:
    """Validate prediction threshold configuration."""
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("threshold must be between 0.0 and 1.0.")


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
) -> str:
    """Convert fake probability into a binary REAL or FAKE decision."""
    if prob_fake >= threshold:
        return "FAKE"

    return "REAL"


def build_prediction(
    pipeline: Any,
    text: str,
    model_path: Path,
    threshold: float,
) -> dict[str, object]:
    """Generate the structured prediction result."""
    prob_fake = get_probability_fake(pipeline, text)

    label = classify_probability(
        prob_fake,
        threshold,
    )

    return {
        "label": label,
        "prob_fake": round(prob_fake, 6),
        "threshold": threshold,
        "model_path": str(model_path),
    }


def main() -> None:
    """Run CLI inference."""
    args = parse_args()

    validate_arguments(args.threshold)

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
    )

    if args.json:
        print(json.dumps(prediction, indent=2))
    else:
        print(f"Prediction: {prediction['label']}")
        print(f"Fake probability: {prediction['prob_fake']:.4f}")
        print(f"Threshold: {prediction['threshold']:.4f}")
        print(f"Model: {prediction['model_path']}")


if __name__ == "__main__":
    main()