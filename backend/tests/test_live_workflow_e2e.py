import json
import time
import urllib.request
import pytest

def test_full_agent_workflow():
    base_url = "http://127.0.0.1:8000/api"

    # 1. Create Project
    req = urllib.request.Request(
        f"{base_url}/projects",
        data=json.dumps({
            "name": "E2E Customer Churn Workbench",
            "prompt": "Analyze this customer dataset and predict churn with high recall.",
            "configuration": {
                "target_column": "churn",
                "task_type": "Classification",
                "optimization_metric": "F1",
            },
        }).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as res:
        assert res.status == 201
        proj = json.loads(res.read())
        project_id = proj["id"]
        assert project_id.startswith("proj_")
        print(f"\n[E2E] 1. Created Project: {project_id}")

    # 2. Trigger Run
    req = urllib.request.Request(
        f"{base_url}/projects/{project_id}/runs",
        data=json.dumps({
            "prompt": "Analyze customer churn and prioritize recall.",
        }).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as res:
        assert res.status == 200
        run_data = json.loads(res.read())
        run_id = run_data["run_id"]
        assert run_id.startswith("run_")
        print(f"[E2E] 2. Launched Run: {run_id}")

    # 3. Poll for progress & verify pipeline stages
    completed = False
    for step in range(25):
        time.sleep(1.2)
        with urllib.request.urlopen(f"{base_url}/projects/{project_id}/runs/{run_id}") as res:
            status_data = json.loads(res.read())
            pct = status_data["progress_pct"]
            agent = status_data["current_agent"]
            run_status = status_data["status"]
            print(f"[E2E] Step {step+1}: {pct}% | Agent: {agent} | Status: {run_status}")

            if status_data.get("pending_decision"):
                print("[E2E] Human-in-the-loop decision required. Submitting 'Cap'...")
                dec_req = urllib.request.Request(
                    f"{base_url}/projects/{project_id}/runs/{run_id}/decisions",
                    data=json.dumps({
                        "decision_key": "outlier",
                        "decision_value": "Cap",
                        "rationale": "Winsorize 99th percentile",
                    }).encode(),
                    headers={"Content-Type": "application/json"},
                )
                with urllib.request.urlopen(dec_req) as d_res:
                    assert d_res.status == 200
                    print("[E2E] Decision accepted. Workflow resuming.")

            if run_status == "COMPLETED":
                completed = True
                print("[E2E] Pipeline finished with COMPLETED status!")
                break

    assert completed, "Pipeline failed to complete in allotted time"

    # 4. Verify Final Results Workspace data
    with urllib.request.urlopen(f"{base_url}/projects/{project_id}/runs/{run_id}/results") as res:
        assert res.status == 200
        results = json.loads(res.read())
        assert results["best_model"] is not None
        assert results["primary_metric_value"] > 0.8
        assert results["generalization_health"] == "Healthy"
        print(f"[E2E] 3. Results Verified: Best Model = {results['best_model']} (Score = {results['primary_metric_value']})")

    # 5. Verify Artifact Downloads
    for art in ["notebook", "html", "pdf", "json", "summary", "model", "pipeline", "bundle"]:
        art_url = f"{base_url}/projects/{project_id}/runs/{run_id}/artifacts/{art}"
        with urllib.request.urlopen(art_url) as res:
            assert res.status == 200
            content = res.read()
            assert len(content) > 0
            print(f"[E2E] 4. Artifact verified: {art} ({len(content)} bytes)")

    # 6. Verify Contextual Assistant
    chat_req = urllib.request.Request(
        f"{base_url}/projects/{project_id}/chat",
        data=json.dumps({"message": "Why did you use RobustScaler?"}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(chat_req) as res:
        assert res.status == 200
        chat_resp = json.loads(res.read())
        assert "RobustScaler" in chat_resp["content"]
        print("[E2E] 5. Contextual assistant verified!")

if __name__ == "__main__":
    test_full_agent_workflow()
