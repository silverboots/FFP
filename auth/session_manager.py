"""Session management utilities for authentication across pages."""
import streamlit as st
import extra_streamlit_components as stx
from datetime import datetime, timedelta
from auth.auth_services import get_user_by_email

COOKIE_NAME = "ffp_session"
COOKIE_EXPIRY_DAYS = 30


def get_cookie_manager():
    """Get the cookie manager instance."""
    # Use a consistent key for the cookie manager
    return stx.CookieManager(key="cookie_manager_main")


def ensure_auth_state():
    """Ensure auth state exists in session state."""
    st.session_state.setdefault("auth", {"is_authed": False, "user_email": None})


def check_auth(cookie_manager):
    """
    Check session state and cookie for authentication.

    Returns:
        True if authenticated, False if not authenticated, None if still loading cookies
    """
    ensure_auth_state()

    # Already authenticated in session state - this persists across page navigation
    if st.session_state.auth["is_authed"]:
        return True

    # Try to get all cookies - this returns a dict on successful load
    try:
        all_cookies = cookie_manager.get_all()
    except Exception:
        all_cookies = None

    # Cookie manager hasn't loaded yet
    if all_cookies is None:
        # Use a counter to prevent infinite loops (max 2 attempts per page load)
        cookie_load_attempts = st.session_state.get("_cookie_load_attempts", 0)

        if cookie_load_attempts < 2:
            st.session_state["_cookie_load_attempts"] = cookie_load_attempts + 1
            return None  # Still loading
        else:
            # After attempts, assume no cookie exists
            return False

    # Reset the counter on successful cookie load
    st.session_state["_cookie_load_attempts"] = 0

    # Check if our cookie exists in the loaded cookies
    session_email = all_cookies.get(COOKIE_NAME)

    # Cookie exists, verify user
    if session_email:
        user = get_user_by_email(session_email)
        if user:
            st.session_state.auth = {"is_authed": True, "user_email": user.email}
            return True
        else:
            # Invalid cookie, clear it
            try:
                cookie_manager.delete(COOKIE_NAME)
            except Exception:
                pass

    return False


def login_user(cookie_manager, email: str):
    """Set session state and cookie for logged in user."""
    st.session_state.auth = {"is_authed": True, "user_email": email}
    st.session_state["_cookie_load_attempts"] = 0
    # Set cookie with expiration date (30 days from now) - datetime object
    expires_at = datetime.now() + timedelta(days=COOKIE_EXPIRY_DAYS)
    # Try with lax same_site for localhost compatibility
    cookie_manager.set(
        cookie=COOKIE_NAME, 
        val=email, 
        expires_at=expires_at,
        same_site="lax",
        key="set_login_cookie"
    )


def logout(cookie_manager):
    """Clear session state and cookie."""
    st.session_state.auth = {"is_authed": False, "user_email": None}
    st.session_state["_cookie_load_attempts"] = 0
    st.session_state["_cookie_set"] = False
    try:
        cookie_manager.delete(COOKIE_NAME, key="logout_delete_cookie")
    except:
        pass  # Cookie might not exist
