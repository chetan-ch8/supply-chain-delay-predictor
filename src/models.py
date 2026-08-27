from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from src.features import build_single_order, load_encoder_bundle

MODELS_DIR = Path("models")
REGRESSOR_PATH = MODELS_DIR / "delay_regressor.pkl"
CLASSIFIER_PATH = MODELS_DIR / "late_classifier.pkl"

RISK_THRESHOLDS = {
    "green": 0.33,   # is_late_probability < 0.33  -> "low"
    "amber": 0.66,   # 0.33 <= prob < 0.66          -> "medium"
    # >= 0.66                                        -> "high"
}

def _load_model(path: Path):
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Run notebooks/03_modelling.ipynb first "
            "(or the equivalent training script) to train and save the models."
        )
    return joblib.load(path)

def load_models():
    regressor = _load_model(REGRESSOR_PATH)
    classifier = _load_model(CLASSIFIER_PATH)
    encoder_bundle = load_encoder_bundle()
    return regressor, classifier, encoder_bundle

def risk_level_from_probability(prob: float) -> str:
    if prob < RISK_THRESHOLDS["green"]:
        return "low"
    elif prob < RISK_THRESHOLDS["amber"]:
        return "medium"
    return "high"

def predict_delay(order: dict, models: tuple | None = None) -> dict:
    if models is None:
        models = load_models()
    regressor, classifier, encoder_bundle = models

    features = build_single_order(order, encoder_bundle)

    delay_days = float(regressor.predict(features)[0])
    is_late_probability = float(classifier.predict_proba(features)[0][1])
    risk_level = risk_level_from_probability(is_late_probability)

    return {
        "delay_days": round(delay_days, 1),
        "is_late_probability": round(is_late_probability, 3),
        "risk_level": risk_level,
    }

if __name__ == "__main__":
    sample_order = {
        "distance_km": 800.0,
        "product_weight_g": 2000.0,
        "freight_value": 35.0,
        "order_purchase_timestamp": "2024-06-01",
        "seller_id": "s1",
        "product_category_name_english": "electronics_en",
        "customer_state": "SP",
    }
    result = predict_delay(sample_order)
    print(result)