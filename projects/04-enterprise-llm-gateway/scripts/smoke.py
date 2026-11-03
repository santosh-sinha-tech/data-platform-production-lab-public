"""Real HTTP smoke test against a running, fresh local gateway."""

import json
import os
import time
import httpx

with httpx.Client(base_url=os.getenv("GATEWAY_URL", "http://127.0.0.1:8000")) as client:
    for attempt in range(50):
        try:
            if client.get("/health").status_code == 200:
                break
        except httpx.TransportError:
            pass
        time.sleep(0.1)
    else:
        raise RuntimeError("gateway did not become ready within five seconds")
    headers = {"X-API-Key": "demo-alpha", "Idempotency-Key": "container-smoke"}
    body = {"app": "chat", "prompt": "synthetic", "input_tokens": 9}
    first = client.post("/v1/generate", json=body, headers=headers)
    replay = client.post("/v1/generate", json=body, headers=headers)
    assert first.status_code == replay.status_code == 200
    assert first.json() == replay.json()
    assert client.get("/v1/usage", headers={"X-API-Key": "demo-beta"}).json() == []
    assert "gateway_requests_total" in client.get("/metrics").text
    assert client.get("/openapi.json").status_code == 200
    assert (
        client.get("/v1/costs", headers={"X-API-Key": "demo-alpha"}).status_code == 200
    )
print(
    json.dumps(
        {
            "health": "PASS",
            "generation": "PASS",
            "durable_replay": "PASS",
            "tenant_isolation": "PASS",
            "metrics": "PASS",
            "openapi": "PASS",
        }
    )
)
