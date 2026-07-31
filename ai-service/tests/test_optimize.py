from fastapi.testclient import TestClient
from main import app


client = TestClient(app)


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["service"] == "greenops-ai"


def test_optimize_returns_best_region_and_insights():
    payload = {
        "metrics": [
            {"region": "eu-west-1", "carbon": 130, "latency": 110, "cost": 0.03},
            {"region": "us-west-2", "carbon": 240, "latency": 80, "cost": 0.025},
            {"region": "ap-south-1", "carbon": 450, "latency": 220, "cost": 0.04},
        ],
        "weights": {"carbon": 0.5, "latency": 0.3, "cost": 0.2},
    }

    res = client.post("/optimize", json=payload)
    assert res.status_code == 200
    body = res.json()

    assert "bestRegion" in body
    assert "scored" in body
    assert "insights" in body
    assert len(body["scored"]) == 3
    assert body["scored"][0]["region"] == body["bestRegion"]
    assert body["scored"][0]["score"] <= body["scored"][1]["score"] <= body["scored"][2]["score"]
