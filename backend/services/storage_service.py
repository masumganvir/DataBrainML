"""
DataWise AI — Storage Service Abstraction
Implements Prompt Section 14:
- S3 / MinIO / Supabase Storage / Local filesystem abstraction
- Exposes: upload(), download(), delete(), generate_signed_url(), exists(), checksum()
- Decouples application and agents from specific storage vendors
"""

from __future__ import annotations

import hashlib
import io
import os
from pathlib import Path
from typing import Any, BinaryIO, Optional, Union
from loguru import logger

try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:
    boto3 = None
    ClientError = Exception

from database.supabase import get_supabase_client, get_supabase_admin_client, is_supabase_enabled


class StorageService:
    """Enterprise Storage Service for datasets, models, reports, and visualization artifacts."""

    def __init__(self):
        self.provider = os.getenv("OBJECT_STORAGE_PROVIDER", "local").lower()
        self.bucket = os.getenv("OBJECT_STORAGE_BUCKET") or os.getenv("S3_BUCKET", "datawise-artifacts")
        self.endpoint = os.getenv("OBJECT_STORAGE_ENDPOINT") or os.getenv("S3_ENDPOINT", "")
        self.local_root = Path(os.getenv("STORAGE_PATH", "./data/uploads")).resolve()
        self.local_root.mkdir(parents=True, exist_ok=True)
        self._s3_client: Optional[Any] = None

    def _get_s3(self):
        if self._s3_client is None and boto3 is not None and self.endpoint:
            access_key = os.getenv("OBJECT_STORAGE_ACCESS_KEY") or os.getenv("S3_ACCESS_KEY")
            secret_key = os.getenv("OBJECT_STORAGE_SECRET_KEY") or os.getenv("S3_SECRET_KEY")
            region = os.getenv("S3_REGION", "us-east-1")
            self._s3_client = boto3.client(
                "s3",
                endpoint_url=self.endpoint,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region,
            )
        return self._s3_client

    def upload(
        self,
        file_source: Union[str, Path, bytes, BinaryIO],
        storage_key: str,
        content_type: str = "application/octet-stream",
    ) -> str:
        """
        Uploads an artifact to storage.
        Returns the persistent storage key / path.
        """
        # Read bytes
        if isinstance(file_source, (str, Path)):
            with open(file_source, "rb") as f:
                data = f.read()
        elif isinstance(file_source, bytes):
            data = file_source
        elif hasattr(file_source, "read"):
            data = file_source.read()
        else:
            raise ValueError(f"Unsupported file source type: {type(file_source)}")

        # 1. Supabase Storage if configured
        if is_supabase_enabled():
            client = get_supabase_admin_client() or get_supabase_client()
            if client is not None:
                try:
                    # Upload to Supabase bucket
                    res = client.storage.from_(self.bucket).upload(
                        path=storage_key,
                        file=data,
                        file_options={"content-type": content_type, "upsert": "true"},
                    )
                    logger.info(f"[StorageService] Uploaded {storage_key} to Supabase bucket '{self.bucket}'")
                    return storage_key
                except Exception as exc:
                    logger.warning(f"[StorageService] Supabase upload failed, falling back to local: {exc}")

        # 2. S3 / MinIO if configured
        s3 = self._get_s3()
        if s3 is not None:
            try:
                s3.put_object(
                    Bucket=self.bucket,
                    Key=storage_key,
                    Body=data,
                    ContentType=content_type,
                )
                logger.info(f"[StorageService] Uploaded {storage_key} to S3/MinIO bucket '{self.bucket}'")
                return storage_key
            except Exception as exc:
                logger.warning(f"[StorageService] S3 upload failed, falling back to local: {exc}")

        # 3. Local filesystem fallback
        dest = self.local_root / storage_key
        dest.parent.mkdir(parents=True, exist_ok=True)
        with open(dest, "wb") as f:
            f.write(data)
        logger.debug(f"[StorageService] Stored {storage_key} locally at {dest}")
        return storage_key

    def download(self, storage_key: str, target_path: Optional[Union[str, Path]] = None) -> Union[Path, bytes]:
        """Downloads artifact from storage to target local path or returns raw bytes."""
        # Check local filesystem first
        local_candidate = self.local_root / storage_key
        if local_candidate.exists() and local_candidate.is_file():
            if target_path is not None:
                target = Path(target_path)
                target.parent.mkdir(parents=True, exist_ok=True)
                if local_candidate != target:
                    target.write_bytes(local_candidate.read_bytes())
                return target
            return local_candidate.read_bytes()

        # Check Supabase Storage
        if is_supabase_enabled():
            client = get_supabase_admin_client() or get_supabase_client()
            if client is not None:
                try:
                    bytes_data = client.storage.from_(self.bucket).download(storage_key)
                    if target_path is not None:
                        target = Path(target_path)
                        target.parent.mkdir(parents=True, exist_ok=True)
                        target.write_bytes(bytes_data)
                        return target
                    return bytes_data
                except Exception as exc:
                    logger.warning(f"[StorageService] Supabase download error: {exc}")

        # Check S3
        s3 = self._get_s3()
        if s3 is not None:
            try:
                if target_path is not None:
                    target = Path(target_path)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    s3.download_file(self.bucket, storage_key, str(target))
                    return target
                response = s3.get_object(Bucket=self.bucket, Key=storage_key)
                return response["Body"].read()
            except Exception as exc:
                logger.warning(f"[StorageService] S3 download error: {exc}")

        raise FileNotFoundError(f"Storage artifact '{storage_key}' not found.")

    def generate_signed_url(self, storage_key: str, expires_in_seconds: int = 3600) -> str:
        """Generates a secure, short-lived signed URL for download authorization."""
        # 1. Supabase Storage signed URL
        if is_supabase_enabled():
            client = get_supabase_admin_client() or get_supabase_client()
            if client is not None:
                try:
                    signed_res = client.storage.from_(self.bucket).create_signed_url(
                        path=storage_key,
                        expires_in=expires_in_seconds,
                    )
                    if isinstance(signed_res, dict) and "signedURL" in signed_res:
                        return signed_res["signedURL"]
                    elif hasattr(signed_res, "signed_url"):
                        return getattr(signed_res, "signed_url")
                except Exception as exc:
                    logger.debug(f"Supabase signed URL fallback: {exc}")

        # 2. S3 signed URL
        s3 = self._get_s3()
        if s3 is not None:
            try:
                url = s3.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": self.bucket, "Key": storage_key},
                    ExpiresIn=expires_in_seconds,
                )
                return url
            except Exception as exc:
                logger.debug(f"S3 presigned URL fallback: {exc}")

        # 3. Direct backend proxy URL
        return f"/api/artifacts/download?key={storage_key}"

    def exists(self, storage_key: str) -> bool:
        """Verifies if artifact exists in storage."""
        if (self.local_root / storage_key).exists():
            return True
        s3 = self._get_s3()
        if s3 is not None:
            try:
                s3.head_object(Bucket=self.bucket, Key=storage_key)
                return True
            except Exception:
                return False
        return False

    def checksum(self, target: Union[str, Path, bytes]) -> str:
        """Calculates SHA-256 checksum of stored artifact (storage_key, path, or raw bytes)."""
        if isinstance(target, bytes):
            return hashlib.sha256(target).hexdigest()

        p = Path(target)
        if p.exists() and p.is_file():
            h = hashlib.sha256()
            with open(p, "rb") as f:
                while chunk := f.read(65536):
                    h.update(chunk)
            return h.hexdigest()

        local_file = self.local_root / str(target)
        if local_file.exists() and local_file.is_file():
            h = hashlib.sha256()
            with open(local_file, "rb") as f:
                while chunk := f.read(65536):
                    h.update(chunk)
            return h.hexdigest()
        return ""

    def delete(self, storage_key: str) -> bool:
        """Deletes artifact from storage."""
        local_file = self.local_root / storage_key
        if local_file.exists():
            try:
                local_file.unlink()
                return True
            except Exception:
                return False
        return False


storage_service = StorageService()
