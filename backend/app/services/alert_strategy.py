from abc import ABC, abstractmethod
from app.models.workitem import Priority


class AlertStrategy(ABC):
    """
    Strategy Pattern: each component type has its own alert strategy
    that determines priority and alert messaging.
    Swap strategies without touching the worker logic.
    """

    @abstractmethod
    def get_priority(self) -> Priority:
        ...

    @abstractmethod
    def get_alert_type(self) -> str:
        ...

    @abstractmethod
    def get_alert_message(self, component_id: str, signal_count: int) -> str:
        ...


class RDBMSFailureStrategy(AlertStrategy):
    """Database failures are P0 — most critical. Data integrity at risk."""

    def get_priority(self) -> Priority:
        return Priority.P0

    def get_alert_type(self) -> str:
        return "RDBMS_FAILURE"

    def get_alert_message(self, component_id: str, signal_count: int) -> str:
        return (
            f"[P0 CRITICAL] RDBMS failure on {component_id}. "
            f"{signal_count} signals received. Immediate action required."
        )


class CacheFailureStrategy(AlertStrategy):
    """Cache failures are P2 — system degrades but stays functional."""

    def get_priority(self) -> Priority:
        return Priority.P2

    def get_alert_type(self) -> str:
        return "CACHE_FAILURE"

    def get_alert_message(self, component_id: str, signal_count: int) -> str:
        return (
            f"[P2 WARNING] Cache failure on {component_id}. "
            f"{signal_count} signals received. Performance may be degraded."
        )


class APIFailureStrategy(AlertStrategy):
    """API failures are P1 — affects users but not data integrity."""

    def get_priority(self) -> Priority:
        return Priority.P1

    def get_alert_type(self) -> str:
        return "API_FAILURE"

    def get_alert_message(self, component_id: str, signal_count: int) -> str:
        return (
            f"[P1 HIGH] API failure on {component_id}. "
            f"{signal_count} signals received. User-facing impact detected."
        )


class QueueFailureStrategy(AlertStrategy):
    """Async queue failures are P1 — message loss risk."""

    def get_priority(self) -> Priority:
        return Priority.P1

    def get_alert_type(self) -> str:
        return "QUEUE_FAILURE"

    def get_alert_message(self, component_id: str, signal_count: int) -> str:
        return (
            f"[P1 HIGH] Async queue failure on {component_id}. "
            f"{signal_count} signals received. Potential message loss."
        )


class MCPFailureStrategy(AlertStrategy):
    """MCP host failures are P1."""

    def get_priority(self) -> Priority:
        return Priority.P1

    def get_alert_type(self) -> str:
        return "MCP_FAILURE"

    def get_alert_message(self, component_id: str, signal_count: int) -> str:
        return (
            f"[P1 HIGH] MCP Host failure on {component_id}. "
            f"{signal_count} signals received."
        )


class DefaultFailureStrategy(AlertStrategy):
    """Fallback for unknown component types."""

    def get_priority(self) -> Priority:
        return Priority.P1

    def get_alert_type(self) -> str:
        return "UNKNOWN_FAILURE"

    def get_alert_message(self, component_id: str, signal_count: int) -> str:
        return (
            f"[P1 HIGH] Failure on {component_id}. "
            f"{signal_count} signals received."
        )


# Registry: component_id prefix → strategy class
# Add new component types here without touching any other code
STRATEGY_REGISTRY: dict[str, type[AlertStrategy]] = {
    "RDBMS": RDBMSFailureStrategy,
    "DB": RDBMSFailureStrategy,
    "POSTGRES": RDBMSFailureStrategy,
    "CACHE": CacheFailureStrategy,
    "REDIS": CacheFailureStrategy,
    "MEMCACHE": CacheFailureStrategy,
    "API": APIFailureStrategy,
    "HTTP": APIFailureStrategy,
    "QUEUE": QueueFailureStrategy,
    "KAFKA": QueueFailureStrategy,
    "RABBIT": QueueFailureStrategy,
    "MCP": MCPFailureStrategy,
}


def get_alert_strategy(component_id: str) -> AlertStrategy:
    """
    Resolve the correct strategy by matching component_id prefix.
    e.g. 'RDBMS_PRIMARY' → RDBMSFailureStrategy
         'CACHE_CLUSTER_01' → CacheFailureStrategy
    """
    upper = component_id.upper()
    for prefix, strategy_cls in STRATEGY_REGISTRY.items():
        if upper.startswith(prefix):
            return strategy_cls()
    return DefaultFailureStrategy()
