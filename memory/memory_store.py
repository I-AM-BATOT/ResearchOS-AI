"""
memory/memory_store.py
Persistent memory for ResearchOS AI.

Backend selection:
- If `chromadb` is importable -> use it for true semantic (embedding-based)
  search over stored memories.
- Otherwise -> fall back to a SQLite store with a lightweight TF-IDF-ish
  keyword search, so memory still works with zero extra native dependencies
  (chromadb pulls in onnxruntime etc., which may not be available in every
  deployment target like minimal Cloud Run containers).

Both backends implement the exact same interface (store/retrieve/update/
delete/search) so the rest of the app (agents, MemoryAgent, the Memory
Dashboard page) never needs to know which one is active.
"""
from __future__ import annotations

import json
import re
import sqlite3
import uuid
from collections import Counter
from pathlib import Path
from typing import Optional

from core.config import settings, get_logger
from core.models import MemoryRecord

logger = get_logger("memory.store")

_CHROMA_AVAILABLE = True
try:
    import chromadb
except ImportError:
    _CHROMA_AVAILABLE = False


class BaseMemoryBackend:
    def store(self, record: MemoryRecord) -> None:
        raise NotImplementedError

    def get(self, record_id: str) -> Optional[MemoryRecord]:
        raise NotImplementedError

    def update(self, record_id: str, text: Optional[str] = None, metadata: Optional[dict] = None) -> bool:
        raise NotImplementedError

    def delete(self, record_id: str) -> bool:
        raise NotImplementedError

    def search(self, query: str, top_k: int = 5, kind: Optional[str] = None) -> list[MemoryRecord]:
        raise NotImplementedError

    def list_all(self, kind: Optional[str] = None) -> list[MemoryRecord]:
        raise NotImplementedError


# --------------------------------------------------------------------------- #
# SQLite backend (always available, zero native deps)
# --------------------------------------------------------------------------- #

_STOPWORDS = {
    "the", "a", "an", "of", "in", "on", "to", "for", "and", "or", "is",
    "are", "was", "were", "this", "that", "with", "as", "by", "it", "be",
}


def _tokenize(text: str) -> list[str]:
    words = re.findall(r"[a-zA-Z0-9]+", text.lower())
    return [w for w in words if w not in _STOPWORDS and len(w) > 1]


class SQLiteMemoryBackend(BaseMemoryBackend):
    def __init__(self, db_path: str) -> None:
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS memory (
                record_id TEXT PRIMARY KEY,
                kind TEXT,
                text TEXT,
                metadata TEXT,
                created_at TEXT
            )
            """
        )
        self.conn.commit()
        logger.info("SQLite memory backend ready at %s (chromadb not installed)", db_path)

    def store(self, record: MemoryRecord) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO memory VALUES (?, ?, ?, ?, ?)",
            (record.record_id, record.kind, record.text,
             json.dumps(record.metadata), record.created_at.isoformat()),
        )
        self.conn.commit()

    def get(self, record_id: str) -> Optional[MemoryRecord]:
        row = self.conn.execute(
            "SELECT record_id, kind, text, metadata, created_at FROM memory WHERE record_id = ?",
            (record_id,),
        ).fetchone()
        return self._row_to_record(row) if row else None

    def update(self, record_id: str, text: Optional[str] = None, metadata: Optional[dict] = None) -> bool:
        existing = self.get(record_id)
        if not existing:
            return False
        new_text = text if text is not None else existing.text
        new_meta = {**existing.metadata, **(metadata or {})}
        self.conn.execute(
            "UPDATE memory SET text = ?, metadata = ? WHERE record_id = ?",
            (new_text, json.dumps(new_meta), record_id),
        )
        self.conn.commit()
        return True

    def delete(self, record_id: str) -> bool:
        cur = self.conn.execute("DELETE FROM memory WHERE record_id = ?", (record_id,))
        self.conn.commit()
        return cur.rowcount > 0

    def list_all(self, kind: Optional[str] = None) -> list[MemoryRecord]:
        if kind:
            rows = self.conn.execute(
                "SELECT record_id, kind, text, metadata, created_at FROM memory WHERE kind = ? ORDER BY created_at DESC",
                (kind,),
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT record_id, kind, text, metadata, created_at FROM memory ORDER BY created_at DESC"
            ).fetchall()
        return [self._row_to_record(r) for r in rows]

    def search(self, query: str, top_k: int = 5, kind: Optional[str] = None) -> list[MemoryRecord]:
        """Lightweight keyword-overlap ranking. Not true semantic search, but
        gives reasonable relevance ordering without an embedding model."""
        query_tokens = Counter(_tokenize(query))
        candidates = self.list_all(kind=kind)
        scored = []
        for record in candidates:
            record_tokens = Counter(_tokenize(record.text))
            overlap = sum((query_tokens & record_tokens).values())
            if overlap > 0:
                scored.append((overlap, record))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [record for _, record in scored[:top_k]]

    @staticmethod
    def _row_to_record(row) -> MemoryRecord:
        record_id, kind, text, metadata_json, created_at = row
        return MemoryRecord(
            record_id=record_id,
            kind=kind,
            text=text,
            metadata=json.loads(metadata_json) if metadata_json else {},
            created_at=created_at,
        )


# --------------------------------------------------------------------------- #
# ChromaDB backend (true semantic search, used when available)
# --------------------------------------------------------------------------- #

class ChromaMemoryBackend(BaseMemoryBackend):
    def __init__(self, persist_dir: str, collection_name: str) -> None:
        Path(persist_dir).mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection = self.client.get_or_create_collection(collection_name)
        logger.info("ChromaDB memory backend ready at %s", persist_dir)

    def store(self, record: MemoryRecord) -> None:
        self.collection.upsert(
            ids=[record.record_id],
            documents=[record.text],
            metadatas=[{"kind": record.kind, "created_at": record.created_at.isoformat(), **record.metadata}],
        )

    def get(self, record_id: str) -> Optional[MemoryRecord]:
        result = self.collection.get(ids=[record_id])
        if not result["ids"]:
            return None
        return self._to_record(result["ids"][0], result["documents"][0], result["metadatas"][0])

    def update(self, record_id: str, text: Optional[str] = None, metadata: Optional[dict] = None) -> bool:
        existing = self.get(record_id)
        if not existing:
            return False
        new_text = text if text is not None else existing.text
        new_meta = {**existing.metadata, **(metadata or {}), "kind": existing.kind,
                    "created_at": existing.created_at.isoformat() if not isinstance(existing.created_at, str) else existing.created_at}
        self.collection.upsert(ids=[record_id], documents=[new_text], metadatas=[new_meta])
        return True

    def delete(self, record_id: str) -> bool:
        self.collection.delete(ids=[record_id])
        return True

    def list_all(self, kind: Optional[str] = None) -> list[MemoryRecord]:
        where = {"kind": kind} if kind else None
        result = self.collection.get(where=where)
        return [
            self._to_record(rid, doc, meta)
            for rid, doc, meta in zip(result["ids"], result["documents"], result["metadatas"])
        ]

    def search(self, query: str, top_k: int = 5, kind: Optional[str] = None) -> list[MemoryRecord]:
        where = {"kind": kind} if kind else None
        result = self.collection.query(query_texts=[query], n_results=top_k, where=where)
        if not result["ids"] or not result["ids"][0]:
            return []
        return [
            self._to_record(rid, doc, meta)
            for rid, doc, meta in zip(result["ids"][0], result["documents"][0], result["metadatas"][0])
        ]

    @staticmethod
    def _to_record(record_id: str, text: str, metadata: dict) -> MemoryRecord:
        metadata = dict(metadata or {})
        kind = metadata.pop("kind", "observation")
        created_at = metadata.pop("created_at", None)
        return MemoryRecord(
            record_id=record_id,
            kind=kind,
            text=text,
            metadata=metadata,
            created_at=created_at or MemoryRecord.model_fields["created_at"].default_factory(),
        )


# --------------------------------------------------------------------------- #
# Public facade
# --------------------------------------------------------------------------- #

class MemoryStore:
    """Public API used by MemoryAgent and the Streamlit Memory Dashboard."""

    def __init__(self) -> None:
        if _CHROMA_AVAILABLE:
            try:
                self.backend: BaseMemoryBackend = ChromaMemoryBackend(
                    settings.memory_dir, settings.chroma_collection
                )
                self.backend_name = "chromadb"
            except Exception as exc:
                logger.warning("ChromaDB init failed (%s); falling back to SQLite", exc)
                self.backend = SQLiteMemoryBackend(f"{settings.memory_dir}/memory.sqlite3")
                self.backend_name = "sqlite"
        else:
            self.backend = SQLiteMemoryBackend(f"{settings.memory_dir}/memory.sqlite3")
            self.backend_name = "sqlite"

    def _failover_to_sqlite(self, exc: Exception) -> None:
        """Called when the active backend raises. If we were on ChromaDB, this
        is almost always its default embedding function trying (and failing)
        to download its model from the internet -- e.g. ConnectTimeout on a
        restricted network. Rather than re-attempting that slow network call
        on every subsequent memory write for the rest of the session, we
        permanently switch to the local SQLite backend once and log it."""
        if self.backend_name.startswith("sqlite"):
            return  # already on the fallback path; nothing further to do
        logger.warning(
            "Memory backend '%s' failed (%s: %s) -- switching to the local SQLite "
            "backend for the rest of this session. This is commonly ChromaDB's "
            "default embedding function failing to reach the internet to download "
            "its model; semantic search quality will be reduced to keyword "
            "matching, but the app will keep working.",
            self.backend_name, type(exc).__name__, exc,
        )
        self.backend = SQLiteMemoryBackend(f"{settings.memory_dir}/memory.sqlite3")
        self.backend_name = "sqlite (auto-failover)"

    def _safe_backend_call(self, method_name: str, *args, default=None, **kwargs):
        """Calls self.backend.<method_name>(*args, **kwargs), failing over to
        SQLite and retrying once if the first attempt raises. Never lets a
        memory operation crash the caller -- memory is a supporting feature,
        not part of the critical path for producing an analysis result."""
        try:
            return getattr(self.backend, method_name)(*args, **kwargs)
        except Exception as exc:
            self._failover_to_sqlite(exc)
            try:
                return getattr(self.backend, method_name)(*args, **kwargs)
            except Exception:
                logger.warning("Memory operation '%s' failed even after failover; returning default.", method_name)
                return default

    def remember(self, kind: str, text: str, metadata: Optional[dict] = None) -> MemoryRecord:
        record = MemoryRecord(record_id=str(uuid.uuid4()), kind=kind, text=text, metadata=metadata or {})
        self._safe_backend_call("store", record)
        return record

    def recall(self, query: str, top_k: int = 5, kind: Optional[str] = None) -> list[MemoryRecord]:
        return self._safe_backend_call("search", query, top_k=top_k, kind=kind, default=[])

    def get(self, record_id: str) -> Optional[MemoryRecord]:
        return self._safe_backend_call("get", record_id, default=None)

    def update(self, record_id: str, text: Optional[str] = None, metadata: Optional[dict] = None) -> bool:
        return self._safe_backend_call("update", record_id, text=text, metadata=metadata, default=False)

    def forget(self, record_id: str) -> bool:
        return self._safe_backend_call("delete", record_id, default=False)

    def all_records(self, kind: Optional[str] = None) -> list[MemoryRecord]:
        return self._safe_backend_call("list_all", kind=kind, default=[])


memory_store = MemoryStore()
