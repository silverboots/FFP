import streamlit as st
st.set_page_config(
    page_title="Home",
    page_icon="🏠",
    layout="wide"
)

import pandas as pd


def style_alternating_rows(df: pd.DataFrame):
    """Apply alternating row colors to a dataframe."""
    def highlight_rows(row):
        if row.name % 2 == 0:
            return ["background-color: #f8f9fa"] * len(row)
        return ["background-color: #ffffff"] * len(row)
    return df.style.apply(highlight_rows, axis=1)
from database.sync_helpers import init_db
from database.lookup_helpers import get_user_team, get_current_gameweek
from auth.auth_services import create_user, authenticate
from auth.session_manager import get_cookie_manager, check_auth, login_user, logout
from fplapi.fpl_services import fetch_fpl_entry, FPLError

# Initialize database
init_db()

# Cookie manager for session persistence (must not be cached as it uses widgets)
cookie_manager = get_cookie_manager()


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


# Check for existing session from cookie
auth_status = check_auth(cookie_manager)

# If still loading cookies, rerun to wait for cookie manager
if auth_status is None:
    st.rerun()

is_authenticated = auth_status

# ============= NOT AUTHENTICATED - SHOW LOGIN/SIGNUP =============
if not is_authenticated:
    st.title("Welcome to Fantasy Football Planner")
    
    tab_login, tab_signup = st.tabs(["Log in", "Sign up"])

    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            remember_me = st.checkbox("Remember me", value=True)
            submitted = st.form_submit_button("Log in")
        if submitted:
            user = authenticate(email, password)
            if user:
                st.session_state.auth = {"is_authed": True, "user_email": user.email}
                if remember_me:
                    login_user(cookie_manager, user.email)
                st.success(f"Login successful! Welcome, {user.email}")
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

# ============= AUTHENTICATED - SHOW FANTASY TEAM =============

# Sidebar with user info and logout
st.sidebar.write(f"Signed in as **{st.session_state.auth['user_email']}**")

def do_logout():
    logout(cookie_manager)

st.sidebar.button("Log out", on_click=do_logout, key="logout_btn")

# Get current gameweek
gameweek = get_current_gameweek()

st.title("My Fantasy Team")
if gameweek:
    st.caption(f"Gameweek {gameweek}")

# Get user's team
user_email = st.session_state.auth["user_email"]
team_data = get_user_team(user_email)

if not team_data:
    st.warning("No team data found. Please ensure your team has been synced.")
    st.stop()

# Convert to DataFrame
df = pd.DataFrame(team_data)

# Calculate summary stats
total_value = df["cost"].sum()
total_points = df["total_points"].sum()
gw_points = df[df["squad_pos"] <= 11]["event_points"].sum()  # Only starting XI

# Team Summary
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Team Value", f"£{total_value:.1f}m")
with col2:
    st.metric("Total Points", f"{total_points}")
with col3:
    st.metric("Gameweek Points", f"{gw_points}")

st.divider()


def format_name(row):
    """Format player name with captain/VC indicator."""
    name = row["name"]
    if row["is_captain"]:
        return f"{name} (C)"
    elif row["is_vice_captain"]:
        return f"{name} (V)"
    return name


def get_status_emoji(status):
    """Return emoji for player status."""
    status_map = {
        "a": "✅",  # Available
        "d": "⚠️",  # Doubtful
        "i": "🔴",  # Injured
        "s": "🔴",  # Suspended
        "u": "❓",  # Unknown
        "n": "🚫",  # Not available
    }
    return status_map.get(status, "❓")


# Add formatted columns
df["Player"] = df.apply(format_name, axis=1)
df["Status"] = df["status"].apply(get_status_emoji)

# Define columns for display
core_cols = ["pos_type", "Player", "club", "Status"]
perf_cols = ["total_points", "event_points", "form", "ppg"]
value_cols = ["cost", "pts_per_pound", "pts_per_pound_l3"]
advanced_cols = ["ict_index", "influence", "creativity", "threat"]
metric_cols = ["player_rating", "player_rank", "selection_likelihood", "min_per_90", "early_sub", "diff_next_3"]
fixture_cols = ["fix_1", "fix_1_atk", "fix_1_def",
                "fix_2", "fix_2_atk", "fix_2_def",
                "fix_3", "fix_3_atk", "fix_3_def",
                "fix_4", "fix_4_atk", "fix_4_def",
                "fix_5", "fix_5_atk", "fix_5_def",
                "fix_6", "fix_6_atk", "fix_6_def"]

# Rename columns for display
column_rename = {
    "pos_type": "Pos",
    "total_points": "Pts",
    "event_points": "GW",
    "form": "Form",
    "ppg": "PPG",
    "cost": "Cost",
    "pts_per_pound": "Pts/£",
    "pts_per_pound_l3": "Pts/£ L3",
    "ict_index": "ICT",
    "influence": "Infl",
    "creativity": "Creat",
    "threat": "Threat",
    "player_rating": "Rating",
    "player_rank": "Rank",
    "selection_likelihood": "Sel%",
    "min_per_90": "Min/90",
    "early_sub": "EarlySub",
    "diff_next_3": "Diff3",
    "fix_1": "GW+1",
    "fix_1_atk": "Atk1",
    "fix_1_def": "Def1",
    "fix_2": "GW+2",
    "fix_2_atk": "Atk2",
    "fix_2_def": "Def2",
    "fix_3": "GW+3",
    "fix_3_atk": "Atk3",
    "fix_3_def": "Def3",
    "fix_4": "GW+4",
    "fix_4_atk": "Atk4",
    "fix_4_def": "Def4",
    "fix_5": "GW+5",
    "fix_5_atk": "Atk5",
    "fix_5_def": "Def5",
    "fix_6": "GW+6",
    "fix_6_atk": "Atk6",
    "fix_6_def": "Def6",
}

# All display columns
all_display_cols = core_cols + perf_cols + value_cols + advanced_cols + metric_cols + fixture_cols

# Starting XI
st.subheader("Starting XI")
starting_xi = df[df["squad_pos"] <= 11][all_display_cols].copy().reset_index(drop=True)
starting_xi = starting_xi.rename(columns=column_rename)

st.dataframe(
    style_alternating_rows(starting_xi),
    width="stretch",
    hide_index=True,
    height=422,
    column_config={
        "Pts": st.column_config.NumberColumn("Pts", format="%d"),
        "GW": st.column_config.NumberColumn("GW", format="%d"),
        "Rank": st.column_config.NumberColumn("Rank", format="%d"),
        "Sel%": st.column_config.NumberColumn("Sel%", format="%d"),
    }
)

# Bench
st.subheader("Bench")
bench = df[df["squad_pos"] > 11][all_display_cols].copy().reset_index(drop=True)
bench = bench.rename(columns=column_rename)

st.dataframe(
    style_alternating_rows(bench),
    width="stretch",
    hide_index=True,
    column_config={
        "Pts": st.column_config.NumberColumn("Pts", format="%d"),
        "GW": st.column_config.NumberColumn("GW", format="%d"),
        "Rank": st.column_config.NumberColumn("Rank", format="%d"),
        "Sel%": st.column_config.NumberColumn("Sel%", format="%d"),
    }
)

# Expandable section for player news
with st.expander("Player News & Availability"):
    news_df = df[df["news"] != ""][["Player", "club", "Status", "news", "chance_next"]].copy().reset_index(drop=True)
    news_df = news_df.rename(columns={"news": "News", "chance_next": "Chance %"})
    if not news_df.empty:
        st.dataframe(style_alternating_rows(news_df), width="stretch", hide_index=True)
    else:
        st.info("No player news available.")
