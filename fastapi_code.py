from typing import Dict
import asyncio
import uuid
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Response, Request, Depends, Cookie
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from supabase_code import initialize_supabase, create_user, login_user, check_username_exists, check_if_box_exists, \
    update_box_status, validate_access_token, get_box_owner, verify_unclaimed_server_password, claim_box, \
    find_user_by_username_or_email, assign_server_to_user, check_server_assignment_exists, \
    remove_server_assignment, get_server_assignments, get_user_servers
import json

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", "https://localhost:5173",
        "http://127.0.0.1:5500", "http://localhost:5500",
        "https://127.0.0.1:5500", "https://localhost:5500",
        "http://localhost:8000", "http://127.0.0.1:8000",
        "https://localhost:8000", "https://127.0.0.1:8000",
        "https://localhost:8443", "https://127.0.0.1:8443",
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

class ClaimBoxRequest(BaseModel):
    box_id: str
    password: str

class AssignServerRequest(BaseModel):
    server_id: str
    user_identifier: str  # Can be username or email

class RemoveAssignmentRequest(BaseModel):
    server_id: str
    user_id: str

async def get_current_user(access_token: str = Cookie(None)):
    if not access_token:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated - no access token found"
        )

    user = validate_access_token(supabase, access_token)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )
    return user


def set_auth_cookies(response: Response, session, secure: bool = True):
    response.set_cookie(
        key="access_token",
        value=session.access_token,
        httponly=True,
        secure=secure,
        samesite="none" if secure else "lax",
        max_age=session.expires_in if hasattr(session, 'expires_in') else 3600
    )
    if hasattr(session, 'refresh_token') and session.refresh_token:
        response.set_cookie(
            key="refresh_token",
            value=session.refresh_token,
            httponly=True,
            secure=secure,
            samesite="none" if secure else "lax",
            max_age=60 * 60 * 24 * 7
        )


@app.websocket("/ws/gateway")
async def websocket_gateway(websocket: WebSocket):
    await websocket.accept()
    box_id = None

    try:
        data = await websocket.receive_json()

        if data.get("type") == "IDENTIFY":
            provided_id = data.get("box_id")
            provided_password = data.get("password")

            result = check_if_box_exists(supabase, provided_id, provided_password)

            if not result:
                await websocket.close(code=4001, reason="Invalid Identity")
                return

            box_id = result.get("server_id")
            claim_password = result.get("claim_password")

            if claim_password:
                await websocket.send_json({
                    "type": "REGISTERED",
                    "payload": {
                        "box_id": box_id,
                        "claim_password": claim_password
                    }
                })

            if provided_id != box_id:
                await websocket.send_json({
                    "type": "PROVISION",
                    "payload": {"box_id": box_id}
                })

            active_connections[box_id] = websocket
            update_box_status(supabase, box_id, "online")
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
            update_box_status(supabase, box_id, "offline")


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
        response_body = resp_payload.get("body")

        if isinstance(response_body, (dict, list)):
            response_body = json.dumps(response_body)

        return Response(
            content=response_body,
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
        if check_username_exists(supabase, user.username):
            raise HTTPException(
                status_code=400,
                detail={"error": "username_taken", "message": f"Username '{user.username}' is already taken"}
            )
        
        auth_response = create_user(supabase, user.email, user.password, user.username)

        if hasattr(auth_response, 'user') and auth_response.user is None:
            raise HTTPException(
                status_code=400,
                detail={"error": "email_taken", "message": "Email is already registered"}
            )

        response_data = {
            "status": "success",
            "message": "User registered successfully",
            "user": {
                "id": auth_response.user.id if auth_response.user else None,
                "email": auth_response.user.email if auth_response.user else None,
                "user_metadata": auth_response.user.user_metadata if auth_response.user else None
            }
        }

        response = JSONResponse(content=response_data)

        if hasattr(auth_response, 'session') and auth_response.session:
            set_auth_cookies(response, auth_response.session)

        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/login")
async def login(user: LoginRequest):
    try:
        auth_response = login_user(supabase, user.email, user.password)

        response_data = {
            "status": "success",
            "message": "User logged in successfully",
            "user": {
                "id": auth_response.user.id if auth_response.user else None,
                "email": auth_response.user.email if auth_response.user else None,
                "user_metadata": auth_response.user.user_metadata if auth_response.user else None
            }
        }

        response = JSONResponse(content=response_data)

        # Set auth cookies
        if hasattr(auth_response, 'session') and auth_response.session:
            set_auth_cookies(response, auth_response.session)

        return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/logout")
async def logout():
    response = JSONResponse(content={"status": "success", "message": "Logged out successfully"})
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")
    return response


@app.get("/me")
async def get_me(current_user = Depends(get_current_user)):
    return {
        "status": "success",
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "user_metadata": current_user.user_metadata
        }
    }


@app.post("/api/boxes/claim")
async def claim_box_endpoint(request: ClaimBoxRequest, current_user = Depends(get_current_user)):
    try:
        box_exists = check_if_box_exists(supabase, request.box_id)
        if not box_exists:
            raise HTTPException(
                status_code=404,
                detail={"error": "box_not_found", "message": "Box not found"}
            )

        existing_owner = get_box_owner(supabase, request.box_id)
        if existing_owner:
            raise HTTPException(
                status_code=400,
                detail={"error": "box_already_claimed", "message": "This box has already been claimed by another user"}
            )

        if not verify_unclaimed_server_password(supabase, request.box_id, request.password):
            raise HTTPException(
                status_code=403,
                detail={"error": "invalid_password", "message": "Invalid claim password"}
            )

        success = claim_box(supabase, request.box_id, current_user.id)
        if not success:
            raise HTTPException(
                status_code=500,
                detail={"error": "claim_failed", "message": "Failed to claim the box"}
            )

        return {
            "status": "success",
            "message": "Box claimed successfully",
            "box_id": request.box_id
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/boxes/assign")
async def assign_server_endpoint(request: AssignServerRequest, current_user = Depends(get_current_user)):
    try:
        server_exists = check_if_box_exists(supabase, request.server_id)
        if not server_exists:
            raise HTTPException(
                status_code=404,
                detail={"error": "server_not_found", "message": "Server not found"}
            )

        owner_id = get_box_owner(supabase, request.server_id)
        if owner_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail={"error": "not_owner", "message": "You are not the owner of this server"}
            )

        target_user = find_user_by_username_or_email(supabase, request.user_identifier)
        if not target_user:
            raise HTTPException(
                status_code=404,
                detail={"error": "user_not_found", "message": "User not found with the provided username or email"}
            )

        if target_user["id"] == current_user.id:
            raise HTTPException(
                status_code=400,
                detail={"error": "cannot_assign_to_self", "message": "You cannot assign a server to yourself"}
            )

        if check_server_assignment_exists(supabase, request.server_id, target_user["id"]):
            raise HTTPException(
                status_code=400,
                detail={"error": "assignment_exists", "message": "This user already has access to this server"}
            )

        success = assign_server_to_user(supabase, request.server_id, current_user.id, target_user["id"])
        if not success:
            raise HTTPException(
                status_code=500,
                detail={"error": "assignment_failed", "message": "Failed to assign server to user"}
            )

        return {
            "status": "success",
            "message": "Server assigned successfully",
            "server_id": request.server_id,
            "assigned_to": {
                "id": target_user["id"],
                "username": target_user.get("username"),
                "email": target_user.get("email")
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/boxes/assign")
async def remove_server_assignment_endpoint(request: RemoveAssignmentRequest, current_user = Depends(get_current_user)):
    try:
        server_exists = check_if_box_exists(supabase, request.server_id)
        if not server_exists:
            raise HTTPException(
                status_code=404,
                detail={"error": "server_not_found", "message": "Server not found"}
            )

        owner_id = get_box_owner(supabase, request.server_id)
        if owner_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail={"error": "not_owner", "message": "You are not the owner of this server"}
            )

        if not check_server_assignment_exists(supabase, request.server_id, request.user_id):
            raise HTTPException(
                status_code=404,
                detail={"error": "assignment_not_found", "message": "Assignment not found"}
            )

        success = remove_server_assignment(supabase, request.server_id, request.user_id)
        if not success:
            raise HTTPException(
                status_code=500,
                detail={"error": "removal_failed", "message": "Failed to remove server assignment"}
            )

        return {
            "status": "success",
            "message": "Server assignment removed successfully",
            "server_id": request.server_id,
            "removed_user_id": request.user_id
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/boxes/{server_id}/assignments")
async def get_server_assignments_endpoint(server_id: str, current_user = Depends(get_current_user)):
    try:
        server_exists = check_if_box_exists(supabase, server_id)
        if not server_exists:
            raise HTTPException(
                status_code=404,
                detail={"error": "server_not_found", "message": "Server not found"}
            )

        owner_id = get_box_owner(supabase, server_id)
        if owner_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail={"error": "not_owner", "message": "You are not the owner of this server"}
            )

        assignments = get_server_assignments(supabase, server_id)

        return {
            "status": "success",
            "server_id": server_id,
            "assignments": assignments
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/boxes")
async def get_user_servers_endpoint(current_user = Depends(get_current_user)):
    try:
        servers = get_user_servers(supabase, current_user.id)

        return {
            "status": "success",
            "servers": servers
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
