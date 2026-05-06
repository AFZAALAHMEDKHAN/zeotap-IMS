# Design Patterns

This document covers the Low Level Design (LLD) decisions in the IMS codebase —
specifically the two design patterns required by the assignment, where they live,
and why they were chosen.

---

## 1. Strategy Pattern — Alert Routing

**File:** `backend/app/services/alert_strategy.py`

### The Problem
Different infrastructure components require different alert severity levels.
An RDBMS failure (data integrity at risk) is far more critical than a cache miss
(degraded performance only). A naive implementation would use a giant `if/elif` block:

```python
# BAD — brittle, violates Open/Closed principle
if "RDBMS" in component_id:
    priority = "P0"
elif "CACHE" in component_id:
    priority = "P2"
elif "API" in component_id:
    priority = "P1"
```

Adding a new component type means editing this block — risk of breaking existing logic.

### The Solution
The **Strategy Pattern** defines a common `AlertStrategy` interface, and each component
type implements it independently. The worker calls `get_alert_strategy(component_id)` and
gets back the right implementation — without any `if/else` logic in the worker.

```
AlertStrategy (abstract)
    ├── RDBMSFailureStrategy   → P0, "RDBMS_FAILURE"
    ├── CacheFailureStrategy   → P2, "CACHE_FAILURE"
    ├── APIFailureStrategy     → P1, "API_FAILURE"
    ├── QueueFailureStrategy   → P1, "QUEUE_FAILURE"
    ├── MCPFailureStrategy     → P1, "MCP_FAILURE"
    └── DefaultFailureStrategy → P1, fallback
```

**To add a new component type:** create a new class extending `AlertStrategy`, add
one entry to `STRATEGY_REGISTRY`. Zero changes to the worker.

---

## 2. State Pattern — WorkItem Lifecycle

**File:** `backend/app/services/state_machine.py`

### The Problem
A WorkItem moves through four states: `OPEN → INVESTIGATING → RESOLVED → CLOSED`.
Not all transitions are valid — you cannot jump from `OPEN` directly to `CLOSED`,
and closing requires a completed RCA. Another `if/elif` approach:

```python
# BAD — every new state/transition adds to this block
if current == "OPEN" and target == "CLOSED":
    raise ValueError("invalid")
if current == "RESOLVED" and target == "CLOSED" and not rca:
    raise ValueError("need RCA")
```

### The Solution
The **State Pattern** gives each state its own class that knows which transitions
are valid *from that state*. The endpoint calls `get_state(wi.status).transition_to(target)`.

```
WorkItemState (abstract)
    ├── OpenState         → can go to: [INVESTIGATING]
    ├── InvestigatingState → can go to: [RESOLVED, OPEN]
    ├── ResolvedState     → can go to: [CLOSED, INVESTIGATING]
    └── ClosedState       → terminal, no transitions allowed
```

The guard `rca_exists=True` check lives inside `transition_to()` on the base class —
it's evaluated universally whenever `CLOSED` is the target, regardless of which state
you're transitioning from.

### Guard Enforcement
```python
# In ResolvedState.transition_to(CLOSED, rca_exists=False):
# → raises HTTP 422: "Cannot close without a completed RCA"

# In OpenState.transition_to(CLOSED, rca_exists=True):
# → raises HTTP 422: "Invalid transition: OPEN → CLOSED"
```

Both guards are enforced. An RCA alone is not enough — you must also be in `RESOLVED`.

---

## 3. Other Code Quality Decisions

### Async-first
Every I/O operation — Postgres, MongoDB, Redis — uses `async/await`. The ingestion
endpoint never blocks the event loop, which is what allows 10,000 signals/sec.

### Dependency Injection
FastAPI's `Depends()` system provides clean, testable database sessions. Tests can
override `get_db` with an in-memory fixture without touching production code.

### Retry with Exponential Backoff
MongoDB writes retry up to 3 times with `0.5s → 1s → 2s` delays.
This handles transient network blips without losing signal data.

### Fail-Open Queue
When the asyncio queue is full (>50,000 items), new signals are dropped with a
warning log rather than blocking the HTTP endpoint. This is intentional: the
ingestion API must remain responsive even if the storage layer is degraded.
