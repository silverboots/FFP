import streamlit as st
import pandas as pd
from database.helpers import init_db
from auth.auth_services import create_user, authenticate
from fplapi.fpl_services import fetch_fpl_entry, FPLError


def lookup_entry(team_id: str):
    try:
        entry_id = int(team_id)
        if entry_id == 0:
            raise FPLError("Invalid team id")
        
        # If already looked up for this exact entry_id, do nothing
        prev_id = st.session_state.get("signup_entry_id")
        if prev_id == entry_id and "signup_entry_data" in st.session_state:
            return
        
        # Otherwise fetch and store
        data = fetch_fpl_entry(entry_id)
        st.session_state["signup_entry_id"] = entry_id
        st.session_state["signup_team_name"] = data["name"]
        st.session_state["signup_player_name"] = data["player_first_name"]
        st.session_state["signup_message"] = f'you selected {data["name"]}'
    except ValueError as e:
        st.session_state["signup_entry_id"] = None
        st.session_state["signup_team_name"] = None
        st.session_state["signup_player_name"] = None
        st.session_state["signup_message"] = f'"Invalid team id : {team_id}"'
    except FPLError as e:
        st.session_state["signup_entry_id"] = None
        st.session_state["signup_team_name"] = None
        st.session_state["signup_player_name"] = None
        st.session_state["signup_message"] = f'" This is not working becasue of {e}"'


st.set_page_config(
    page_title="Main Menu",
    page_icon="👋", 
    layout="centered"
)

init_db()

def ensure_auth_state():
    st.session_state.setdefault("auth", {"is_authed": False, "user_email": None})

def logout():
    st.session_state.auth = {"is_authed": False, "user_email": None}
    st.rerun()

ensure_auth_state()

if not st.session_state.auth["is_authed"]:
    tab_login, tab_signup = st.tabs(["Log in", "Sign up"])

    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Log in")
        if submitted:
            print(email, password)
            user = authenticate(email, password)
            if user:
                st.session_state.auth = {"is_authed": True, "user_email": user.email}
                st.rerun()
            else:
                st.error("Invalid email or password.")

    with tab_signup:
        team_id = st.text_input("TeamID", key="su_team_id", help="Please enter your team id from the fpl website")
        if team_id:
            if st.button("Validate team"):
                try:
                    with st.spinner("Looking up your team…"):
                        lookup_entry(team_id)
                    st.success(st.session_state["signup_message"])
                except (FPLError, Exception) as e:
                    st.error(st.session_state["signup_message"])

        if st.session_state.get("signup_entry_id"):
            with st.form("signup_form"):
                name = st.text_input("Name", key="su_name", value=st.session_state["signup_player_name"])
                email = st.text_input("Email", key="su_email")
                password = st.text_input("Password", type="password", key="su_pw")
                password2 = st.text_input("Confirm password", type="password", key="su_pw2")
                submitted = st.form_submit_button("Create account")
            if submitted:
                if password != password2:
                    st.error("Passwords do not match.")
                elif len(password) < 8:
                    st.error("Use at least 8 characters.")
                else:
                    try:
                        create_user(email, password, name, int(team_id))
                        st.success("Account created. You can log in now.")
                    except ValueError as e:
                        st.error(str(e))

    st.stop()

# --- Protected content below ---
st.sidebar.write(f"Signed in as **{st.session_state.auth['user_email']}**")
st.sidebar.button("Log out", on_click=logout)

st.title("You are logged in")
st.write("Protected app content goes here.")
