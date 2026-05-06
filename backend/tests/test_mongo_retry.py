import pytest

from app.workers import signal_worker


class FakeCollection:
    def __init__(self):
        self.calls = 0

    async def insert_one(self, signal):
        self.calls += 1
        if self.calls < 3:
            raise RuntimeError("temporary mongo failure")
        return True


class FakeMongoDB:
    def __init__(self):
        self.collection = FakeCollection()

    def __getitem__(self, name):
        return self.collection


@pytest.mark.asyncio
async def test_write_signal_to_mongo_retries_then_succeeds(monkeypatch):
    fake_db = FakeMongoDB()

    monkeypatch.setattr(signal_worker, "get_mongo_db", lambda: fake_db)

    async def no_sleep(seconds):
        return None

    monkeypatch.setattr(signal_worker.asyncio, "sleep", no_sleep)

    signal = {
        "_id": "signal-1",
        "component_id": "RDBMS_PRIMARY",
        "error_message": "database down",
        "severity": "critical",
        "raw_payload": {},
        "received_at": "2026-01-01T10:00:00+00:00",
    }

    await signal_worker._write_signal_to_mongo(signal, "workitem-1")

    assert fake_db.collection.calls == 3
    assert signal["workitem_id"] == "workitem-1"