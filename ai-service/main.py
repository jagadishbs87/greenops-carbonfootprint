from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import List, Dict
import random

app = FastAPI(title="GreenOps AI Optimizer", version="1.0.0")


class RegionMetric(BaseModel):
    region: str
    carbon: float
    latency: float
    cost: float


class WeightConfig(BaseModel):
    carbon: float = Field(ge=0)
    latency: float = Field(ge=0)
    cost: float = Field(ge=0)


class OptimizeRequest(BaseModel):
    metrics: List[RegionMetric]
    weights: WeightConfig


def normalize(values: List[float]) -> List[float]:
    mn = min(values)
    mx = max(values)
    if mx == mn:
        return [1.0 for _ in values]
    return [(v - mn) / (mx - mn) for v in values]


@app.get("/health")
def health() -> Dict:
    return {"ok": True, "service": "greenops-ai"}


@app.post("/optimize")
def optimize(payload: OptimizeRequest) -> Dict:
    metrics = payload.metrics
    w = payload.weights
    carbon_n = normalize([m.carbon for m in metrics])
    latency_n = normalize([m.latency for m in metrics])
    cost_n = normalize([m.cost for m in metrics])

    scored = []
    for idx, m in enumerate(metrics):
        score = w.carbon * carbon_n[idx] + w.latency * latency_n[idx] + w.cost * cost_n[idx]
        scored.append(
            {
                "region": m.region,
                "carbon": m.carbon,
                "latency": m.latency,
                "cost": m.cost,
                "score": round(score, 6),
            }
        )

    scored = sorted(scored, key=lambda x: x["score"])
    best = scored[0]
    worst_cost = max(item["cost"] for item in scored)
    worst_carbon = max(item["carbon"] for item in scored)
    worst_latency = max(item["latency"] for item in scored)

    cost_saved = ((worst_cost - best["cost"]) / worst_cost * 100) if worst_cost else 0
    carbon_saved = ((worst_carbon - best["carbon"]) / worst_carbon * 100) if worst_carbon else 0

    return {
        "weights": w.model_dump(),
        "scored": scored,
        "bestRegion": best["region"],
        "insights": {
            "costSavedPercent": round(cost_saved, 2),
            "latencyReducedMs": round(max(0, worst_latency - best["latency"]), 2),
            "carbonReducedPercent": round(carbon_saved, 2),
        },
    }


class PredictRequest(BaseModel):
    history_carbon: List[float]
    history_cost: List[float]


@app.post("/predict")
def predict(payload: PredictRequest) -> Dict:
    # A simple mock AI prediction for future trends based on history
    avg_carbon = sum(payload.history_carbon) / len(payload.history_carbon) if payload.history_carbon else 50.0
    avg_cost = sum(payload.history_cost) / len(payload.history_cost) if payload.history_cost else 0.05
    
    # Simulate a slight optimization trend or fluctuation
    future_carbon = max(0, avg_carbon * (1.0 - random.uniform(-0.05, 0.15)))
    future_cost = max(0, avg_cost * (1.0 - random.uniform(-0.02, 0.10)))
    
    return {
        "predictedCarbon24h": round(future_carbon, 2),
        "predictedCost24h": round(future_cost, 4),
        "trend": "down" if future_carbon < avg_carbon else "up"
    }
