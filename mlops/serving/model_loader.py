import mlflow.pyfunc, joblib, yaml, threading

_cache, _lock = {}, threading.Lock()

def load(name: str, stage: str = "Production"):
    with _lock:
        key = f"{name}:{stage}"
        if key not in _cache:
            with open("mlops/config/mlops.yaml") as f:
                cfg = yaml.safe_load(f)
            mlflow.set_tracking_uri(cfg["mlflow"]["tracking_uri"])
            _cache[key] = mlflow.pyfunc.load_model(f"models:/{name}/{stage}")
        return _cache[key]

def invalidate(name=None):
    with _lock:
        _cache.clear() if name is None else \
            [_cache.pop(k) for k in list(_cache) if k.startswith(name)]
