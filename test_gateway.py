"""
Gateway Mock Server
Mimics the OutsideServer's /ws/gateway endpoint on ws://localhost:9999
Run this FIRST, then run test_gateway_client.mjs from the LocalServer.
"""
import asyncio
import json
import websockets
import uuid

PORT = 9999

def log(msg, status="ℹ️"):
    print(f"  {status} [SERVER] {msg}")


async def mock_gateway_handler(websocket):
    log("Client connected!")

    # Step 1: Wait for IDENTIFY
    raw = await websocket.recv()
    data = json.loads(raw)

    if data.get("type") != "IDENTIFY":
        log(f"Expected IDENTIFY, got: {data.get('type')}", "❌")
        await websocket.close()
        return

    box_id = data.get("box_id")
    password = data.get("password")
    log(f"IDENTIFY received — box_id={box_id}, password={'(set)' if password else '(null)'}", "✅")

    # Step 2: Send REGISTERED (simulate successful registration)
    await websocket.send(json.dumps({
        "type": "REGISTERED",
        "payload": {
            "box_id": box_id or "test-server-id",
            "claim_password": "test_claim_pw_123"
        }
    }))
    log("Sent REGISTERED", "📤")

    # Step 3: Wait a moment, then send a test REQUEST
    await asyncio.sleep(0.5)
    test_request_id = str(uuid.uuid4())
    await websocket.send(json.dumps({
        "type": "REQUEST",
        "request_id": test_request_id,
        "method": "GET",
        "path": "/api/health",
        "query": "",
        "headers": {"accept": "application/json"},
        "body": None
    }))
    log(f"Sent REQUEST GET /api/health (id={test_request_id[:8]}...)", "📤")

    # Step 4: Wait for RESPONSE from the gateway client
    try:
        raw = await asyncio.wait_for(websocket.recv(), timeout=10.0)
        response = json.loads(raw)

        if response.get("type") == "RESPONSE" and response.get("request_id") == test_request_id:
            payload = response.get("payload", {})
            status_code = payload.get("status")
            body = payload.get("body")
            log(f"RESPONSE received — status={status_code}", "✅")
            log(f"  Body: {json.dumps(body) if isinstance(body, (dict, list)) else body}", "   ")

            if status_code == 502:
                log("Status 502 is expected (no local Express server running) — protocol works!", "✅")
            elif status_code == 200:
                log("Status 200 — local Express server responded! Full round-trip works!", "🎉")
            else:
                log(f"Unexpected status {status_code}, but RESPONSE was received — protocol works!", "✅")
        else:
            log(f"Unexpected message type: {response.get('type')}", "❌")
    except asyncio.TimeoutError:
        log("Timed out waiting for RESPONSE", "❌")

    log("Test complete — closing connection", "🏁")


async def main():
    print("\n" + "=" * 60)
    print("🔌 Gateway Mock Server (mimics OutsideServer)")
    print("=" * 60)
    print(f"\n  Listening on ws://localhost:{PORT}")
    print("  Waiting for the gateway client to connect...")
    print("  (Run test_gateway_client.mjs from the LocalServer)\n")

    async with websockets.serve(mock_gateway_handler, "localhost", PORT):
        await asyncio.Future()  # Run forever


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n  Server stopped.")
