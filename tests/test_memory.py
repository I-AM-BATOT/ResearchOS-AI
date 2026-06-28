"""
tests/test_memory.py
Tests for the persistent memory store: store / retrieve / update / delete /
semantic search, using whichever backend is available (chromadb or SQLite
fallback) -- the public MemoryStore API must behave identically either way.
"""
import uuid

import pytest

from memory.memory_store import MemoryStore


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setenv("MEMORY_DIR", str(tmp_path / "memdb"))
    return MemoryStore()


class TestMemoryStore:
    def test_remember_and_recall(self, store):
        store.remember("paper_summary", "Transformers revolutionized NLP with self-attention.")
        store.remember("paper_summary", "CNNs are widely used for image classification.")
        results = store.recall("self-attention transformer architecture", top_k=1)
        assert len(results) >= 1

    def test_get_and_update(self, store):
        record = store.remember("observation", "Initial observation text.")
        fetched = store.get(record.record_id)
        assert fetched is not None
        assert fetched.text == "Initial observation text."

        updated = store.update(record.record_id, text="Updated observation text.")
        assert updated is True
        assert store.get(record.record_id).text == "Updated observation text."

    def test_delete(self, store):
        record = store.remember("observation", "To be deleted.")
        assert store.forget(record.record_id) is True
        assert store.get(record.record_id) is None

    def test_delete_nonexistent_returns_false(self, store):
        assert store.forget(str(uuid.uuid4())) is False

    def test_filter_by_kind(self, store):
        store.remember("paper_summary", "Summary A")
        store.remember("research_interest", "Interest B")
        records = store.all_records(kind="paper_summary")
        assert all(r.kind == "paper_summary" for r in records)
        assert len(records) == 1

    def test_failover_when_backend_raises(self, store):
        """Regression test: a real-world failure mode is ChromaDB's default
        embedding function trying (and timing out) to download its model on
        a restricted network -- raising ConnectTimeout from inside upsert().
        Memory writes must never crash the caller; MemoryStore must fail
        over to SQLite and keep working."""
        from unittest.mock import patch

        with patch.object(store.backend, "store", side_effect=ConnectionError(
                "ConnectTimeout: _ssl.c:1063: The handshake operation timed out in upsert.")):
            record = store.remember("paper_summary", "Should survive the simulated timeout.")
        assert record is not None
        assert store.backend_name.startswith("sqlite")
