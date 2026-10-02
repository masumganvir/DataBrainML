"""DataWise AI — Unified Object Storage Service (S3 / MinIO / Local Fallback)

Provides production-ready S3 / MinIO object storage with:
  - Structured enterprise key schemas: projects/{project_id}/{category}/{uuid}_{filename}
  - Presigned URL generation for secure, direct downloads
  - Automatic bucket initialization
  - Resilient local disk fallback for seamless local tests and dev mode
"""

from __future__ import annotations

import io
import os
import uuid
from pathlib import Path
from typing import BinaryIO, Optional, Union
from loguru import logger

from app.config.settings import get_settings

try:
    import boto3
    from botocore.client import Config
    from botocore.exceptions import ClientError, EndpointConnectionError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False


class StorageService:
    """Enterprise Object Storage abstraction supporting AWS S3, MinIO, and Local Fallback."""

    def __init__(self):
        self.settings = get_settings()
        self.endpoint = self.settings.s3_endpoint
        self.bucket = self.settings.s3_bucket
        self.access_key = self.settings.s3_access_key
        self.secret_key = self.settings.s3_secret_key
        self.region = self.settings.s3_region
        self.use_ssl = self.settings.s3_use_ssl

        self._s3_client = None
        self._init_client()

    def _init_client(self):
        if not BOTO3_AVAILABLE:
            logger.warning("boto3 is not available. Object storage running in Local Fallback mode.")
            return

        import socket
        from urllib.parse import urlparse

        # Quick check if S3 endpoint is reachable within 200ms
        try:
            parsed = urlparse(self.endpoint)
            host = parsed.hostname or "localhost"
            port = parsed.port or (443 if parsed.scheme == "https" else 80)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.2)
            sock.connect((host, port))
            sock.close()
        except Exception:
            # MinIO / S3 offline; use instant local storage
            self._s3_client = None
            return

        try:
            self._s3_client = boto3.client(
                "s3",
                endpoint_url=self.endpoint,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=self.region,
                config=Config(
                    signature_version="s3v4",
                    s3={"addressing_style": "path"},
                    connect_timeout=0.5,
                    read_timeout=0.5,
                    retries={"max_attempts": 0},
                ),
            )
            self._ensure_buckets()
        except Exception as e:
            logger.warning(f"Could not connect to S3/MinIO at {self.endpoint}: {e}. Falling back to local storage.")
            self._s3_client = None


    def _ensure_buckets(self):
        if not self._s3_client:
            return
        buckets = [self.bucket, self.settings.model_storage_bucket, self.settings.artifact_storage_bucket]
        for b in buckets:
            try:
                self._s3_client.head_bucket(Bucket=b)
            except Exception:
                try:
                    self._s3_client.create_bucket(Bucket=b)
                    logger.info(f"Created S3 bucket: {b}")
                except Exception as ex:
                    logger.warning(f"Could not initialize S3 bucket '{b}': {ex}")

    def build_project_key(self, project_id: str, category: str, filename: str) -> str:
        """Create structured hierarchical storage key."""
        unique_prefix = uuid.uuid4().hex[:8]
        safe_filename = filename.replace(" ", "_")
        return f"projects/{project_id}/{category}/{unique_prefix}_{safe_filename}"

    def upload_file(
        self,
        key: str,
        data: Union[bytes, BinaryIO],
        content_type: str = "application/octet-stream",
        bucket: Optional[str] = None,
    ) -> str:
        """Upload binary data or file stream to object storage or local fallback."""
        target_bucket = bucket or self.bucket

        # Convert to bytes if binary stream
        if isinstance(data, (io.BytesIO, BinaryIO)) or hasattr(data, "read"):
            data_bytes = data.read()
        else:
            data_bytes = data

        if self._s3_client:
            try:
                self._s3_client.put_object(
                    Bucket=target_bucket,
                    Key=key,
                    Body=data_bytes,
                    ContentType=content_type,
                )
                return key
            except Exception as e:
                logger.warning(f"S3 upload failed for {key}: {e}. Persisting to local fallback.")

        # Local fallback
        local_path = Path(self.settings.storage_path) / key
        local_path.parent.mkdir(parents=True, exist_ok=True)
        with open(local_path, "wb") as f:
            f.write(data_bytes)
        return key

    def get_file_bytes(self, key: str, bucket: Optional[str] = None) -> bytes:
        """Retrieve binary content of file."""
        target_bucket = bucket or self.bucket

        if self._s3_client:
            try:
                resp = self._s3_client.get_object(Bucket=target_bucket, Key=key)
                return resp["Body"].read()
            except Exception as e:
                logger.debug(f"S3 get_object failed: {e}. Checking local fallback.")

        # Local fallback
        local_path = Path(self.settings.storage_path) / key
        if local_path.exists():
            with open(local_path, "rb") as f:
                return f.read()

        raise FileNotFoundError(f"Storage object '{key}' not found in bucket or local storage.")

    def generate_presigned_url(self, key: str, bucket: Optional[str] = None, expires_in: int = 3600) -> str:
        """Generate presigned download URL."""
        target_bucket = bucket or self.bucket

        if self._s3_client:
            try:
                url = self._s3_client.generate_presigned_url(
                    ClientMethod="get_object",
                    Params={"Bucket": target_bucket, "Key": key},
                    ExpiresIn=expires_in,
                )
                return url
            except Exception as e:
                logger.warning(f"Could not generate presigned URL for {key}: {e}")

        # Local fallback URL
        return f"/api/artifacts/download?key={key}"

    def delete_file(self, key: str, bucket: Optional[str] = None) -> bool:
        """Delete object from storage."""
        target_bucket = bucket or self.bucket
        deleted = False

        if self._s3_client:
            try:
                self._s3_client.delete_object(Bucket=target_bucket, Key=key)
                deleted = True
            except Exception as e:
                logger.warning(f"S3 delete failed: {e}")

        local_path = Path(self.settings.storage_path) / key
        if local_path.exists():
            local_path.unlink()
            deleted = True

        return deleted

    def check_health(self) -> dict:
        """Verify object storage connectivity for health probes."""
        if not self._s3_client:
            return {"status": "ok", "mode": "local_fallback", "endpoint": self.endpoint}
        try:
            self._s3_client.head_bucket(Bucket=self.bucket)
            return {"status": "ok", "mode": "s3_connected", "endpoint": self.endpoint}
        except Exception as e:
            return {"status": "degraded", "mode": "local_fallback_active", "error": str(e)}


_storage_singleton: Optional[StorageService] = None


def get_storage_service() -> StorageService:
    """Return cached storage singleton."""
    global _storage_singleton
    if _storage_singleton is None:
        _storage_singleton = StorageService()
    return _storage_singleton
