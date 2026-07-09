"""
Quick test script for noptechs_ai endpoints.
Run with:  python test_endpoints.py

Requirements: pip install requests
"""

import json
import requests

# ── Configuration ─────────────────────────────────────────────────────────────
BASE_URL  = "http://localhost:8069"
DATABASE  = "YOUR_DATABASE_NAME"   # <-- change this (find it on the Odoo login screen)
LOGIN     = "admin"
PASSWORD  = "admin"                # <-- your admin password
# ─────────────────────────────────────────────────────────────────────────────


def call(session, route, params):
    """Send one JSON-RPC request and return the result or raise on error."""
    resp = session.post(
        f"{BASE_URL}{route}",
        json={"jsonrpc": "2.0", "method": "call", "params": params},
    )
    data = resp.json()
    if "error" in data:
        raise RuntimeError(json.dumps(data["error"], indent=2))
    return data["result"]


def main():
    session = requests.Session()

    # ── Step 1: authenticate ──────────────────────────────────────────────────
    print("=== Authenticating ===")
    result = call(session, "/web/session/authenticate", {
        "db": DATABASE,
        "login": LOGIN,
        "password": PASSWORD,
    })
    if not result.get("uid"):
        print("Login failed — check DATABASE / LOGIN / PASSWORD")
        return
    print(f"Logged in as user ID {result['uid']}\n")


    # ── Step 2: find or create a partner ─────────────────────────────────────
    print("=== Test: find_or_create_partner ===")
    result = call(session, "/noptechs_ai/find_or_create_partner", {
        "email": "test.ai@example.com",
        "name":  "AI Test Contact",
        "phone": "0501234567",
        # "search_only": True   # uncomment to only search, never create
    })
    print(json.dumps(result, indent=2))
    partner_id = (
        result["partner"]["id"] if result.get("created")
        else result["partners"][0]["id"] if result.get("found")
        else None
    )
    print(f"Partner ID to use: {partner_id}\n")


    # ── Step 3: create a helpdesk ticket ─────────────────────────────────────
    print("=== Test: create_ticket ===")
    result = call(session, "/noptechs_ai/create_ticket", {
        "subject":     "AI Test Ticket",
        "description": "Error reproduced in channel. Steps: open app > click X > crash.",
        # "channel_id": 1,       # replace with a real discuss.channel ID
        # "assignee_id": 2,      # replace with a real res.users ID
        # "partner_id": partner_id,
    })
    print(json.dumps(result, indent=2))
    print()


    # ── Step 4: search knowledge ──────────────────────────────────────────────
    print("=== Test: search_knowledge ===")
    # NOTE: this returns nothing until you set allowed folders in
    # Settings > Noptechs AI.  The message field will tell you.
    result = call(session, "/noptechs_ai/search_knowledge", {
        "query": "onboarding",
        "limit": 5,
    })
    print(json.dumps(result, indent=2))
    print()


    # ── Step 5: create a CRM lead ────────────────────────────────────────────
    print("=== Test: create_lead ===")
    result = call(session, "/noptechs_ai/create_lead", {
        "name":        "AI Test Lead",
        "email":       "test.ai@example.com",
        "description": "Interested in product X — raised via AI assistant.",
        # "partner_id": partner_id,
    })
    print(json.dumps(result, indent=2))
    print()

    print("All tests complete.")


if __name__ == "__main__":
    main()
