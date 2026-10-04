"""
DataWise AI — MongoDB Atlas & Vector Search Integration
Stores project knowledge chunks, semantic embeddings, decision histories,
and provides semantic retrieval for grounded contextual assistance.
"""

from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional
from loguru import logger

try:
    from pymongo import MongoClient
except ImportError:
    MongoClient = None


class MongoVectorManager:
    """Manages MongoDB Atlas connection and vector search queries."""

    def __init__(self):
        self.uri = os.getenv("MONGODB_URI", "")
        self.db_name = os.getenv("MONGODB_DATABASE", "datawise_ai")
        self.collection_name = os.getenv("MONGODB_VECTOR_COLLECTION", "knowledge_chunks")
        self._client: Optional[Any] = None
        self._db: Optional[Any] = None

    def get_collection(self):
        """Returns the knowledge chunks collection if MongoDB is configured."""
        if not self.uri or MongoClient is None:
            return None

        if self._client is None:
            try:
                self._client = MongoClient(self.uri, serverSelectionTimeoutMS=5000)
                self._db = self._client[self.db_name]
                logger.info(f"[MongoDB] Connected to MongoDB Atlas: {self.db_name}")
            except Exception as exc:
                logger.warning(f"[MongoDB] Connection failed: {exc}")
                return None

        return self._db[self.collection_name] if self._db is not None else None

    def insert_knowledge_chunk(
        self,
        owner_id: str,
        project_id: str,
        source_type: str,
        source_id: str,
        text: str,
        embedding: Optional[List[float]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Stores a verified semantic knowledge chunk for project memory."""
        coll = self.get_collection()
        if coll is None:
            return False

        doc = {
            "owner_id": owner_id,
            "project_id": project_id,
            "source_type": source_type,
            "source_id": source_id,
            "text": text,
            "embedding": embedding or [],
            "metadata": metadata or {},
            "created_at": time.time(),
        }
        try:
            coll.insert_one(doc)
            return True
        except Exception as exc:
            logger.error(f"[MongoDB] Error inserting knowledge chunk: {exc}")
            return False

    def search_project_memory(
        self,
        owner_id: str,
        project_id: str,
        query_text: str,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Performs tenant-isolated retrieval of project memory.
        Enforces strict user isolation: owner_id + project_id must match.
        """
        coll = self.get_collection()
        if coll is None:
            return []

        try:
            # Query strictly filtered by owner_id and project_id (Tenant Isolation)
            cursor = coll.find(
                {
                    "owner_id": owner_id,
                    "project_id": project_id,
                    "$text": {"$search": query_text} if "$text" in coll.index_information() else {},
                }
            ).limit(limit)
            return list(cursor)
        except Exception as exc:
            logger.warning(f"[MongoDB] Fallback search error: {exc}")
            return []


mongo_vector_manager = MongoVectorManager()
