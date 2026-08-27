from pathlib import Path
import pytest
from src.models import (
    REGRESSOR_PATH,
    CLASSIFIER_PATH,
    load_models,
    predict_delay,
    risk_level_from_probability,
)

MODELS_EXIST = REGRESSOR_PATH.exists() and CLASSIFIER_PATH.exists() and Path(
    "models/feature_encoder.pkl"
).exists()

pytestmark = pytest.mark.skipif(
    not MODELS_EXIST,
    reason="Model files not found — run notebooks/03_modelling.ipynb and "
           "pipeline/03_features.py first",
)

SAMPLE_ORDER = {
    "distance_km": 800.0,
    "product_weight_g": 2000.0,
    "freight_value": 35.0,
    "order_purchase_timestamp": "2024-06-01",
    "seller_id": "does_not_matter_for_this_test",
    "product_category_name_english": "some_category",
    "customer_state": "SP",
}

@pytest.fixture(scope="module")
def models():
    return load_models()

def test_models_load_without_error(models):
    regressor, classifier, encoder_bundle = models
    assert regressor is not None
    assert classifier is not None
    assert "category_encoder" in encoder_bundle

def test_predict_delay_returns_expected_keys(models):
    result = predict_delay(SAMPLE_ORDER, models=models)
    assert set(result.keys()) == {"delay_days", "is_late_probability", "risk_level"}

def test_delay_days_is_a_float(models):
    result = predict_delay(SAMPLE_ORDER, models=models)
    assert isinstance(result["delay_days"], float)

def test_probability_is_between_0_and_1(models):
    result = predict_delay(SAMPLE_ORDER, models=models)
    assert 0.0 <= result["is_late_probability"] <= 1.0

def test_risk_level_is_a_valid_category(models):
    result = predict_delay(SAMPLE_ORDER, models=models)
    assert result["risk_level"] in {"low", "medium", "high"}

def test_risk_level_thresholds_are_monotonic():
    # end-to-end sanity check on the risk banding logic itself
    assert risk_level_from_probability(0.05) == "low"
    assert risk_level_from_probability(0.50) == "medium"
    assert risk_level_from_probability(0.95) == "high"

def test_end_to_end_predict_call_with_unseen_category_and_seller(models):
    unseen_order = dict(
        SAMPLE_ORDER,
        seller_id="brand_new_seller_never_seen",
        product_category_name_english="brand_new_category_never_seen",
        customer_state="ZZ",
    )
    result = predict_delay(unseen_order, models=models)
    assert result["risk_level"] in {"low", "medium", "high"}