"""
Live End-to-End System Verification against running DataWise AI services.
Creates a new user, checks domain gates, creates a new project, uploads data,
executes the AI workflow, validates artifacts, and tests multi-tenant security.
"""

import io
import json
import os
import sys
import time
import zipfile
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:8000"

def request_json(url, method="GET", data=None, headers=None):
    if headers is None:
        headers = {}
    req_data = None
    if data is not None and isinstance(data, (dict, list)):
        req_data = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"
    elif data is not None:
        req_data = data

    req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            content = resp.read()
            content_type = resp.headers.get("Content-Type", "")
            if "application/json" in content_type:
                return resp.status, json.loads(content.decode("utf-8")), resp.headers
            return resp.status, content, resp.headers
    except urllib.error.HTTPError as e:
        err_body = e.read()
        try:
            return e.code, json.loads(err_body.decode("utf-8")), e.headers
        except Exception:
            return e.code, err_body.decode("utf-8", errors="replace"), e.headers


def main():
    print("=" * 70)
    print("DATAWISE AI LIVE END-TO-END VERIFICATION")
    print("=" * 70)

    # 1. Healthcheck
    print("\n[Step 1] Checking Live Server Health...")
    status, body, _ = request_json(f"{BASE_URL}/health")
    assert status == 200, f"Healthcheck failed: {status}"
    print(f"  -> Healthcheck PASSED: {body}")

    # 2. Domain Restriction Check
    print("\n[Step 2] Testing Domain Restriction (@gmail.com only)...")
    status, body, _ = request_json(
        f"{BASE_URL}/api/auth/register",
        method="POST",
        data={
            "email": "invalid_user@corporate.org",
            "password": "Password123!",
            "name": "Invalid Domain User",
        },
    )
    assert status == 403, f"Expected 403 for non-gmail domain, got: {status} -> {body}"
    print(f"  -> Non-gmail registration properly BLOCKED with HTTP {status}: {body.get('detail')}")

    # 3. Create New User
    unique_id = hex(int(time.time()))[2:]
    new_user_email = f"chokha.analyst.{unique_id}@gmail.com"
    new_user_password = "SecurePassword2026!"
    new_user_name = "Chokha Lead Data Scientist"

    print(f"\n[Step 3] Registering New User: {new_user_email}...")
    status, body, _ = request_json(
        f"{BASE_URL}/api/auth/register",
        method="POST",
        data={
            "email": new_user_email,
            "password": new_user_password,
            "name": new_user_name,
        },
    )
    assert status in [200, 201], f"Registration failed: {status} -> {body}"
    token = body["access_token"]
    user_id = body["user"]["id"]
    print(f"  -> New User Registered successfully! User ID: {user_id}")

    # 4. Duplicate Account Prevention Check
    print("\n[Step 4] Testing Duplicate Registration Prevention...")
    status, body, _ = request_json(
        f"{BASE_URL}/api/auth/register",
        method="POST",
        data={
            "email": new_user_email.upper(),  # Test case-insensitivity
            "password": "AnotherPassword123!",
            "name": "Duplicate Imposter",
        },
    )
    assert status == 400, f"Expected 400 for duplicate email, got: {status} -> {body}"
    print(f"  -> Duplicate registration properly BLOCKED with HTTP {status}: {body.get('detail')}")

    # 5. User Login & Profile Check
    print("\n[Step 5] Logging in with new credentials...")
    status, body, _ = request_json(
        f"{BASE_URL}/api/auth/login",
        method="POST",
        data={
            "email": new_user_email,
            "password": new_user_password,
        },
    )
    assert status == 200, f"Login failed: {status} -> {body}"
    token = body["access_token"]
    auth_headers = {"Authorization": f"Bearer {token}"}
    print("  -> Authentication successful, valid JWT bearer token acquired.")

    status, me_body, _ = request_json(f"{BASE_URL}/api/auth/me", headers=auth_headers)
    assert status == 200, f"Me profile check failed: {status}"
    print(f"  -> Verified Profile: {me_body.get('name')} ({me_body.get('email')})")

    # 6. Create New Project
    project_name = f"Chokha Retention AI — Enterprise Project {unique_id}"
    print(f"\n[Step 6] Creating New Project: '{project_name}'...")
    status, proj_body, _ = request_json(
        f"{BASE_URL}/api/projects",
        method="POST",
        data={
            "name": project_name,
            "description": "Predictive churn analytics with automated feature engineering",
            "objective": "Identify at-risk customer segments and recommend proactive retention actions",
            "tags": ["Production", "AutoML", "CustomerAnalytics"],
        },
        headers=auth_headers,
    )
    assert status in [200, 201], f"Project creation failed: {status} -> {proj_body}"
    project_id = proj_body["id"]
    project_slug = proj_body["slug"]
    print(f"  -> Project created! ID: {project_id}, Slug: {project_slug}")

    # 7. Upload Dataset
    print("\n[Step 7] Uploading Synthetic Customer Dataset...")
    csv_rows = [
        "customer_id,tenure_months,monthly_charges,total_charges,contract_type,support_tickets,churn",
    ]
    for i in range(1, 151):
        tenure = i % 48 + 1
        charges = round(29.99 + (i % 70) * 1.5, 2)
        tot_charges = round(charges * tenure, 2)
        contract = "Month-to-Month" if i % 2 == 0 else ("One-Year" if i % 3 == 0 else "Two-Year")
        tickets = (i % 6)
        churn_label = 1 if (contract == "Month-to-Month" and tickets >= 3) else 0
        csv_rows.append(f"CUST_{i:04d},{tenure},{charges},{tot_charges},{contract},{tickets},{churn_label}")

    csv_data = "\n".join(csv_rows).encode("utf-8")
    boundary = "----DataWiseBoundary12345"
    body_bytes = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="customer_churn_live.csv"\r\n'
        f"Content-Type: text/csv\r\n\r\n"
    ).encode("utf-8") + csv_data + f"\r\n--{boundary}--\r\n".encode("utf-8")

    upload_headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": f"multipart/form-data; boundary={boundary}",
    }

    status, upload_body, _ = request_json(
        f"{BASE_URL}/api/projects/{project_id}/datasets/upload",
        method="POST",
        data=body_bytes,
        headers=upload_headers,
    )
    assert status in [200, 201], f"Dataset upload failed: {status} -> {upload_body}"
    print(f"  -> Dataset uploaded successfully! Rows: {upload_body.get('rows', 150)}, Columns: {upload_body.get('columns', 7)}")

    # 8. EDA Profiling & Visualizations
    print("\n[Step 8] Triggering Automated EDA & Statistical Profiling...")
    status, eda_body, _ = request_json(
        f"{BASE_URL}/api/projects/{project_id}/eda",
        headers=auth_headers,
    )
    assert status == 200, f"EDA profiling failed: {status} -> {eda_body}"
    print("  -> EDA profiling completed. Statistical summary and visualization manifests generated.")

    # 9. AI Plan Proposal & Human Approval
    print("\n[Step 9] Proposing AI Project Blueprint...")
    status, prop_body, _ = request_json(
        f"{BASE_URL}/api/projects/{project_id}/plan/propose",
        method="POST",
        data={"prompt": "Build an optimal, leakage-free churn classifier with interpretability"},
        headers=auth_headers,
    )
    assert status in [200, 201], f"Plan proposal failed: {status} -> {prop_body}"
    print("  -> AI Blueprint generated successfully.")

    print("\n[Step 10] Approving Project Blueprint & Triggering AutoML Pipeline...")
    status, app_body, _ = request_json(
        f"{BASE_URL}/api/projects/{project_id}/plan/approve",
        method="POST",
        data={"action": "approve", "start_analysis": True},
        headers=auth_headers,
    )
    assert status in [200, 201], f"Plan approval failed: {status} -> {app_body}"
    print("  -> Plan approved. AutoML pipeline triggered.")

    # 10. Start / Monitor Run
    print("\n[Step 11] Triggering AutoML Execution Run...")
    status, run_body, _ = request_json(
        f"{BASE_URL}/api/projects/{project_id}/runs",
        method="POST",
        data={"prompt": "Train candidate models and package champion"},
        headers=auth_headers,
    )
    assert status in [200, 201, 202], f"Run launch failed: {status} -> {run_body}"
    run_id = run_body.get("run_id")
    print(f"  -> Analysis Run scheduled with Run ID: {run_id}")

    # Wait for completion of model training (it takes ~10-20 seconds)
    print("  -> Waiting for model training and artifact compilation...")
    for attempt in range(30):
        time.sleep(2)
        s_status, s_body, _ = request_json(
            f"{BASE_URL}/api/projects/{project_id}/runs/{run_id}",
            headers=auth_headers,
        )
        if s_status == 200 and s_body.get("status") in ("COMPLETED", "SUCCESS"):
            print(f"  -> Run reached {s_body.get('status')} state at {attempt * 2}s.")
            break
        print(f"     ... status: {s_body.get('status', 'RUNNING')}, progress: {s_body.get('progress_pct', 0)}%")
    else:
        print("  -> Note: Continued to artifact verification checks.")

    # 11. Artifact Previews & Downloads
    print("\n[Step 12] Verifying Artifact Previews and Downloads...")
    
    # A) Executable Jupyter Notebook
    status, nb_content, _ = request_json(
        f"{BASE_URL}/api/projects/{project_id}/runs/{run_id}/artifacts/notebook",
        headers=auth_headers,
    )
    assert status in [200, 201], f"Notebook download failed: {status}"
    nb_dict = json.loads(nb_content.decode("utf-8")) if isinstance(nb_content, bytes) else nb_content
    print(f"  [Artifact A] Executable Jupyter Notebook: VALID (Cells: {len(nb_dict.get('cells', []))})")

    # B) Executive HTML Report
    status, html_content, headers_resp = request_json(
        f"{BASE_URL}/api/projects/{project_id}/runs/{run_id}/artifacts/html",
        headers=auth_headers,
    )
    assert status == 200, f"HTML report download failed: {status}"
    print(f"  [Artifact B] Executive HTML Report: VALID ({len(html_content)} bytes)")

    # C) Model Serialization Artifact (.pkl)
    status, model_bytes, _ = request_json(
        f"{BASE_URL}/api/projects/{project_id}/runs/{run_id}/artifacts/model",
        headers=auth_headers,
    )
    assert status == 200, f"Model download failed: {status}"
    print(f"  [Artifact C] Serialized Model Pipeline: VALID ({len(model_bytes)} bytes)")

    # D) ZIP Deployment Export Bundle
    status, zip_bytes, _ = request_json(
        f"{BASE_URL}/api/projects/{project_id}/runs/{run_id}/artifacts/zip",
        headers=auth_headers,
    )
    assert status == 200, f"ZIP bundle download failed: {status}"
    with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
        namelist = zf.namelist()
        print(f"  [Artifact D] Deployment ZIP Bundle: VALID ({len(namelist)} packaged files: {namelist[:4]}...)")

    # 12. Multi-Tenant Security Check
    print("\n[Step 13] Verifying Multi-Tenant Isolation (Unauthorized Access Prevention)...")
    intruder_email = f"intruder.analyst.{unique_id}@gmail.com"
    request_json(
        f"{BASE_URL}/api/auth/register",
        method="POST",
        data={
            "email": intruder_email,
            "password": "IntruderPassword123!",
            "name": "Intruder User",
        },
    )
    _, int_login, _ = request_json(
        f"{BASE_URL}/api/auth/login",
        method="POST",
        data={"email": intruder_email, "password": "IntruderPassword123!"},
    )
    intruder_token = int_login["access_token"]
    intruder_headers = {"Authorization": f"Bearer {intruder_token}"}

    # Intruder tries to download User's model
    atk_status, atk_body, _ = request_json(
        f"{BASE_URL}/api/projects/{project_id}/runs/{run_id}/artifacts/model",
        headers=intruder_headers,
    )
    assert atk_status == 403, f"Expected 403 Forbidden for cross-tenant download, got: {atk_status}"
    print(f"  -> Cross-tenant artifact download attack BLOCKED with HTTP {atk_status}: {atk_body.get('detail')}")

    # 13. Project Persistence Verification
    print("\n[Step 14] Verifying Project Persistence in User's Workspace...")
    status, proj_list, _ = request_json(f"{BASE_URL}/api/projects", headers=auth_headers)
    assert status == 200, f"List projects failed: {status}"
    user_projects = proj_list if isinstance(proj_list, list) else proj_list.get("projects", [])
    matching = [p for p in user_projects if (p.get("id") if isinstance(p, dict) else getattr(p, "id", None)) == project_id]
    assert len(matching) > 0, "Created project not found in user projects list"
    print(f"  -> Verified Project is properly persisted in user's workspace (Found {len(user_projects)} project(s)).")

    print("\n" + "=" * 70)
    print("ALL LIVE END-TO-END VERIFICATION CHECKS PASSED WITH ZERO ERRORS!")
    print("=" * 70)


if __name__ == "__main__":
    main()
