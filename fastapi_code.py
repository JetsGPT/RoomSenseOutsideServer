from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from supabase_code import initialize_supabase, create_user, login_user, check_username_exists

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

# Base model for parsing registration requests
class RegisterRequest(BaseModel):
    email: str
    password: str
    username: str

class LoginRequest(BaseModel):
    email: str
    password: str

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
        
        # Check for email already registered error
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

