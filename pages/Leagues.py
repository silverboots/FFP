import streamlit as st
st.set_page_config(page_title="My Leagues", page_icon="🏆", layout="wide")

import pandas as pd
from auth.session_manager import get_cookie_manager, check_auth
from database.lookup_helpers import get_user_team_id
from fplapi.fpl_services import fetch_fpl_entry_leagues, fetch_all_league_standings, FPLError

# Cookie manager for session persistence
cookie_manager = get_cookie_manager()

# Check authentication
auth_status = check_auth(cookie_manager)

# If still loading cookies, rerun to wait for cookie manager
if auth_status is None:
    st.rerun()

# If not authenticated, redirect to home/login
if not auth_status:
    st.switch_page("Home.py")

st.title("My Leagues")

# Get user's team ID
user_email = st.session_state.auth["user_email"]
team_id = get_user_team_id(user_email)

if not team_id:
    st.error("Could not find your team ID. Please ensure your account is set up correctly.")
    st.stop()


@st.cache_data(ttl=300, show_spinner=False)
def get_leagues(entry_id: int):
    """Fetch leagues with caching (5 min TTL)."""
    return fetch_fpl_entry_leagues(entry_id)


@st.cache_data(ttl=300, show_spinner=False)
def get_league_standings(league_id: int, league_type: str):
    """Fetch league standings with caching (5 min TTL)."""
    return fetch_all_league_standings(league_id, league_type)


# Fetch user's leagues
try:
    with st.spinner("Loading leagues..."):
        leagues = get_leagues(team_id)
except FPLError as e:
    st.error(f"Failed to load leagues: {e}")
    st.stop()

if not leagues:
    st.info("You are not in any leagues.")
    st.stop()

# Filter out massive public leagues (like "Overall" with millions of entries)
# Keep leagues where user has a rank, typically private/smaller leagues
private_leagues = [l for l in leagues if l.get("entry_rank") and l.get("entry_rank") < 1000000]

# Summary metrics
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Leagues", len(leagues))
with col2:
    classic_count = len([l for l in leagues if l["type"] == "classic"])
    st.metric("Classic Leagues", classic_count)
with col3:
    h2h_count = len([l for l in leagues if l["type"] == "h2h"])
    st.metric("H2H Leagues", h2h_count)

st.divider()

# League selection
st.subheader("Select a League")

# Create league options (filter to manageable leagues)
displayable_leagues = [l for l in leagues if l.get("entry_rank") and l.get("entry_rank") < 500000]

if not displayable_leagues:
    st.warning("No leagues with standings available to display.")
    st.stop()

league_options = {f"{l['name']} ({l['type'].upper()}) - Rank: {l['entry_rank']}": l for l in displayable_leagues}
selected_league_name = st.selectbox(
    "Choose league",
    options=[""] + list(league_options.keys()),
    format_func=lambda x: "Select a league to view standings..." if x == "" else x
)

if not selected_league_name:
    st.info("Select a league from the dropdown above to view standings.")
    st.stop()

selected_league = league_options[selected_league_name]

# Fetch standings for selected league
try:
    with st.spinner(f"Loading standings for {selected_league['name']}..."):
        standings_data = get_league_standings(selected_league["id"], selected_league["type"])
except FPLError as e:
    st.error(f"Failed to load standings: {e}")
    st.stop()

league_info = standings_data.get("league", {})
standings = standings_data.get("standings", [])

# League info
st.subheader(f"📊 {league_info.get('name', selected_league['name'])}")

if standings:
    # Convert to DataFrame
    df = pd.DataFrame(standings)

    # Find user's position in the standings
    user_entry = df[df["entry"] == team_id]
    if not user_entry.empty:
        user_rank = user_entry.iloc[0]["rank"]
        user_points = user_entry.iloc[0]["total"]
        st.info(f"Your position: **Rank {user_rank}** with **{user_points} points**")

    # Prepare display columns
    display_cols = []

    if "rank" in df.columns:
        display_cols.append("rank")
    if "entry_name" in df.columns:
        display_cols.append("entry_name")
    if "player_name" in df.columns:
        display_cols.append("player_name")
    if "total" in df.columns:
        display_cols.append("total")
    if "event_total" in df.columns:
        display_cols.append("event_total")
    if "rank_sort" in df.columns and "rank" not in df.columns:
        display_cols.append("rank_sort")

    # Rename columns for display
    column_rename = {
        "rank": "Rank",
        "entry_name": "Team",
        "player_name": "Manager",
        "total": "Total Pts",
        "event_total": "GW Pts",
        "rank_sort": "Rank",
    }

    display_df = df[display_cols].copy().reset_index(drop=True)
    display_df = display_df.rename(columns=column_rename)

    # Track which rows belong to the user for highlighting
    user_row_mask = (df["entry"] == team_id).reset_index(drop=True)

    # Style function to highlight user's row with green, others with alternating colors
    def highlight_rows(row):
        if user_row_mask.iloc[row.name]:
            return ["background-color: #d4edda; font-weight: bold"] * len(row)
        elif row.name % 2 == 0:
            return ["background-color: #f8f9fa"] * len(row)
        return ["background-color: #ffffff"] * len(row)

    # Apply styling
    styled_df = display_df.style.apply(highlight_rows, axis=1)

    # Calculate height to fit all rows
    table_height = (len(display_df) + 1) * 35 + 3

    st.dataframe(
        styled_df,
        width="stretch",
        hide_index=True,
        height=table_height,
        column_config={
            "Rank": st.column_config.NumberColumn("Rank", format="%d"),
            "Total Pts": st.column_config.NumberColumn("Total Pts", format="%d"),
            "GW Pts": st.column_config.NumberColumn("GW Pts", format="%d"),
        }
    )

    st.caption(f"Showing {len(standings)} teams in this league")
else:
    st.warning("No standings available for this league.")
