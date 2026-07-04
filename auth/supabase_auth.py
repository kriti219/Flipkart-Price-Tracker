import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    raise ValueError(
        "SUPABASE_URL and SUPABASE_ANON_KEY must be set in your .env file"
    )

supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)


def sign_up(email: str, password: str):
    """Register a new user with email and password."""
    return supabase.auth.sign_up({
        "email": email,
        "password": password,
    })


def sign_in(email: str, password: str):
    """Sign in an existing user, returns session with access_token."""
    return supabase.auth.sign_in_with_password({
        "email": email,
        "password": password,
    })


def sign_out(access_token: str):
    """Invalidate the user's session."""
    return supabase.auth.sign_out()


def get_user(access_token: str):
    """
    Verify a JWT token and return the user object.
    Returns None if the token is invalid or expired.
    """
    try:
        response = supabase.auth.get_user(access_token)
        return response.user
    except Exception:
        return None


def get_google_oauth_url(redirect_to: str) -> str:
    """
    Generate a Google OAuth URL.
    redirect_to: where Supabase sends the user after Google auth.
    """
    response = supabase.auth.sign_in_with_oauth({
        "provider": "google",
        "options": {"redirect_to": redirect_to},
    })
    return response.url