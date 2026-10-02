"""
DataWise AI — Auto-Generated Production FastAPI Serving Microservice
Model: LogisticRegression
"""

import time
import uuid
import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="DataWise AI Model API - LogisticRegression", version="1.0.0")
pipeline = joblib.load("model.joblib")

class PredictionRequest(BaseModel):
    age: float = 0.0
    monthly_charges: float = 0.0
    total_charges: float = 0.0
    num_products: float = 0.0

class BatchPredictionRequest(BaseModel):
    records: list[PredictionRequest]

class PredictionResponse(BaseModel):
    request_id: str
    prediction: Any
    probability: Optional[float] = None
    latency_ms: float

@app.get("/health")
def health():
    return {"status": "healthy", "model": "LogisticRegression"}

@app.get("/model/info")
def model_info():
    return {"model_name": "LogisticRegression", "features_count": 4}

@app.post("/predict", response_model=PredictionResponse)
def predict(request: PredictionRequest):
    t0 = time.perf_counter()
    df = pd.DataFrame([request.model_dump()])
    try:
        pred = pipeline.predict(df)[0]
        prob = None
        if hasattr(pipeline, "predict_proba"):
            probs = pipeline.predict_proba(df)[0]
            prob = float(max(probs))
        latency = (time.perf_counter() - t0) * 1000
        return PredictionResponse(
            request_id=str(uuid.uuid4()),
            prediction=pred if not hasattr(pred, "item") else pred.item(),
            probability=prob,
            latency_ms=round(latency, 2)
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
