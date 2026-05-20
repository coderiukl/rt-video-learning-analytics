from __future__ import annotations
import os
import logging
import threading
from typing import Any

import joblib
from django.conf import settings

logger = logging.getLogger(__name__)

_cache: dict[str, tuple[Any, Any]] = {}
_lock = threading.Lock()


def _project_root() -> str:
    return str(getattr(settings, "BASE_DIR").parent)


LOCAL_FALLBACK = {
    "dropout_predictor": (
        "models/dropout/dropout_model.pkl",
        "models/dropout/dropout_scaler.pkl",
    ),
    "learning_style": ("models/style/kmeans.pkl", None),
    "recommender": ("models/recommender/hybrid.pkl", None),
}


def _try_mlflow(name: str, alias: str):
    """Load via sklearn flavor (preserves predict_proba) with pyfunc fallback."""
    uri = getattr(settings, "MLFLOW_TRACKING_URI", None)
    if not uri:
        return None
    try:
        import mlflow  # local import keeps Django boot cheap
        mlflow.set_tracking_uri(uri)
        for uri_form in (f"models:/{name}@{alias}", f"models:/{name}/{alias.capitalize()}"):
            for loader in ("sklearn", "pyfunc"):
                try:
                    if loader == "sklearn":
                        import mlflow.sklearn
                        return mlflow.sklearn.load_model(uri_form)
                    import mlflow.pyfunc
                    return mlflow.pyfunc.load_model(uri_form)
                except Exception:
                    continue
        return None
    except Exception as exc:
        logger.warning("MLflow load failed for %s@%s: %s", name, alias, exc)
        return None


def _try_local(name: str):
    if name not in LOCAL_FALLBACK:
        return None, None
    m_rel, s_rel = LOCAL_FALLBACK[name]
    root = _project_root()
    m_path = os.path.join(root, m_rel)
    s_path = os.path.join(root, s_rel) if s_rel else None
    if not os.path.exists(m_path):
        # Legacy fallback for old single-file layout backend/models/*.pkl
        legacy = os.path.join(root, "backend", "models", os.path.basename(m_rel))
        if os.path.exists(legacy):
            m_path = legacy
            if s_rel:
                legacy_s = os.path.join(
                    root, "backend", "models", os.path.basename(s_rel)
                )
                s_path = legacy_s if os.path.exists(legacy_s) else None
        else:
            return None, None
    model = joblib.load(m_path)
    scaler = joblib.load(s_path) if s_path and os.path.exists(s_path) else None
    logger.info("Loaded %s from local pkl: %s", name, m_path)
    return model, scaler


def load(name: str, alias: str = "production"):
    """Return (model, scaler). scaler may be None for MLflow-loaded models."""
    key = f"{name}:{alias}"
    with _lock:
        if key in _cache:
            return _cache[key]
        model = _try_mlflow(name, alias)
        if model is not None:
            # MLflow pyfunc bundles preprocessing inside the model, so scaler=None.
            # Fall back to local scaler if user explicitly registered one separately.
            _, local_scaler = _try_local(name)
            _cache[key] = (model, local_scaler)
            return _cache[key]
        _cache[key] = _try_local(name)
        return _cache[key]


def invalidate(name: str | None = None) -> None:
    with _lock:
        if name is None:
            _cache.clear()
            return
        for key in [k for k in _cache if k.startswith(f"{name}:")]:
            _cache.pop(key, None)


def status(name: str) -> dict:
    model, _ = load(name)
    return {"name": name, "loaded": model is not None}
