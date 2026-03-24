"""
Notification Relay E2E Test
Tests the full flow: Login → Relay notification → ntfy.sh delivery

Starts a minimal FastAPI server with mocked auth, sends a notification
through the relay endpoint, and verifies it reaches ntfy.sh.
"""
import asyncio
import httpx
import uvicorn
import threading
import time
import uuid
import sys

# ─── Import the actual notification system ───
from notification_forwarders import NtfyForwarder, NotificationPayload, NotificationPriority

TEST_PORT = 9876
NTFY_TOPIC = f"roomsense-test-{uuid.uuid4().hex[:8]}"


def log(msg, icon="ℹ️"):
    print(f"  {icon} {msg}")


async def test_direct_ntfy():
    """Test 1: Send directly via NtfyForwarder (bypasses server entirely)"""
    print("\n" + "=" * 60)
    print("📧 Test 1: Direct ntfy.sh Forwarding")
    print("=" * 60)

    forwarder = NtfyForwarder()

    payload = NotificationPayload(
        target=NTFY_TOPIC,
        title="RoomSense Test Notification",
        message="This is a test notification sent directly from the NtfyForwarder.",
        priority=NotificationPriority.DEFAULT,
        tags=["test", "white_check_mark"],
    )

    config = {"base_url": "https://ntfy.sh"}

    log(f"Sending to ntfy.sh topic: {NTFY_TOPIC}")
    result = await forwarder.forward(payload, config)

    if result.success:
        log(f"Notification sent! Status: {result.status_code}", "✅")
        log(f"View it at: https://ntfy.sh/{NTFY_TOPIC}", "🔗")
        return True
    else:
        log(f"Failed: {result.error_message}", "❌")
        return False


async def test_relay_endpoint():
    """Test 2: Full relay endpoint test with mocked FastAPI server"""
    print("\n" + "=" * 60)
    print("🔄 Test 2: Full Relay Endpoint")
    print("=" * 60)

    # ─── Build a minimal FastAPI app with the relay endpoint ───
    from fastapi import FastAPI, Header, HTTPException, Depends
    from pydantic import BaseModel
    from typing import Optional, List, Dict
    from notification_forwarders import notification_router, ForwardResult

    app = FastAPI()

    class RelayRequest(BaseModel):
        target: str
        title: str
        message: str
        priority: str = "default"
        provider: str = "ntfy"
        tags: Optional[List[str]] = None

    # Mock auth — accepts any X-Relay-Secret
    async def mock_auth(x_relay_secret: str = Header(None, alias="X-Relay-Secret")):
        if x_relay_secret == "test-secret":
            return {"auth_method": "shared_secret", "server_id": "test-server"}
        raise HTTPException(status_code=401, detail="Unauthorized")

    @app.post("/api/v1/relay/send")
    async def relay(request: RelayRequest, auth=Depends(mock_auth)):
        priority_map = {
            "min": NotificationPriority.MIN,
            "low": NotificationPriority.LOW,
            "default": NotificationPriority.DEFAULT,
            "high": NotificationPriority.HIGH,
            "urgent": NotificationPriority.URGENT,
        }
        payload = NotificationPayload(
            target=request.target,
            title=request.title,
            message=request.message,
            priority=priority_map.get(request.priority, NotificationPriority.DEFAULT),
            tags=request.tags,
        )
        result: ForwardResult = await notification_router.route(
            provider=request.provider, payload=payload, config={}
        )
        if result.success:
            return {"status": "success", "status_code": result.status_code}
        raise HTTPException(status_code=502, detail=result.error_message)

    # ─── Start server in background thread ───
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=TEST_PORT, log_level="warning"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    time.sleep(1)  # Let it start

    log(f"Mock server running on http://127.0.0.1:{TEST_PORT}")

    # ─── Test: Unauthorized request ───
    async with httpx.AsyncClient() as client:
        log("Testing unauthorized request (no secret)...")
        r = await client.post(f"http://127.0.0.1:{TEST_PORT}/api/v1/relay/send", json={
            "target": NTFY_TOPIC,
            "title": "Should Fail",
            "message": "This should be rejected",
        })
        if r.status_code == 401:
            log("Correctly rejected with 401", "✅")
        else:
            log(f"Expected 401, got {r.status_code}", "❌")
            return False

    # ─── Test: Authorized relay to ntfy.sh ───
    async with httpx.AsyncClient() as client:
        log("Testing authorized relay to ntfy.sh...")
        r = await client.post(
            f"http://127.0.0.1:{TEST_PORT}/api/v1/relay/send",
            json={
                "target": NTFY_TOPIC,
                "title": "RoomSense Relay Test",
                "message": "This notification went through the full relay endpoint!",
                "priority": "default",
                "provider": "ntfy",
                "tags": ["rocket", "test"],
            },
            headers={"X-Relay-Secret": "test-secret"},
        )
        if r.status_code == 200:
            log(f"Relay successful! Response: {r.json()}", "✅")
            return True
        else:
            log(f"Relay failed: {r.status_code} — {r.text}", "❌")
            return False


async def main():
    print("\n" + "=" * 60)
    print("🔔 RoomSense Notification E2E Test")
    print("=" * 60)
    print(f"\n  ntfy.sh topic: {NTFY_TOPIC}")
    print(f"  Open this URL to see notifications arrive:")
    print(f"  👉 https://ntfy.sh/{NTFY_TOPIC}\n")

    results = []

    # Test 1: Direct forwarder
    results.append(("Direct ntfy.sh forwarding", await test_direct_ntfy()))

    # Test 2: Full relay endpoint
    results.append(("Relay endpoint (auth + forwarding)", await test_relay_endpoint()))

    # ─── Summary ───
    print("\n" + "=" * 60)
    print("📋 Results")
    print("=" * 60)
    all_pass = True
    for name, passed in results:
        icon = "✅" if passed else "❌"
        print(f"  {icon} {name}")
        if not passed:
            all_pass = False

    print()
    if all_pass:
        print(f"  🎉 All tests passed!")
        print(f"  📱 Check your notifications at: https://ntfy.sh/{NTFY_TOPIC}")
    else:
        print(f"  ⚠️  Some tests failed — review output above.")
    print()


if __name__ == "__main__":
    asyncio.run(main())
