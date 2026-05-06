#!/usr/bin/env python3
"""
simulate_incident.py

Simulates a realistic incident:
  1. RDBMS outage — fires 150 signals in 8 seconds (triggers debounce)
  2. MCP Host failure — fires 60 signals (second WorkItem)
  3. Walks the RDBMS WorkItem through full lifecycle to CLOSED with an RCA
  4. Prints MTTR at the end

Usage:
  python scripts/simulate_incident.py [--url http://localhost:8000]

Requirements:
  - Python 3.10+ (Recommended for active security support)
  - Install dependencies:
      pip install httpx
"""

import asyncio
import httpx
import argparse
import json
from datetime import datetime, timezone, timedelta

BASE_URL = "http://localhost:8000"


async def fire_signals(client: httpx.AsyncClient, component_id: str, count: int, severity: str):
    print(f"\n→ Firing {count} signals for {component_id} [{severity}]...")
    tasks = []
    for i in range(count):
        payload = {
            "component_id": component_id,
            "error_message": f"Connection timeout #{i+1} on {component_id}",
            "severity": severity,
            "raw_payload": {
                "host": f"{component_id.lower()}.internal",
                "error_code": 500 + (i % 10),
                "latency_ms": 5000 + (i * 10),
            }
        }
        tasks.append(client.post(f"{BASE_URL}/api/v1/signals", json=payload))

    # Fire in batches of 20, with small delays to simulate a burst
    for i in range(0, len(tasks), 20):
        batch = tasks[i:i+20]
        responses = await asyncio.gather(*batch)
        ok = sum(1 for r in responses if r.status_code == 202)
        print(f"  Batch {i//20 + 1}: {ok}/{len(batch)} accepted")
        await asyncio.sleep(0.5)


async def get_workitems(client: httpx.AsyncClient) -> list[dict]:
    r = await client.get(f"{BASE_URL}/api/v1/workitems")
    r.raise_for_status()
    return r.json()


async def transition(client: httpx.AsyncClient, workitem_id: str, status: str):
    r = await client.patch(
        f"{BASE_URL}/api/v1/workitems/{workitem_id}/status",
        json={"status": status},
    )
    if r.status_code == 200:
        print(f"  ✓ Transitioned to {status}")
    else:
        print(f"  ✗ Transition to {status} failed: {r.text}")
    return r


async def submit_rca(client: httpx.AsyncClient, workitem_id: str):
    now = datetime.now(timezone.utc)
    payload = {
        "incident_start": (now - timedelta(hours=1)).isoformat(),
        "incident_end": now.isoformat(),
        "root_cause_category": "DATABASE_FAILURE",
        "fix_applied": (
            "Identified a deadlock caused by a long-running analytics query. "
            "Killed the blocking session and restarted the read replica. "
            "Promoted the secondary to primary to restore write capacity."
        ),
        "prevention_steps": (
            "1. Add query timeout limits (max 30s) on the analytics role. "
            "2. Set up automated deadlock detection alerts in CloudWatch. "
            "3. Separate the analytics workload onto a dedicated read replica. "
            "4. Schedule weekly review of slow query logs."
        ),
    }
    r = await client.post(
        f"{BASE_URL}/api/v1/workitems/{workitem_id}/rca",
        json=payload,
    )
    if r.status_code == 201:
        print("  ✓ RCA submitted")
    else:
        print(f"  ✗ RCA submission failed: {r.text}")
    return r


async def main(base_url: str):
    global BASE_URL
    BASE_URL = base_url

    print("=" * 60)
    print("  IMS Incident Simulation")
    print("=" * 60)

    async with httpx.AsyncClient(timeout=30) as client:

        # Health check first
        r = await client.get(f"{BASE_URL}/health")
        health = r.json()
        print(f"\nHealth: {json.dumps(health, indent=2)}")
        if health.get("overall") != "ok":
            print("⚠ System not fully healthy. Proceeding anyway...")

        # Step 1 — RDBMS burst
        await fire_signals(client, "RDBMS_PRIMARY", 150, "P0")
        await asyncio.sleep(2)  # Let the worker process

        # Step 2 — MCP failure
        await fire_signals(client, "MCP_HOST_01", 60, "P1")
        await asyncio.sleep(2)

        # Step 3 — Fetch created work items
        print("\n→ Fetching WorkItems...")
        items = await get_workitems(client)
        print(f"  Found {len(items)} active WorkItem(s):")
        for item in items:
            print(f"  [{item['priority']}] {item['component_id']} — {item['status']} (signals: {item['signal_count']})")

        if not items:
            print("  No WorkItems found. Worker may still be processing. Try again in a few seconds.")
            return

        # Step 4 — Find the RDBMS WorkItem and walk it to CLOSED
        rdbms_item = next((i for i in items if "RDBMS" in i["component_id"]), items[0])
        wid = rdbms_item["id"]

        print(f"\n→ Walking WorkItem {wid} ({rdbms_item['component_id']}) to CLOSED...")

        # Try to close without RCA first — should be rejected
        print("\n  Testing guard: attempting CLOSED without RCA...")
        r = await client.patch(
            f"{BASE_URL}/api/v1/workitems/{wid}/status",
            json={"status": "CLOSED"},
        )
        if r.status_code == 422:
            print(f"  ✓ Guard worked — rejected: {r.json()['detail'][:80]}...")
        else:
            print(f"  ✗ Guard failed (expected 422, got {r.status_code})")

        # Now do it properly
        await transition(client, wid, "INVESTIGATING")
        await transition(client, wid, "RESOLVED")

        print("\n  Submitting RCA...")
        await submit_rca(client, wid)

        await transition(client, wid, "CLOSED")

        # Step 5 — Fetch final state and print MTTR
        r = await client.get(f"{BASE_URL}/api/v1/workitems/{wid}")
        final = r.json()
        print(f"\n{'='*60}")
        print(f"  INCIDENT CLOSED")
        print(f"  Component:  {final['component_id']}")
        print(f"  Priority:   {final['priority']}")
        print(f"  Signals:    {final['signal_count']}")
        print(f"  Status:     {final['status']}")
        print(f"  MTTR:       {final.get('mttr_minutes', 'N/A')} minutes")
        print(f"{'='*60}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="IMS Incident Simulator")
    parser.add_argument("--url", default="http://localhost:8000", help="Backend base URL")
    args = parser.parse_args()
    asyncio.run(main(args.url))
