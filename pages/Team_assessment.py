import streamlit as st
st.set_page_config(page_title="Team Assessment", page_icon="📈", layout="wide")

import pandas as pd
from auth.session_manager import get_cookie_manager, check_auth
from database.lookup_helpers import get_user_team, get_current_gameweek

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


def style_alternating_rows(df: pd.DataFrame):
    """Apply alternating row colors to a dataframe."""
    def highlight_rows(row):
        if row.name % 2 == 0:
            return ["background-color: #f8f9fa"] * len(row)
        return ["background-color: #ffffff"] * len(row)
    return df.style.apply(highlight_rows, axis=1)


st.title("Team Assessment")

# Get current gameweek
gameweek = get_current_gameweek()
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
avg_rating = df["player_rating"].mean()
avg_rank = df["player_rank"].mean()
starting_xi = df[df["squad_pos"] <= 11]
starting_value = starting_xi["cost"].sum()

# Team Summary
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("Team Value", f"£{total_value:.1f}m")
with col2:
    st.metric("Starting XI Value", f"£{starting_value:.1f}m")
with col3:
    st.metric("Total Points", f"{total_points}")
with col4:
    st.metric("Avg Rating", f"{avg_rating:.1f}")
with col5:
    st.metric("Avg Rank", f"{avg_rank:.0f}")

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
        "a": "✅",
        "d": "⚠️",
        "i": "🔴",
        "s": "🔴",
        "u": "❓",
        "n": "🚫",
    }
    return status_map.get(status, "❓")


def get_squad_position(squad_pos):
    """Return Starting/Bench indicator."""
    return "Starting" if squad_pos <= 11 else "Bench"


# Add formatted columns
df["Player"] = df.apply(format_name, axis=1)
df["Status"] = df["status"].apply(get_status_emoji)
df["Squad"] = df["squad_pos"].apply(get_squad_position)

# Column groups for different analysis views
core_cols = ["Squad", "pos_type", "Player", "club", "Status"]
perf_cols = ["total_points", "event_points", "form", "ppg", "minutes"]
value_cols = ["cost", "pts_per_pound", "pts_per_pound_l3"]
advanced_cols = ["ict_index", "influence", "creativity", "threat"]
metric_cols = ["player_rating", "player_rank", "selection_likelihood", "min_per_90", "early_sub", "diff_next_3"]
fixture_cols = ["fix_1", "fix_1_diff", "fix_2", "fix_2_diff", "fix_3", "fix_3_diff",
                "fix_4", "fix_4_diff", "fix_5", "fix_5_diff", "fix_6", "fix_6_diff"]

# Rename columns for display
column_rename = {
    "Squad": "Squad",
    "pos_type": "Pos",
    "total_points": "Pts",
    "event_points": "GW",
    "form": "Form",
    "ppg": "PPG",
    "minutes": "Mins",
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
    "fix_1_diff": "Diff1",
    "fix_2": "GW+2",
    "fix_2_diff": "Diff2",
    "fix_3": "GW+3",
    "fix_3_diff": "Diff3",
    "fix_4": "GW+4",
    "fix_4_diff": "Diff4",
    "fix_5": "GW+5",
    "fix_5_diff": "Diff5",
    "fix_6": "GW+6",
    "fix_6_diff": "Diff6",
}

# View selection
view_option = st.selectbox(
    "Select View",
    ["Full Overview", "Performance", "Value Analysis", "Advanced Stats", "Fixtures"],
    index=0
)

# Determine which columns to show based on view
if view_option == "Full Overview":
    display_cols = core_cols + ["total_points", "form", "cost", "player_rating", "player_rank", "diff_next_3"]
elif view_option == "Performance":
    display_cols = core_cols + perf_cols
elif view_option == "Value Analysis":
    display_cols = core_cols + value_cols + ["total_points", "form"]
elif view_option == "Advanced Stats":
    display_cols = core_cols + advanced_cols + metric_cols
elif view_option == "Fixtures":
    display_cols = core_cols + fixture_cols
else:
    display_cols = core_cols + perf_cols

# Filter columns that exist in dataframe
display_cols = [col for col in display_cols if col in df.columns]

# Sort options
sort_col = st.selectbox(
    "Sort by",
    ["squad_pos", "total_points", "form", "cost", "player_rating", "player_rank"],
    index=0,
    format_func=lambda x: {
        "squad_pos": "Squad Position",
        "total_points": "Total Points",
        "form": "Form",
        "cost": "Cost",
        "player_rating": "Rating",
        "player_rank": "Rank"
    }.get(x, x)
)

ascending = sort_col in ["squad_pos", "player_rank", "cost"]
display_df = df.sort_values(sort_col, ascending=ascending)[display_cols].copy().reset_index(drop=True)
display_df = display_df.rename(columns=column_rename)

# Calculate height to fit all rows
table_height = (len(display_df) + 1) * 35 + 3

st.subheader(f"Team Players ({view_option})")
st.dataframe(
    style_alternating_rows(display_df),
    width="stretch",
    hide_index=True,
    height=table_height,
    column_config={
        "Pts": st.column_config.NumberColumn("Pts", format="%d"),
        "GW": st.column_config.NumberColumn("GW", format="%d"),
        "Mins": st.column_config.NumberColumn("Mins", format="%d"),
        "Rank": st.column_config.NumberColumn("Rank", format="%d"),
        "Sel%": st.column_config.NumberColumn("Sel%", format="%d"),
        "Cost": st.column_config.NumberColumn("Cost", format="%.1f"),
        "Form": st.column_config.NumberColumn("Form", format="%.1f"),
        "PPG": st.column_config.NumberColumn("PPG", format="%.1f"),
        "Pts/£": st.column_config.NumberColumn("Pts/£", format="%.2f"),
        "Pts/£ L3": st.column_config.NumberColumn("Pts/£ L3", format="%.2f"),
        "ICT": st.column_config.NumberColumn("ICT", format="%.1f"),
        "Infl": st.column_config.NumberColumn("Infl", format="%.1f"),
        "Creat": st.column_config.NumberColumn("Creat", format="%.1f"),
        "Threat": st.column_config.NumberColumn("Threat", format="%.1f"),
        "Rating": st.column_config.NumberColumn("Rating", format="%.1f"),
        "Min/90": st.column_config.NumberColumn("Min/90", format="%.1f"),
        "Diff3": st.column_config.NumberColumn("Diff3", format="%.1f"),
        "Diff1": st.column_config.NumberColumn("Diff1", format="%d"),
        "Diff2": st.column_config.NumberColumn("Diff2", format="%d"),
        "Diff4": st.column_config.NumberColumn("Diff4", format="%d"),
        "Diff5": st.column_config.NumberColumn("Diff5", format="%d"),
        "Diff6": st.column_config.NumberColumn("Diff6", format="%d"),
    }
)

# Position breakdown
st.divider()
st.subheader("Position Analysis")

pos_stats = df.groupby("pos_type").agg({
    "total_points": "sum",
    "cost": "sum",
    "player_rating": "mean",
    "form": "mean",
}).round(2)

pos_stats = pos_stats.rename(columns={
    "total_points": "Total Pts",
    "cost": "Value",
    "player_rating": "Avg Rating",
    "form": "Avg Form"
})

# Reorder positions
pos_order = ["GK", "DEF", "MID", "FWD"]
pos_stats = pos_stats.reindex([p for p in pos_order if p in pos_stats.index])

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Points by Position**")
    st.dataframe(
        pos_stats[["Total Pts", "Value"]],
        width="stretch"
    )

with col2:
    st.markdown("**Ratings by Position**")
    st.dataframe(
        pos_stats[["Avg Rating", "Avg Form"]],
        width="stretch"
    )

# Players needing attention
st.divider()
st.subheader("Players to Watch")

# Low form players (form < 4)
low_form = df[df["form"] < 4][["name", "pos_type", "club", "form", "total_points", "player_rating"]].copy()
if not low_form.empty:
    with st.expander(f"Low Form Players ({len(low_form)})", expanded=False):
        low_form = low_form.rename(columns={
            "name": "Player",
            "pos_type": "Pos",
            "club": "Club",
            "form": "Form",
            "total_points": "Total Pts",
            "player_rating": "Rating"
        })
        st.dataframe(style_alternating_rows(low_form.reset_index(drop=True)), width="stretch", hide_index=True)

# Low minutes players (min_per_90 < 70)
low_mins = df[df["min_per_90"] < 70][["name", "pos_type", "club", "min_per_90", "minutes", "selection_likelihood"]].copy()
if not low_mins.empty:
    with st.expander(f"Low Minutes Players ({len(low_mins)})", expanded=False):
        low_mins = low_mins.rename(columns={
            "name": "Player",
            "pos_type": "Pos",
            "club": "Club",
            "min_per_90": "Min/90",
            "minutes": "Total Mins",
            "selection_likelihood": "Sel%"
        })
        st.dataframe(style_alternating_rows(low_mins.reset_index(drop=True)), width="stretch", hide_index=True)

# Tough fixtures ahead (diff_next_3 > 10)
tough_fixtures = df[df["diff_next_3"] > 10][["name", "pos_type", "club", "diff_next_3", "fix_1", "fix_2", "fix_3"]].copy()
if not tough_fixtures.empty:
    with st.expander(f"Tough Fixtures Ahead ({len(tough_fixtures)})", expanded=False):
        tough_fixtures = tough_fixtures.rename(columns={
            "name": "Player",
            "pos_type": "Pos",
            "club": "Club",
            "diff_next_3": "Diff3",
            "fix_1": "GW+1",
            "fix_2": "GW+2",
            "fix_3": "GW+3"
        })
        st.dataframe(style_alternating_rows(tough_fixtures.reset_index(drop=True)), width="stretch", hide_index=True)

# Player news
news_players = df[df["news"] != ""][["name", "pos_type", "club", "status", "news", "chance_next"]].copy()
if not news_players.empty:
    with st.expander(f"Player News ({len(news_players)})", expanded=True):
        news_players["Status"] = news_players["status"].apply(get_status_emoji)
        news_players = news_players[["name", "pos_type", "club", "Status", "news", "chance_next"]]
        news_players = news_players.rename(columns={
            "name": "Player",
            "pos_type": "Pos",
            "club": "Club",
            "news": "News",
            "chance_next": "Chance %"
        })
        st.dataframe(style_alternating_rows(news_players.reset_index(drop=True)), width="stretch", hide_index=True)
