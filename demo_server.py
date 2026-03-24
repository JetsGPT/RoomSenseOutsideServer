"""
Frontend Demo Server
A mock API backend so you can demo the Notifications page in the React frontend.

Usage:
  1. Start this server:    .venv\Scripts\python.exe demo_server.py
  2. Start the frontend:   set VITE_API_URL=http://localhost:9876 && npm run dev --prefix frontend-react
  3. Open http://localhost:5173, click Login, use: demo@roomsense.info / anything
  4. Click "Notifications" in the nav bar
"""
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
import random
import uuid
import json

app = FastAPI(title="RoomSense Demo Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Mock Data ───

DEMO_USER = {
    "user": {
        "id": "demo-user-001",
        "email": "demo@roomsense.info",
        "user_metadata": {"username": "DemoUser"},
    },
    "session": {"access_token": "demo-token-12345"},
}

MOCK_SERVERS = [
    {"id": "7a7b8e81-686c-4bf6-9965-ef8a2c4ff7e0", "name": "Living Room Box", "status": "online",
     "last_seen": datetime.now().isoformat(), "role": "owner"},
    {"id": "b2c3d4e5-f6a7-8901-bcde-f01234567890", "name": "Bedroom Sensor", "status": "offline",
     "last_seen": (datetime.now() - timedelta(hours=3)).isoformat(), "role": "owner"},
]

MOCK_PROVIDERS = ["ntfy", "email", "sms"]

MOCK_CONFIGS = [
    {"config_key": "ntfy_config", "config_value": {"base_url": "https://ntfy.sh", "default_topic": "roomsense-alerts"},
     "description": "Default ntfy.sh configuration", "updated_at": datetime.now().isoformat()},
    {"config_key": "email_config", "config_value": {"smtp_host": "smtp.example.com", "smtp_port": 587, "sender": "alerts@roomsense.info"},
     "description": "Email relay settings", "updated_at": datetime.now().isoformat()},
]

MOCK_SETTINGS = {}


def generate_mock_logs(count=15):
    providers = ["ntfy", "email"]
    targets = ["roomsense-alerts", "admin@roomsense.info", "sensor-warnings"]
    titles = ["High Temperature Alert", "Motion Detected", "Humidity Warning", "Sensor Offline", "Battery Low"]
    messages = ["Temperature exceeded 30°C", "Motion detected in hallway", "Humidity above 80%", "Sensor lost connection", "Battery below 15%"]
    logs = []
    for i in range(count):
        success = random.random() > 0.2
        server = random.choice(MOCK_SERVERS)
        logs.append({
            "id": str(uuid.uuid4()),
            "server_id": server["id"],
            "provider": random.choice(providers),
            "target": random.choice(targets),
            "title": random.choice(titles),
            "message": random.choice(messages),
            "priority": random.choice(["default", "high", "urgent"]),
            "success": success,
            "status_code": 200 if success else random.choice([500, 502, 408]),
            "error_message": None if success else "Connection timeout",
            "created_at": (datetime.now() - timedelta(minutes=random.randint(1, 1440))).isoformat(),
        })
    return sorted(logs, key=lambda x: x["created_at"], reverse=True)


MOCK_LOGS = generate_mock_logs()


# ─── Endpoints ───

@app.get("/")
async def root():
    return {"status": "ok", "message": "RoomSense Demo Server"}


# Login — accepts anything
class LoginReq(BaseModel):
    email: str
    password: str

@app.post("/login")
async def login(req: LoginReq):
    return DEMO_USER


@app.post("/logout")
async def logout():
    return {"status": "ok"}


# Boxes
@app.get("/api/boxes")
async def get_boxes():
    return {"servers": {"owned": MOCK_SERVERS, "assigned": []}}


# Notification Logs
@app.get("/api/v1/notifications/logs")
async def get_logs(limit: int = 100):
    return {"logs": MOCK_LOGS[:limit]}


@app.get("/api/v1/servers/{server_id}/notifications/logs")
async def get_server_logs(server_id: str, limit: int = 100):
    filtered = [l for l in MOCK_LOGS if l["server_id"] == server_id]
    return {"logs": filtered[:limit]}


# Server Notification Settings
@app.get("/api/v1/servers/{server_id}/notification-settings")
async def get_settings(server_id: str):
    return {"settings": MOCK_SETTINGS.get(server_id, {
        "ntfy_enabled": True, "ntfy_base_url": "https://ntfy.sh",
        "ntfy_default_topic": "roomsense-alerts",
        "email_enabled": False, "sms_enabled": False,
        "dnd_enabled": True, "dnd_start": "22:00", "dnd_end": "07:00",
    })}


@app.post("/api/v1/servers/{server_id}/notification-settings")
async def save_settings(server_id: str, request: Request):
    body = await request.json()
    MOCK_SETTINGS[server_id] = body
    return {"status": "ok", "message": "Settings saved"}


# Global Config
@app.get("/api/v1/config/global")
async def get_configs():
    return {"configs": MOCK_CONFIGS}


@app.post("/api/v1/config/global")
async def save_config(request: Request):
    body = await request.json()
    for c in MOCK_CONFIGS:
        if c["config_key"] == body["config_key"]:
            c["config_value"] = body["config_value"]
            c["description"] = body.get("description")
            return {"status": "ok"}
    MOCK_CONFIGS.append({
        "config_key": body["config_key"], "config_value": body["config_value"],
        "description": body.get("description"), "updated_at": datetime.now().isoformat(),
    })
    return {"status": "ok"}


@app.delete("/api/v1/config/global/{config_key}")
async def delete_config(config_key: str):
    global MOCK_CONFIGS
    MOCK_CONFIGS = [c for c in MOCK_CONFIGS if c["config_key"] != config_key]
    return {"status": "ok"}


# Providers
@app.get("/api/v1/relay/providers")
async def get_providers():
    return {"providers": MOCK_PROVIDERS}


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("🎬 RoomSense Demo Server")
    print("=" * 50)
    print(f"\n  API running on http://localhost:9876")
    print(f"  Login: demo@roomsense.info / any password\n")
    uvicorn.run(app, host="0.0.0.0", port=9876, log_level="info")
