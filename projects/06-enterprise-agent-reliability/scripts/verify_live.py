"""Real loopback HTTP and durable API restart smoke test; no external services."""
import os
import subprocess
import sys
import tempfile
import time

import httpx


def start(directory):
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "agent_lab.app:app", "--host", "127.0.0.1", "--port", "18006", "--no-access-log"],
        cwd=directory, env=os.environ.copy(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    for _ in range(100):
        try:
            if httpx.get("http://127.0.0.1:18006/health").status_code == 200:
                return process
        except httpx.TransportError:
            pass
        if process.poll() is not None:
            raise RuntimeError("API exited before health check")
        time.sleep(0.05)
    process.terminate()
    process.wait(timeout=10)
    raise RuntimeError("API did not become healthy")


def stop(process):
    process.terminate()
    process.wait(timeout=10)


with tempfile.TemporaryDirectory() as directory:
    process = start(directory)
    try:
        with httpx.Client(base_url="http://127.0.0.1:18006") as client:
            operator = {"X-Lab-Identity": "alpha-operator"}
            response = client.post("/executions", headers=operator, json={"key": "live-smoke", "workflow": "deploy"})
            response.raise_for_status()
            row = response.json()
            assert row["status"] == "pending_approval"
            eid = row["id"]
            assert client.post(f"/executions/{eid}/approve", headers={"X-Lab-Identity": "beta-approver"}).status_code == 404
            assert client.post(f"/executions/{eid}/approve", headers={"X-Lab-Identity": "alpha-approver"}).json()["status"] == "succeeded"
            assert client.get(f"/executions/{eid}/audit", headers=operator).status_code == 200
            metrics = client.get("/metrics").text
            assert "agent_workflows" in metrics and "agent_simulated_cost_units" in metrics and eid not in metrics
    finally:
        stop(process)
    process = start(directory)
    try:
        with httpx.Client(base_url="http://127.0.0.1:18006") as client:
            assert client.get(f"/executions/{eid}", headers=operator).json()["status"] == "succeeded"
            assert "agent_workflows" in client.get("/metrics").text
    finally:
        stop(process)
print("PASS: real HTTP approval, tenant denial, audit, metrics and persisted server restart")
