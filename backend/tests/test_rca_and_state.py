import pytest
from datetime import datetime, timezone, timedelta
from pydantic import ValidationError
from fastapi import HTTPException

from app.schemas.rca import RCACreate
from app.services.state_machine import (
    get_state,
    OpenState,
    InvestigatingState,
    ResolvedState,
    ClosedState,
)
from app.models.workitem import WorkItemStatus
from app.services.alert_strategy import get_alert_strategy
from app.models.workitem import Priority


# ──────────────────────────────────────────────
# RCA Schema Validation Tests
# ──────────────────────────────────────────────

class TestRCAValidation:

    def _valid_payload(self, **overrides):
        base = dict(
            incident_start=datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc),
            incident_end=datetime(2026, 1, 1, 11, 0, tzinfo=timezone.utc),
            root_cause_category="DATABASE_FAILURE",
            fix_applied="Restarted the primary database and promoted a replica.",
            prevention_steps="Add automated failover and increase monitoring coverage.",
        )
        base.update(overrides)
        return base

    def test_valid_rca_passes(self):
        rca = RCACreate(**self._valid_payload())
        assert rca.root_cause_category == "DATABASE_FAILURE"

    def test_end_before_start_is_rejected(self):
        with pytest.raises(ValidationError) as exc_info:
            RCACreate(**self._valid_payload(
                incident_start=datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc),
                incident_end=datetime(2026, 1, 1, 11, 0, tzinfo=timezone.utc),
            ))
        assert "incident_end must be after incident_start" in str(exc_info.value)

    def test_end_equal_to_start_is_rejected(self):
        t = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)
        with pytest.raises(ValidationError):
            RCACreate(**self._valid_payload(incident_start=t, incident_end=t))

    def test_invalid_root_cause_category_is_rejected(self):
        with pytest.raises(ValidationError) as exc_info:
            RCACreate(**self._valid_payload(root_cause_category="ALIENS"))
        assert "root_cause_category" in str(exc_info.value)

    def test_all_valid_categories_accepted(self):
        valid_cats = [
            "DATABASE_FAILURE", "CACHE_FAILURE", "NETWORK_ISSUE",
            "APPLICATION_BUG", "INFRASTRUCTURE", "THIRD_PARTY",
            "HUMAN_ERROR", "UNKNOWN",
        ]
        for cat in valid_cats:
            rca = RCACreate(**self._valid_payload(root_cause_category=cat))
            assert rca.root_cause_category == cat

    def test_fix_applied_too_short_is_rejected(self):
        with pytest.raises(ValidationError):
            RCACreate(**self._valid_payload(fix_applied="short"))

    def test_prevention_steps_too_short_is_rejected(self):
        with pytest.raises(ValidationError):
            RCACreate(**self._valid_payload(prevention_steps="short"))

    def test_missing_required_field_is_rejected(self):
        payload = self._valid_payload()
        del payload["fix_applied"]
        with pytest.raises(ValidationError):
            RCACreate(**payload)


# ──────────────────────────────────────────────
# State Machine Tests
# ──────────────────────────────────────────────

class TestStateMachine:

    def test_open_can_transition_to_investigating(self):
        state = get_state(WorkItemStatus.OPEN)
        assert isinstance(state, OpenState)
        assert state.can_transition_to(WorkItemStatus.INVESTIGATING)

    def test_open_cannot_skip_to_resolved(self):
        state = get_state(WorkItemStatus.OPEN)
        assert not state.can_transition_to(WorkItemStatus.RESOLVED)

    def test_open_cannot_skip_to_closed(self):
        state = get_state(WorkItemStatus.OPEN)
        assert not state.can_transition_to(WorkItemStatus.CLOSED)

    def test_investigating_can_go_to_resolved(self):
        state = get_state(WorkItemStatus.INVESTIGATING)
        assert state.can_transition_to(WorkItemStatus.RESOLVED)

    def test_investigating_can_reopen(self):
        state = get_state(WorkItemStatus.INVESTIGATING)
        assert state.can_transition_to(WorkItemStatus.OPEN)

    def test_resolved_can_go_to_closed(self):
        state = get_state(WorkItemStatus.RESOLVED)
        assert state.can_transition_to(WorkItemStatus.CLOSED)

    def test_closed_is_terminal(self):
        state = get_state(WorkItemStatus.CLOSED)
        assert isinstance(state, ClosedState)
        for s in WorkItemStatus:
            assert not state.can_transition_to(s)

    def test_closing_without_rca_raises_422(self):
        state = get_state(WorkItemStatus.RESOLVED)
        with pytest.raises(HTTPException) as exc_info:
            state.transition_to(WorkItemStatus.CLOSED, rca_exists=False)
        assert exc_info.value.status_code == 422
        assert "RCA" in exc_info.value.detail

    def test_closing_with_rca_succeeds(self):
        state = get_state(WorkItemStatus.RESOLVED)
        # Should not raise
        state.transition_to(WorkItemStatus.CLOSED, rca_exists=True)

    def test_invalid_transition_raises_422(self):
        state = get_state(WorkItemStatus.OPEN)
        with pytest.raises(HTTPException) as exc_info:
            state.transition_to(WorkItemStatus.CLOSED)
        assert exc_info.value.status_code == 422


# ──────────────────────────────────────────────
# Alert Strategy Tests
# ──────────────────────────────────────────────

class TestAlertStrategy:

    def test_rdbms_component_gets_p0(self):
        strategy = get_alert_strategy("RDBMS_PRIMARY")
        assert strategy.get_priority() == Priority.P0

    def test_cache_component_gets_p2(self):
        strategy = get_alert_strategy("CACHE_CLUSTER_01")
        assert strategy.get_priority() == Priority.P2

    def test_api_component_gets_p1(self):
        strategy = get_alert_strategy("API_GATEWAY")
        assert strategy.get_priority() == Priority.P1

    def test_mcp_component_gets_p1(self):
        strategy = get_alert_strategy("MCP_HOST_01")
        assert strategy.get_priority() == Priority.P1

    def test_unknown_component_gets_default_p1(self):
        strategy = get_alert_strategy("UNKNOWN_SYSTEM_XYZ")
        assert strategy.get_priority() == Priority.P1

    def test_case_insensitive_matching(self):
        strategy = get_alert_strategy("rdbms_secondary")
        assert strategy.get_priority() == Priority.P0
