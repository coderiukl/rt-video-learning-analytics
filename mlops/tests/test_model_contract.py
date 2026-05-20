import joblib, numpy as np, pytest

def test_predict_shape():
    m = joblib.load("models/dropout/dropout_model.pkl")
    s = joblib.load("models/dropout/dropout_scaler.pkl")
    X = np.zeros((1, 13))
    p = m.predict_proba(s.transform(X))
    assert p.shape == (1, 2)
    assert 0 <= p[0, 1] <= 1

def test_minimum_performance():
    import json
    with open("metrics/dropout_metrics.json") as f:
        m = json.load(f)
    assert m["roc_auc"] >= 0.7, "Model degraded"
