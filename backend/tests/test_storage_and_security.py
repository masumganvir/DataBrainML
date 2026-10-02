"""DataWise AI — Storage Service & File Security Tests."""

import pytest
from app.storage.security import sanitize_filename, validate_file_content
from app.storage.service import get_storage_service


def test_sanitize_filename():
    bad_name = "../../../etc/passwd"
    clean = sanitize_filename(bad_name)
    assert ".." not in clean
    assert clean == "passwd"

    shell_name = "dataset;rm -rf /;.csv"
    clean_shell = sanitize_filename(shell_name)
    assert ";" not in clean_shell


def test_validate_file_content():
    # Valid CSV
    valid, msg = validate_file_content(b"col1,col2\n1,2", "data.csv")
    assert valid is True

    # Bad extension
    invalid_ext, _ = validate_file_content(b"content", "script.sh")
    assert invalid_ext is False

    # Empty file
    invalid_empty, _ = validate_file_content(b"", "empty.csv")
    assert invalid_empty is False


def test_storage_service_upload_and_download():
    storage = get_storage_service()
    key = storage.build_project_key("proj_test", "datasets", "sample.csv")
    data = b"id,name,value\n1,alpha,10.5\n2,beta,20.0\n"

    uploaded_key = storage.upload_file(key, data, content_type="text/csv")
    assert uploaded_key == key

    retrieved = storage.get_file_bytes(key)
    assert retrieved == data

    # Cleanup
    storage.delete_file(key)
