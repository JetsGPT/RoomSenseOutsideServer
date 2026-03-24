from typing import Dict, Optional, List
import asyncio
import uuid
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Response, Request, Depends, Cookie, Header
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel

from notification_forwarders import NotificationPriority, NotificationPayload, ForwardResult, notification_router
from supabase_code import initialize_supabase, create_user, login_user, check_username_exists, check_if_box_exists, \
    update_box_status, validate_access_token, get_box_owner, verify_unclaimed_server_password, claim_box, \
    find_user_by_username_or_email, assign_server_to_user, check_server_assignment_exists, \
    remove_server_assignment, get_server_assignments, get_user_servers, request_email_change, \
    verify_email_change_token, get_server_notification_settings, get_global_notification_config, log_notification, \
    delete_global_notification_config, set_server_notification_settings, get_notification_logs, \
    register_server_identity_token, get_all_global_notification_configs, set_global_notification_config, \
    verify_server_identity
import json

from fastapi.middleware.cors import CORSMiddleware

import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        "https://roomsense.info", "https://proxy.roomsense.info",
        "https://proxy.roomsense.info:8443",
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

class EmailChangeRequest(BaseModel):
    new_email: str


# =============================================================================
# Notification System Models
# =============================================================================

class NotificationRelayRequest(BaseModel):
    """Request payload for relaying notifications from Local Servers."""
    target: str  # Target for the notification (e.g., ntfy topic, email address)
    title: str  # Notification title
    message: str  # Notification message body
    priority: str = "default"  # Priority: min, low, default, high, urgent
    provider: str = "ntfy"  # Notification provider: ntfy, email, sms
    tags: Optional[List[str]] = None  # Optional tags for the notification
    click_url: Optional[str] = None  # URL to open when notification is clicked
    attach_url: Optional[str] = None  # URL of attachment
    extra: Optional[Dict] = None  # Additional provider-specific options


class GlobalConfigRequest(BaseModel):
    """Request for setting global notification configuration."""
    config_key: str  # Configuration key (e.g., 'ntfy_base_url', 'dnd_schedule')
    config_value: Dict  # Configuration value as JSON object
    description: Optional[str] = None  # Description of this configuration


class ServerNotificationSettingsRequest(BaseModel):
    """Request for setting server-specific notification settings."""
    ntfy_enabled: Optional[bool] = True
    ntfy_base_url: Optional[str] = None
    ntfy_default_topic: Optional[str] = None
    email_enabled: Optional[bool] = False
    sms_enabled: Optional[bool] = False
    dnd_enabled: Optional[bool] = False
    dnd_start: Optional[str] = None  # e.g., "22:00"
    dnd_end: Optional[str] = None    # e.g., "07:00"


# Shared secret for relay authentication (can also be loaded from env)
RELAY_SHARED_SECRET = os.getenv("RELAY_SHARED_SECRET", None)


async def verify_relay_authorization(
    x_server_id: str = Header(None, alias="X-Server-ID"),
    x_identity_token: str = Header(None, alias="X-Identity-Token"),
    x_relay_secret: str = Header(None, alias="X-Relay-Secret")
):
    """
    Verify that the request is from an authorized Local Server.
    Supports both identity token verification and shared secret authentication.
    """
    # Check shared secret first (simpler authentication)
    if RELAY_SHARED_SECRET and x_relay_secret:
        if x_relay_secret == RELAY_SHARED_SECRET:
            return {"auth_method": "shared_secret", "server_id": x_server_id}

    # Check server identity token
    if x_server_id and x_identity_token:
        if verify_server_identity(supabase, x_server_id, x_identity_token):
            return {"auth_method": "identity_token", "server_id": x_server_id}

    raise HTTPException(
        status_code=401,
        detail={
            "error": "unauthorized",
            "message": "Invalid or missing server authentication credentials"
        }
    )


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
        pending_requests.pop(request_id, None)

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


@app.post("/api/user/email")
async def change_email(
    request: EmailChangeRequest,
    access_token: str = Cookie(None),
    current_user = Depends(get_current_user)
):
    if not access_token:
        raise HTTPException(
            status_code=401,
            detail={"error": "not_authenticated", "message": "Not authenticated"}
        )

    if not request.new_email or "@" not in request.new_email:
        raise HTTPException(
            status_code=400,
            detail={"error": "invalid_email", "message": "Please provide a valid email address"}
        )

    result = request_email_change(supabase, access_token, request.new_email)

    if not result["success"]:
        error_code = result.get("error", "unknown")
        status_codes = {
            "invalid_token": 401,
            "same_email": 400,
            "email_exists": 400,
            "rate_limit": 429,
            "unknown": 500
        }
        raise HTTPException(
            status_code=status_codes.get(error_code, 500),
            detail={"error": error_code, "message": result.get("message", "Failed to change email")}
        )

    return {
        "status": "success",
        "message": result["message"],
        "new_email": result["new_email"]
    }


@app.get("/auth/callback")
async def auth_callback(
    response: Response,
    token_hash: str = None,
    type: str = None,
    error: str = None,
    error_description: str = None
):
    frontend_success_url = "https://roomsense.info/settings?email_changed=true"
    frontend_error_url = "https://roomsense.info/settings?email_change_error=true"

    if error:
        error_msg = error_description or error
        return RedirectResponse(
            url=f"{frontend_error_url}&message={error_msg}",
            status_code=303
        )

    if not token_hash or not type:
        return RedirectResponse(
            url=f"{frontend_error_url}&message=Invalid callback parameters",
            status_code=303
        )

    if type == "email_change":
        result = verify_email_change_token(supabase, token_hash, type)

        if not result["success"]:
            return RedirectResponse(
                url=f"{frontend_error_url}&message={result.get('message', 'Verification failed')}",
                status_code=303
            )

        if result.get("session"):
            redirect_response = RedirectResponse(url=frontend_success_url, status_code=303)
            set_auth_cookies(redirect_response, result["session"], secure=True)
            return redirect_response

        return RedirectResponse(url=frontend_success_url, status_code=303)

    return RedirectResponse(
        url=f"{frontend_error_url}&message=Unknown callback type",
        status_code=303
    )


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


# =============================================================================
# Notification Relay Endpoints (for Local Servers)
# =============================================================================

@app.post("/api/v1/relay/send")
async def relay_notification(
    request: NotificationRelayRequest,
    auth_info: dict = Depends(verify_relay_authorization)
):
    """
    Relay endpoint for Local Servers to send notifications through external providers.

    This endpoint receives notification payloads from authenticated Local Servers
    and forwards them to the appropriate external provider (ntfy, email, SMS, etc.).

    Authentication: Requires either X-Server-ID + X-Identity-Token headers,
    or X-Relay-Secret header with the shared secret.
    """
    server_id = auth_info.get("server_id", "unknown")

    try:
        # Map string priority to enum
        priority_map = {
            "min": NotificationPriority.MIN,
            "low": NotificationPriority.LOW,
            "default": NotificationPriority.DEFAULT,
            "high": NotificationPriority.HIGH,
            "urgent": NotificationPriority.URGENT,
        }
        priority = priority_map.get(request.priority.lower(), NotificationPriority.DEFAULT)

        # Build the notification payload
        payload = NotificationPayload(
            target=request.target,
            title=request.title,
            message=request.message,
            priority=priority,
            tags=request.tags,
            click_url=request.click_url,
            attach_url=request.attach_url,
            extra=request.extra
        )

        # Get provider configuration
        # First check server-specific settings, then fall back to global config
        config = {}

        server_settings = get_server_notification_settings(supabase, server_id)
        if server_settings:
            if request.provider == "ntfy":
                if server_settings.get("ntfy_base_url"):
                    config["base_url"] = server_settings["ntfy_base_url"]

        # Check global config for provider settings
        global_config = get_global_notification_config(supabase, f"{request.provider}_config")
        if global_config:
            config_value = global_config.get("config_value", {})
            # Merge global config (server-specific takes precedence)
            for key, value in config_value.items():
                if key not in config:
                    config[key] = value

        # Forward to the notification router
        result: ForwardResult = await notification_router.route(
            provider=request.provider,
            payload=payload,
            config=config
        )

        # Log the notification attempt
        log_notification(
            supabase=supabase,
            server_id=server_id,
            provider=request.provider,
            target=request.target,
            title=request.title,
            message=request.message,
            priority=request.priority,
            success=result.success,
            status_code=result.status_code,
            error_message=result.error_message,
            response_data=result.response_data
        )

        if result.success:
            logger.info(f"✅ Notification relayed: {request.provider} -> {request.target} (server: {server_id})")
            return {
                "status": "success",
                "message": "Notification sent successfully",
                "provider": result.provider,
                "target": result.target,
                "status_code": result.status_code
            }
        else:
            logger.warning(f"⚠️ Notification relay failed: {result.error_message} (server: {server_id})")
            raise HTTPException(
                status_code=502,
                detail={
                    "error": "relay_failed",
                    "message": result.error_message,
                    "provider": result.provider
                }
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error relaying notification: {e}")

        # Still log the failed attempt
        log_notification(
            supabase=supabase,
            server_id=server_id,
            provider=request.provider,
            target=request.target,
            title=request.title,
            message=request.message,
            priority=request.priority,
            success=False,
            error_message=str(e)
        )

        raise HTTPException(
            status_code=500,
            detail={"error": "internal_error", "message": str(e)}
        )


@app.get("/api/v1/relay/providers")
async def list_notification_providers():
    """List all available notification providers."""
    return {
        "status": "success",
        "providers": notification_router.list_providers()
    }


# =============================================================================
# Server Identity Token Management
# =============================================================================

@app.post("/api/v1/server/register-identity")
async def register_server_identity(
    server_id: str,
    identity_token: str,
    auth_info: dict = Depends(verify_relay_authorization)
):
    """
    Register or update a server's identity token.
    Used during Local Server initialization.
    """
    success = register_server_identity_token(supabase, server_id, identity_token)

    if success:
        return {
            "status": "success",
            "message": "Server identity token registered"
        }
    else:
        raise HTTPException(
            status_code=500,
            detail={"error": "registration_failed", "message": "Failed to register identity token"}
        )


# =============================================================================
# Global Notification Configuration Endpoints
# =============================================================================

@app.get("/api/v1/config/global")
async def get_all_global_configs(current_user = Depends(get_current_user)):
    """Get all global notification configuration values."""
    configs = get_all_global_notification_configs(supabase)
    return {
        "status": "success",
        "configs": configs
    }


@app.get("/api/v1/config/global/{config_key}")
async def get_global_config(config_key: str, current_user = Depends(get_current_user)):
    """Get a specific global notification configuration."""
    config = get_global_notification_config(supabase, config_key)

    if config:
        return {
            "status": "success",
            "config": config
        }
    else:
        raise HTTPException(
            status_code=404,
            detail={"error": "not_found", "message": f"Configuration '{config_key}' not found"}
        )


@app.post("/api/v1/config/global")
async def set_global_config(
    request: GlobalConfigRequest,
    current_user = Depends(get_current_user)
):
    """
    Set or update a global notification configuration.

    Example config_keys:
    - ntfy_config: {"base_url": "https://ntfy.sh", "auth_token": "..."}
    - dnd_schedule: {"enabled": true, "start": "22:00", "end": "07:00"}
    - email_config: {"smtp_host": "...", "smtp_port": 587, "sender_email": "..."}
    """
    success = set_global_notification_config(
        supabase,
        request.config_key,
        request.config_value,
        request.description
    )

    if success:
        return {
            "status": "success",
            "message": f"Configuration '{request.config_key}' saved"
        }
    else:
        raise HTTPException(
            status_code=500,
            detail={"error": "save_failed", "message": "Failed to save configuration"}
        )


@app.delete("/api/v1/config/global/{config_key}")
async def delete_global_config(config_key: str, current_user = Depends(get_current_user)):
    """Delete a global notification configuration."""
    success = delete_global_notification_config(supabase, config_key)

    if success:
        return {
            "status": "success",
            "message": f"Configuration '{config_key}' deleted"
        }
    else:
        raise HTTPException(
            status_code=500,
            detail={"error": "delete_failed", "message": "Failed to delete configuration"}
        )


# =============================================================================
# Server-Specific Notification Settings
# =============================================================================

@app.get("/api/v1/servers/{server_id}/notification-settings")
async def get_server_notification_settings_endpoint(
    server_id: str,
    current_user = Depends(get_current_user)
):
    """Get notification settings for a specific server."""
    # Verify user has access to this server
    owner_id = get_box_owner(supabase, server_id)
    if owner_id != current_user.id:
        # Check if user is assigned to this server
        if not check_server_assignment_exists(supabase, server_id, current_user.id):
            raise HTTPException(
                status_code=403,
                detail={"error": "forbidden", "message": "You don't have access to this server"}
            )

    settings = get_server_notification_settings(supabase, server_id)

    return {
        "status": "success",
        "server_id": server_id,
        "settings": settings or {}
    }


@app.post("/api/v1/servers/{server_id}/notification-settings")
async def set_server_notification_settings_endpoint(
    server_id: str,
    request: ServerNotificationSettingsRequest,
    current_user = Depends(get_current_user)
):
    """Set notification settings for a specific server. Only the owner can modify settings."""
    # Verify user is the owner
    owner_id = get_box_owner(supabase, server_id)
    if owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail={"error": "not_owner", "message": "Only the server owner can modify notification settings"}
        )

    settings_dict = request.model_dump(exclude_none=True)
    success = set_server_notification_settings(supabase, server_id, settings_dict)

    if success:
        return {
            "status": "success",
            "message": "Notification settings saved",
            "server_id": server_id
        }
    else:
        raise HTTPException(
            status_code=500,
            detail={"error": "save_failed", "message": "Failed to save notification settings"}
        )


# =============================================================================
# Notification Logs Endpoints
# =============================================================================

@app.get("/api/v1/notifications/logs")
async def get_notification_logs_endpoint(
    server_id: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    current_user = Depends(get_current_user)
):
    """
    Get notification logs. If server_id is provided, only logs for that server are returned.
    Requires authentication and ownership/assignment verification.
    """
    if server_id:
        # Verify user has access to this server
        owner_id = get_box_owner(supabase, server_id)
        if owner_id != current_user.id:
            if not check_server_assignment_exists(supabase, server_id, current_user.id):
                raise HTTPException(
                    status_code=403,
                    detail={"error": "forbidden", "message": "You don't have access to this server"}
                )

    logs = get_notification_logs(supabase, server_id, limit, offset)

    return {
        "status": "success",
        "logs": logs,
        "count": len(logs),
        "limit": limit,
        "offset": offset
    }


@app.get("/api/v1/servers/{server_id}/notifications/logs")
async def get_server_notification_logs(
    server_id: str,
    limit: int = 100,
    offset: int = 0,
    current_user = Depends(get_current_user)
):
    """Get notification logs for a specific server."""
    # Verify user has access to this server
    owner_id = get_box_owner(supabase, server_id)
    if owner_id != current_user.id:
        if not check_server_assignment_exists(supabase, server_id, current_user.id):
            raise HTTPException(
                status_code=403,
                detail={"error": "forbidden", "message": "You don't have access to this server"}
            )

    logs = get_notification_logs(supabase, server_id, limit, offset)

    return {
        "status": "success",
        "server_id": server_id,
        "logs": logs,
        "count": len(logs),
        "limit": limit,
        "offset": offset
    }

