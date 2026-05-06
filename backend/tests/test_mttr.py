from datetime import datetime, timezone


def test_mttr_uses_workitem_created_at_and_rca_submitted_at():
    workitem_created_at = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)
    rca_submitted_at = datetime(2026, 1, 1, 10, 45, tzinfo=timezone.utc)

    delta = rca_submitted_at - workitem_created_at
    mttr_minutes = round(delta.total_seconds() / 60, 2)

    assert mttr_minutes == 45.0