from typing import Dict
import asyncio
import uuid
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Response, Request
from pydantic import BaseModel
from supabase_code import initialize_supabase, create_user, login_user, check_username_exists, check_if_box_exists, update_box_status

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase_code import initialize_supabase, create_user, login_user, check_username_exists

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", "https://localhost:5173",  # Vite
        "http://127.0.0.1:5500", "http://localhost:5500",   # VS Code Live Server
        "http://localhost:8000", "http://127.0.0.1:8000"    # Python http.server
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

supabase = initialize_supabase()

active_connections: Dict[str, WebSocket] = {}
pending_requests: Dict[str, asyncio.Future] = {}

class RegisterRequest(BaseModel):
    email: str
    password: str
    username: str

class LoginRequest(BaseModel):
    email: str
    password: str


@app.websocket("/ws/gateway")
async def websocket_gateway(websocket: WebSocket):
    await websocket.accept()
    box_id = None

    try:
        data = await websocket.receive_json()

        if data.get("type") == "IDENTIFY":
            provided_id = data.get("box_id")

            box_id = check_if_box_exists(supabase, provided_id)

            if not box_id:
                await websocket.close(code=4001, reason="Invalid Identity")
                return

            if provided_id != box_id:
                await websocket.send_json({
                    "type": "PROVISION",
                    "payload": {"box_id": box_id}
                })

            active_connections[box_id] = websocket
            update_box_status(box_id, "online")
            print(f"✅ Server connected: {box_id}")

            while True:
                message = await websocket.receive_json()

                if message.get("type") == "RESPONSE":
                    req_id = message.get("request_id")
                    if req_id and req_id in pending_requests:
                        pending_requests[req_id].set_result(message)

    except WebSocketDisconnect:
        print(f"❌ Server disconnected: {box_id}")
    except Exception as e:
        print(f"⚠️ Error in websocket: {e}")
    finally:
        if box_id:
            active_connections.pop(box_id, None)
            update_box_status(box_id, "offline")


@app.api_route("/proxy/{box_id}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_request(box_id: str, path: str, request: Request):
    if box_id not in active_connections:
        raise HTTPException(status_code=404, detail="Target server is offline or not found")

    request_id = str(uuid.uuid4())
    body = await request.body()

    payload = {
        "type": "REQUEST",
        "request_id": request_id,
        "method": request.method,
        "path": f"/{path}",
        "query": str(request.query_params),
        "headers": dict(request.headers),
        "body": body.decode("utf-8") if body else None
    }

    loop = asyncio.get_running_loop()
    future = loop.create_future()
    pending_requests[request_id] = future

    try:
        await active_connections[box_id].send_json(payload)

        response_data = await asyncio.wait_for(future, timeout=10.0)

        resp_payload = response_data.get("payload", {})
        return Response(
            content=resp_payload.get("body"),
            status_code=resp_payload.get("status", 200),
            media_type=resp_payload.get("headers", {}).get("content-type", "application/json")
        )

    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Target server timed out")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Proxy error: {str(e)}")
    finally:
        await pending_requests.pop(request_id, None)

@app.get("/")
async def read_root():
    return {"status": "running"}

@app.post("/register")
async def register(user: RegisterRequest):
    try:
        # Check if username already exists
        if check_username_exists(supabase, user.username):
            raise HTTPException(
                status_code=400,
                detail={"error": "username_taken", "message": f"Username '{user.username}' is already taken"}
            )
        
        response = create_user(supabase, user.email, user.password, user.username)
        
        # Check for email already registered error55
        if hasattr(response, 'user') and response.user is None:
            raise HTTPException(
                status_code=400,
                detail={"error": "email_taken", "message": "Email is already registered"}
            )
        
        return {
            "status": "success",
            "message": "User registered successfully",
            "user": response
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/login")
async def login(user: LoginRequest):
    try:
        response = login_user(supabase, user.email, user.password)
        return {
            "status": "success",
            "message": "User logged in successfully",
            "user": response
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

