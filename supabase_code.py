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


def check_if_box_exists(supabase: Client, server_id: Optional[str]) -> Optional[str]:
    if server_id:
        try:
            res = supabase.table("connected_servers").select("id").eq("id", server_id).execute()
            if res.data:
                return res.data[0]['id']
        except Exception as e:
            print(f"Error verifying server ID: {e}")
            return None
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
