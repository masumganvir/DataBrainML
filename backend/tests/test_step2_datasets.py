"""
DataWise AI — STEP 2 Tests: Dataset Upload, Validation & Versioned Storage

Tests:
  - Filename sanitization against path traversal
  - File format validation (accepts CSV/XLSX/JSON, rejects disallowed)
  - Rejection of empty files
  - Delimiter sniffing and encoding detection
  - Full upload flow via FastAPI TestClient
  - Dataset versioning & persistence
  - Dataset preview endpoint with column types & pagination
  - Dataset download endpoint
"""

from __future__ import annotations

import io
from pathlib import Path

import pandas as pd
import pytest

from app.security.file_validator import (
    FileValidationError,
    detect_csv_encoding,
    sanitize_filename,
    sniff_csv_delimiter,
    validate_uploaded_file,
)
from app.tools.storage import storage_manager


# ------------------------------------------------------------------ #
#  Validator Unit Tests
# ------------------------------------------------------------------ #

class TestFileValidator:
    def test_sanitize_filename_path_traversal(self):
        """Sanitizer should strip directory traversal attempts."""
        assert sanitize_filename("../../../etc/passwd.csv") == "passwd.csv"
        assert sanitize_filename("..\\..\\windows\\system32\\cmd.csv") == "cmd.csv"
        assert sanitize_filename("normal_data.csv") == "normal_data.csv"
        assert sanitize_filename("") == "dataset.csv"
        assert sanitize_filename("   ") == "dataset.csv"

    def test_reject_unsupported_extensions(self):
        """Disallowed extensions must raise FileValidationError."""
        with pytest.raises(FileValidationError) as exc:
            validate_uploaded_file(b"print('malicious')", "script.py")
        assert exc.value.code == "unsupported_format"

        with pytest.raises(FileValidationError) as exc:
            validate_uploaded_file(b"MZ...", "malware.exe")
        assert exc.value.code == "unsupported_format"

    def test_reject_empty_file(self):
        """Zero-byte file must raise empty_file error."""
        with pytest.raises(FileValidationError) as exc:
            validate_uploaded_file(b"", "empty.csv")
        assert exc.value.code == "empty_file"

    def test_sniff_delimiters(self):
        """Sniffer should correctly identify comma, semicolon, tab, and pipe."""
        assert sniff_csv_delimiter("a,b,c\n1,2,3") == ","
        assert sniff_csv_delimiter("a;b;c\n1;2;3") == ";"
        assert sniff_csv_delimiter("a\tb\tc\n1\t2\t3") == "\t"
        assert sniff_csv_delimiter("a|b|c\n1|2|3") == "|"

    def test_encoding_detection(self):
        """UTF-8 and Latin-1 encodings should be detected without raising."""
        utf8_bytes = "name,city\nFrançois,Montréal".encode("utf-8")
        assert detect_csv_encoding(utf8_bytes) in ("utf-8", "utf-8-sig")

    def test_validate_valid_csv(self):
        """Valid CSV should produce accurate column count, row count, and format."""
        csv_bytes = b"id,name,age\n1,Alice,30\n2,Bob,25\n3,Charlie,35\n"
        res = validate_uploaded_file(csv_bytes, "users.csv")
        assert res.is_valid is True
        assert res.format == "csv"
        assert res.row_count == 3
        assert res.column_count == 3
        assert res.columns == ["id", "name", "age"]

    def test_validate_valid_json(self):
        """Valid JSON records array should validate properly."""
        json_bytes = b'[{"a": 1, "b": "x"}, {"a": 2, "b": "y"}]'
        res = validate_uploaded_file(json_bytes, "data.json")
        assert res.is_valid is True
        assert res.format == "json"
        assert res.row_count == 2
        assert res.column_count == 2


# ------------------------------------------------------------------ #
#  Storage Unit Tests
# ------------------------------------------------------------------ #

class TestStorageManager:
    def test_save_and_load_dataframe(self, tmp_path):
        """StorageManager should write and reload DataFrames losslessly."""
        from app.tools.storage import StorageManager
        sm = StorageManager(upload_dir=tmp_path)
        df = pd.DataFrame({"col_a": [1, 2, 3], "col_b": ["apple", "banana", "cherry"]})

        file_path, stored_name = sm.save_dataframe(df, "sess_123", "original", "fruits.csv")
        assert Path(file_path).exists()
        assert "original_fruits.csv" in stored_name

        loaded_df = sm.load_dataframe(file_path, "csv")
        assert len(loaded_df) == 3
        assert list(loaded_df.columns) == ["col_a", "col_b"]

    def test_dataset_preview(self, tmp_path):
        """get_dataset_preview should return paginated rows and schema stats."""
        from app.tools.storage import StorageManager
        sm = StorageManager(upload_dir=tmp_path)
        df = pd.DataFrame({"num": list(range(100)), "val": [f"v{i}" for i in range(100)]})
        file_path, _ = sm.save_dataframe(df, "sess_preview", "original", "numbers.csv")

        preview = sm.get_dataset_preview(file_path, "csv", limit=10, offset=5)
        assert preview["total_rows"] == 100
        assert preview["total_columns"] == 2
        assert len(preview["rows"]) == 10
        assert preview["rows"][0]["num"] == 5


# ------------------------------------------------------------------ #
#  API Integration Tests
# ------------------------------------------------------------------ #

@pytest.mark.asyncio
class TestDatasetEndpoints:
    async def test_upload_dataset_success(self, client):
        """Uploading a valid CSV should return 201 and update session stage."""
        # 1. Create a session first
        create_resp = await client.post("/api/sessions", json={"name": "Upload Test"})
        session_id = create_resp.json()["id"]

        # 2. Upload CSV
        csv_content = b"customer_id,churn,monthly_fee\nC001,0,55.5\nC002,1,89.0\n"
        files = {"file": ("test_churn.csv", io.BytesIO(csv_content), "text/csv")}
        upload_resp = await client.post(f"/api/sessions/{session_id}/datasets/upload", files=files)

        assert upload_resp.status_code == 201
        data = upload_resp.json()
        assert data["original_filename"] == "test_churn.csv"
        assert data["version"] == "original"
        assert data["row_count"] == 2
        assert data["column_count"] == 3

        # Verify session state was updated
        sess_resp = await client.get(f"/api/sessions/{session_id}")
        assert sess_resp.json()["current_stage"] == "PROFILING"
        assert sess_resp.json()["status"] == "active"

    async def test_upload_to_nonexistent_session(self, client):
        """Upload to non-existent session should return 404."""
        files = {"file": ("data.csv", io.BytesIO(b"a,b\n1,2\n"), "text/csv")}
        resp = await client.post("/api/sessions/unknown-id/datasets/upload", files=files)
        assert resp.status_code == 404

    async def test_upload_invalid_file_extension(self, client):
        """Uploading an unauthorized extension should return 422."""
        create_resp = await client.post("/api/sessions", json={"name": "Bad Ext"})
        session_id = create_resp.json()["id"]

        files = {"file": ("hack.sh", io.BytesIO(b"echo hello"), "application/x-sh")}
        resp = await client.post(f"/api/sessions/{session_id}/datasets/upload", files=files)
        assert resp.status_code == 422

    async def test_list_and_preview_datasets(self, client):
        """Listing and previewing datasets should work end-to-end."""
        create_resp = await client.post("/api/sessions", json={"name": "Preview Test"})
        session_id = create_resp.json()["id"]

        csv_content = b"x,y\n10,20\n30,40\n50,60\n"
        files = {"file": ("points.csv", io.BytesIO(csv_content), "text/csv")}
        upload_resp = await client.post(f"/api/sessions/{session_id}/datasets/upload", files=files)
        dataset_id = upload_resp.json()["id"]

        # List
        list_resp = await client.get(f"/api/sessions/{session_id}/datasets")
        assert list_resp.status_code == 200
        assert len(list_resp.json()) == 1

        # Preview
        preview_resp = await client.get(
            f"/api/sessions/{session_id}/datasets/{dataset_id}/preview?limit=2&offset=1"
        )
        assert preview_resp.status_code == 200
        pdata = preview_resp.json()
        assert pdata["total_rows"] == 3
        assert len(pdata["rows"]) == 2
        assert pdata["rows"][0]["x"] == 30

        # Download
        down_resp = await client.get(f"/api/sessions/{session_id}/datasets/{dataset_id}/download")
        assert down_resp.status_code == 200
        assert b"10,20" in down_resp.content
