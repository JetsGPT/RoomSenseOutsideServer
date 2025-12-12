import os
from typing import Optional

from dotenv import load_dotenv
from supabase import create_client, Client


def initialize_supabase() -> Client:
    # Load environment variables from .env
    load_dotenv()

    # Initialize Supabase client
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    # check if the environment variables are set
    if not supabase_url or not supabase_key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in .env file")

    supabase: Client = create_client(supabase_url, supabase_key)
    return supabase



def check_username_exists(supabase: Client, username: str) -> bool:
    """Check if username already exists in the users table"""
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


def check_if_box_exists(supabase: Client, server_id: Optional[str]) -> str:
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