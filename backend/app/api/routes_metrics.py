"""Model evaluation metrics API route."""

import json
from fastapi import APIRouter, HTTPException
from backend.app.config import find_project_root

router = APIRouter(prefix="/metrics", tags=["Metrics"])

@router.get("")
async def get_model_metrics() -> dict:
    """Return holdout-test model performance metrics."""
    metrics_path = find_project_root() / "outputs" / "metrics.json"
    if not metrics_path.exists():
        raise HTTPException(status_code=404, detail="Model metrics file not found.")

    try:
        with metrics_path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=500, detail="Unable to read model metrics.") from exc

    holdout = data.get("holdout_test")
    if not isinstance(holdout, dict):
        raise HTTPException(status_code=500, detail="Holdout test metrics are missing.")

    weighted = holdout.get("classification_report", {}).get("weighted avg", {})
    return {
        "model": data.get("model", "Unknown model"),
        "split": holdout.get("split", "holdout_test"),
        "threshold": holdout.get("threshold", 0.5),
        "accuracy": holdout.get("accuracy"),
        "precision": holdout.get("precision_fake"),
        "recall": holdout.get("recall_fake"),
        "f1_score": holdout.get("f1_fake"),
        "test_samples": weighted.get("support"),
    }
