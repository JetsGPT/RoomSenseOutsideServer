import os
from typing import Optional

from dotenv import load_dotenv
from supabase import create_client, Client


def initialize_supabase() -> Client:
    load_dotenv()

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in .env file")

    supabase: Client = create_client(supabase_url, supabase_key)
    return supabase



def check_username_exists(supabase: Client, username: str) -> bool:
    try:
        response = supabase.table("users").select("username").eq("username", username).execute()
        return len(response.data) > 0
    except:
        return False

def create_user(supabase: Client, email: str, password: str, username: str):
    response = supabase.auth.sign_up(
        {
            "email": email,
            "password": password,
            "options": {"data": {"username": username}},
        }
    )
    return response

def login_user(supabase: Client, email: str, password: str):
    response = supabase.auth.sign_in_with_password(
        {
            "email": email,
            "password": password,
        }
    )
    return response


def validate_access_token(supabase: Client, access_token: str):
    if not access_token:
        return None

    try:
        user_response = supabase.auth.get_user(access_token)
        if user_response and user_response.user:
            return user_response.user
        return None
    except Exception:
        return None


def check_if_box_exists(supabase: Client, server_id: Optional[str], password: Optional[str] = None) -> Optional[dict]:
    if server_id:
        try:
            res = supabase.table("connected_servers").select("id").eq("id", server_id).execute()
            if res.data:
                return {"server_id": res.data[0]['id']}

            if password:
                new_server = check_new_server(supabase, server_id, password)
                if new_server:
                    result = register_new_server(supabase, server_id, new_server.get("metadata"))
                    if result:
                        return result
        except Exception as e:
            print(f"Error verifying server ID: {e}")
            return None
    return None


def check_new_server(supabase: Client, server_id: str, password: str) -> Optional[dict]:
    try:
        res = supabase.table("new_servers").select("*").eq("server_id", server_id).execute()
        if res.data and len(res.data) > 0:
            stored_password = res.data[0].get("password")
            if stored_password == password:
                return res.data[0]
        return None
    except Exception as e:
        print(f"Error checking new server: {e}")
        return None


def generate_claim_password(length: int = 12) -> str:
    import secrets
    import string
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def register_new_server(supabase: Client, server_id: str, metadata: Optional[dict] = None) -> Optional[dict]:
    try:
        claim_password = generate_claim_password()

        insert_data = {
            "id": server_id,
            "status": "offline",
            "metadata": metadata or {}
        }
        supabase.table("connected_servers").insert(insert_data).execute()

        supabase.table("unclaimed_servers").insert({
            "server_id": server_id,
            "password": claim_password,
            "created_at": "now()"
        }).execute()

        supabase.table("new_servers").delete().eq("server_id", server_id).execute()

        return {
            "server_id": server_id,
            "claim_password": claim_password
        }
    except Exception as e:
        print(f"Error registering new server: {e}")
        return None


def update_box_status(supabase: Client, server_id: str, status: str):
    try:
        supabase.table("connected_servers").update({
            "status": status,
            "last_seen": "now()"
        }).eq("id", server_id).execute()
    except Exception as e:
        print(f"Error updating status: {e}")


def get_box_owner(supabase: Client, box_id: str) -> Optional[str]:
    try:
        response = supabase.table("connected_servers").select("owner").eq("id", box_id).execute()
        if response.data and len(response.data) > 0:
            return response.data[0].get("owner")
        return None
    except Exception as e:
        print(f"Error getting box owner: {e}")
        return None


def verify_unclaimed_server_password(supabase: Client, box_id: str, password: str) -> bool:
    try:
        response = supabase.table("unclaimed_servers").select("password").eq("server_id", box_id).execute()
        if response.data and len(response.data) > 0:
            stored_password = response.data[0].get("password")
            return stored_password == password
        return False
    except Exception as e:
        print(f"Error verifying unclaimed server password: {e}")
        return False


def claim_box(supabase: Client, box_id: str, user_id: str) -> bool:
    try:
        supabase.table("connected_servers").update({
            "owner": user_id
        }).eq("id", box_id).execute()

        supabase.table("unclaimed_servers").delete().eq("server_id", box_id).execute()

        return True
    except Exception as e:
        print(f"Error claiming box: {e}")
        return False


def find_user_by_username_or_email(supabase: Client, identifier: str) -> Optional[dict]:
    try:
        response = supabase.table("users").select("id, username, email").eq("username", identifier).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]

        response = supabase.table("users").select("id, username, email").eq("email", identifier).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]

        return None
    except Exception as e:
        print(f"Error finding user: {e}")
        return None


def assign_server_to_user(supabase: Client, server_id: str, owner_id: str, target_user_id: str) -> bool:
    try:
        supabase.table("server_assignments").insert({
            "server_id": server_id,
            "assigned_by": owner_id,
            "assigned_to": target_user_id
        }).execute()
        return True
    except Exception as e:
        print(f"Error assigning server: {e}")
        return False


def check_server_assignment_exists(supabase: Client, server_id: str, user_id: str) -> bool:
    try:
        response = supabase.table("server_assignments").select("id").eq("server_id", server_id).eq("assigned_to", user_id).execute()
        return len(response.data) > 0
    except Exception as e:
        print(f"Error checking server assignment: {e}")
        return False


def remove_server_assignment(supabase: Client, server_id: str, user_id: str) -> bool:
    try:
        supabase.table("server_assignments").delete().eq("server_id", server_id).eq("assigned_to", user_id).execute()
        return True
    except Exception as e:
        print(f"Error removing server assignment: {e}")
        return False


def get_server_assignments(supabase: Client, server_id: str) -> list:
    try:
        response = supabase.table("server_assignments").select("*, users!assigned_to(id, username, email)").eq("server_id", server_id).execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"Error getting server assignments: {e}")
        return []


def request_email_change(supabase: Client, access_token: str, new_email: str) -> dict:
    try:
        user_response = supabase.auth.get_user(access_token)
        if not user_response or not user_response.user:
            return {"success": False, "error": "invalid_token", "message": "Invalid or expired token"}

        current_email = user_response.user.email
        if current_email == new_email:
            return {"success": False, "error": "same_email", "message": "New email is the same as current email"}

        update_response = supabase.auth.update_user({
            "email": new_email
        })

        if update_response and update_response.user:
            return {
                "success": True,
                "message": "Confirmation email sent. Please check your inbox to confirm the email change.",
                "new_email": new_email
            }

        return {"success": False, "error": "update_failed", "message": "Failed to initiate email change"}
    except Exception as e:
        error_message = str(e)
        if "email_exists" in error_message.lower() or "already registered" in error_message.lower():
            return {"success": False, "error": "email_exists", "message": "This email is already registered to another account"}
        if "rate limit" in error_message.lower():
            return {"success": False, "error": "rate_limit", "message": "Too many requests. Please try again later."}
        print(f"Error requesting email change: {e}")
        return {"success": False, "error": "unknown", "message": str(e)}


def verify_email_change_token(supabase: Client, token_hash: str, token_type: str = "email_change") -> dict:
    try:
        response = supabase.auth.verify_otp({
            "token_hash": token_hash,
            "type": token_type
        })

        if response and response.user:
            return {
                "success": True,
                "user": response.user,
                "session": response.session
            }

        return {"success": False, "error": "verification_failed", "message": "Failed to verify email change"}
    except Exception as e:
        print(f"Error verifying email change token: {e}")
        return {"success": False, "error": "verification_failed", "message": str(e)}


def get_user_servers(supabase: Client, user_id: str) -> dict:
    try:
        owned_response = supabase.table("connected_servers").select(
            "id, name, created_at, last_seen, status, metadata, owner, users!owner(username)"
        ).eq("owner", user_id).execute()

        owned_servers = []
        if owned_response.data:
            for server in owned_response.data:
                owner_info = server.get("users", {})
                owned_servers.append({
                    "id": server.get("id"),
                    "name": server.get("name"),
                    "created_at": server.get("created_at"),
                    "last_seen": server.get("last_seen"),
                    "status": server.get("status"),
                    "metadata": server.get("metadata"),
                    "owner_username": owner_info.get("username") if owner_info else None,
                    "role": "owner"
                })

        assigned_response = supabase.table("server_assignments").select(
            "server_id, connected_servers!server_id(id, name, created_at, last_seen, status, metadata, owner, users!owner(username))"
        ).eq("assigned_to", user_id).execute()

        assigned_servers = []
        if assigned_response.data:
            for assignment in assigned_response.data:
                server = assignment.get("connected_servers", {})
                if server:
                    owner_info = server.get("users", {})
                    assigned_servers.append({
                        "id": server.get("id"),
                        "name": server.get("name"),
                        "created_at": server.get("created_at"),
                        "last_seen": server.get("last_seen"),
                        "status": server.get("status"),
                        "metadata": server.get("metadata"),
                        "owner_username": owner_info.get("username") if owner_info else None,
                        "role": "assigned"
                    })

        return {
            "owned": owned_servers,
            "assigned": assigned_servers
        }
    except Exception as e:
        print(f"Error getting user servers: {e}")
        return {"owned": [], "assigned": []}


# =============================================================================
# Notification System Functions
# =============================================================================

def verify_server_identity(supabase: Client, server_id: str, identity_token: str) -> bool:
    """
    Verify that a server identity token is valid.
    This is used to authenticate relay requests from Local Servers.
    """
    try:
        response = supabase.table("connected_servers").select(
            "id, identity_token"
        ).eq("id", server_id).execute()

        if response.data and len(response.data) > 0:
            stored_token = response.data[0].get("identity_token")
            return stored_token == identity_token
        return False
    except Exception as e:
        print(f"Error verifying server identity: {e}")
        return False


def register_server_identity_token(supabase: Client, server_id: str, identity_token: str) -> bool:
    """Register or update a server's identity token."""
    try:
        supabase.table("connected_servers").update({
            "identity_token": identity_token
        }).eq("id", server_id).execute()
        return True
    except Exception as e:
        print(f"Error registering server identity token: {e}")
        return False


def log_notification(
    supabase: Client,
    server_id: str,
    provider: str,
    target: str,
    title: str,
    message: str,
    priority: str,
    success: bool,
    status_code: Optional[int] = None,
    error_message: Optional[str] = None,
    response_data: Optional[dict] = None
) -> Optional[dict]:
    """
    Log a notification relay attempt to the database for audit purposes.
    """
    try:
        log_entry = {
            "server_id": server_id,
            "provider": provider,
            "target": target,
            "title": title,
            "message": message,
            "priority": priority,
            "success": success,
            "status_code": status_code,
            "error_message": error_message,
            "response_data": response_data,
            "created_at": "now()"
        }

        response = supabase.table("notification_logs").insert(log_entry).execute()

        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        print(f"Error logging notification: {e}")
        return None


def get_notification_logs(
    supabase: Client,
    server_id: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> list:
    """
    Retrieve notification logs, optionally filtered by server_id.
    """
    try:
        query = supabase.table("notification_logs").select("*").order(
            "created_at", desc=True
        ).limit(limit).offset(offset)

        if server_id:
            query = query.eq("server_id", server_id)

        response = query.execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"Error getting notification logs: {e}")
        return []


def get_global_notification_config(supabase: Client, config_key: str) -> Optional[dict]:
    """
    Get a global notification configuration value.
    """
    try:
        response = supabase.table("global_notification_config").select(
            "*"
        ).eq("config_key", config_key).execute()

        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        print(f"Error getting global config: {e}")
        return None


def set_global_notification_config(
    supabase: Client,
    config_key: str,
    config_value: dict,
    description: Optional[str] = None
) -> bool:
    """
    Set or update a global notification configuration value.
    Uses upsert to create or update the config entry.
    """
    try:
        data = {
            "config_key": config_key,
            "config_value": config_value,
            "description": description,
            "updated_at": "now()"
        }

        supabase.table("global_notification_config").upsert(
            data, on_conflict="config_key"
        ).execute()
        return True
    except Exception as e:
        print(f"Error setting global config: {e}")
        return False


def get_all_global_notification_configs(supabase: Client) -> list:
    """
    Get all global notification configuration values.
    """
    try:
        response = supabase.table("global_notification_config").select("*").execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"Error getting all global configs: {e}")
        return []


def delete_global_notification_config(supabase: Client, config_key: str) -> bool:
    """
    Delete a global notification configuration value.
    """
    try:
        supabase.table("global_notification_config").delete().eq(
            "config_key", config_key
        ).execute()
        return True
    except Exception as e:
        print(f"Error deleting global config: {e}")
        return False


def get_server_notification_settings(supabase: Client, server_id: str) -> Optional[dict]:
    """
    Get notification settings for a specific server.
    """
    try:
        response = supabase.table("server_notification_settings").select(
            "*"
        ).eq("server_id", server_id).execute()

        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        print(f"Error getting server notification settings: {e}")
        return None


def set_server_notification_settings(
    supabase: Client,
    server_id: str,
    settings: dict
) -> bool:
    """
    Set or update notification settings for a specific server.
    """
    try:
        data = {
            "server_id": server_id,
            **settings,
            "updated_at": "now()"
        }

        supabase.table("server_notification_settings").upsert(
            data, on_conflict="server_id"
        ).execute()
        return True
    except Exception as e:
        print(f"Error setting server notification settings: {e}")
        return False

