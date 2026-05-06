from abc import ABC, abstractmethod
from app.models.workitem import WorkItemStatus
from fastapi import HTTPException


class WorkItemState(ABC):
    """
    State Pattern: each state knows which transitions are valid from it.
    The WorkItem delegates transition logic to its current state object.
    Attempting an invalid transition raises a 422 immediately.
    """

    @abstractmethod
    def get_status(self) -> WorkItemStatus:
        ...

    @abstractmethod
    def can_transition_to(self, target: WorkItemStatus) -> bool:
        ...

    def transition_to(self, target: WorkItemStatus, rca_exists: bool = False) -> None:
        if not self.can_transition_to(target):
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Invalid transition: {self.get_status().value} → {target.value}. "
                    f"Allowed from {self.get_status().value}: "
                    f"{[s.value for s in self._allowed_targets()]}"
                ),
            )
        if target == WorkItemStatus.CLOSED and not rca_exists:
            raise HTTPException(
                status_code=422,
                detail=(
                    "Cannot close a Work Item without a completed RCA. "
                    "Submit an RCA first via POST /api/v1/workitems/{id}/rca"
                ),
            )

    @abstractmethod
    def _allowed_targets(self) -> list[WorkItemStatus]:
        ...


class OpenState(WorkItemState):
    def get_status(self) -> WorkItemStatus:
        return WorkItemStatus.OPEN

    def _allowed_targets(self) -> list[WorkItemStatus]:
        return [WorkItemStatus.INVESTIGATING]

    def can_transition_to(self, target: WorkItemStatus) -> bool:
        return target in self._allowed_targets()


class InvestigatingState(WorkItemState):
    def get_status(self) -> WorkItemStatus:
        return WorkItemStatus.INVESTIGATING

    def _allowed_targets(self) -> list[WorkItemStatus]:
        return [WorkItemStatus.RESOLVED, WorkItemStatus.OPEN]

    def can_transition_to(self, target: WorkItemStatus) -> bool:
        return target in self._allowed_targets()


class ResolvedState(WorkItemState):
    def get_status(self) -> WorkItemStatus:
        return WorkItemStatus.RESOLVED

    def _allowed_targets(self) -> list[WorkItemStatus]:
        return [WorkItemStatus.CLOSED, WorkItemStatus.INVESTIGATING]

    def can_transition_to(self, target: WorkItemStatus) -> bool:
        return target in self._allowed_targets()


class ClosedState(WorkItemState):
    def get_status(self) -> WorkItemStatus:
        return WorkItemStatus.CLOSED

    def _allowed_targets(self) -> list[WorkItemStatus]:
        return []  # Terminal state — no transitions allowed

    def can_transition_to(self, target: WorkItemStatus) -> bool:
        return False


# Factory: get the right state object for a given status string
STATE_MAP: dict[WorkItemStatus, type[WorkItemState]] = {
    WorkItemStatus.OPEN: OpenState,
    WorkItemStatus.INVESTIGATING: InvestigatingState,
    WorkItemStatus.RESOLVED: ResolvedState,
    WorkItemStatus.CLOSED: ClosedState,
}


def get_state(status: WorkItemStatus) -> WorkItemState:
    return STATE_MAP[status]()
