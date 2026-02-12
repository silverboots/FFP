import streamlit as st

from auth.session_manager import get_cookie_manager, check_auth
from database.lookup_helpers import get_all_player_news

from streamlit_helpers.common_modules import style_alternating_rows

import pandas as pd

st.set_page_config(page_title="Player News", page_icon="📰", layout="wide")

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

st.title("Player News & Availability")


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


def get_status_label(status):
    """Return label for player status."""
    status_map = {
        "a": "Available",
        "d": "Doubtful",
        "i": "Injured",
        "s": "Suspended",
        "u": "Unknown",
        "n": "Not Available",
    }
    return status_map.get(status, "Unknown")


# Get all player news
news_data = get_all_player_news()

if not news_data:
    st.info("No player news available at this time.")
    st.stop()

# Convert to DataFrame
df = pd.DataFrame(news_data)

# Add formatted columns
df["Status"] = df["status"].apply(get_status_emoji)
df["Status Label"] = df["status"].apply(get_status_label)

# Summary stats
col1, col2, col3, col4 = st.columns(4)
with col1:
    injured = len(df[df["status"] == "i"])
    st.metric("Injured", injured)
with col2:
    suspended = len(df[df["status"] == "s"])
    st.metric("Suspended", suspended)
with col3:
    doubtful = len(df[df["status"] == "d"])
    st.metric("Doubtful", doubtful)
with col4:
    total = len(df)
    st.metric("Total with News", total)

st.divider()

# Filter options
filter_col1, filter_col2 = st.columns(2)
with filter_col1:
    status_filter = st.multiselect(
        "Filter by Status",
        options=["Injured", "Suspended", "Doubtful", "Not Available", "Unknown", "Available"],
        default=["Injured", "Suspended", "Doubtful", "Not Available"]
    )
with filter_col2:
    position_filter = st.multiselect(
        "Filter by Position",
        options=["GK", "DEF", "MID", "FWD"],
        default=["GK", "DEF", "MID", "FWD"]
    )

# Apply filters
status_label_map = {
    "Injured": "i", "Suspended": "s", "Doubtful": "d",
    "Not Available": "n", "Unknown": "u", "Available": "a"
}
selected_statuses = [status_label_map[s] for s in status_filter]

filtered_df = df[
    (df["status"].isin(selected_statuses)) &
    (df["position"].isin(position_filter))
]

# Display columns
display_cols = ["Status", "name", "club", "position", "Status Label", "chance_next", "news", "cost", "selected_by", "total_points"]

# Rename columns for display
column_rename = {
    "name": "Player",
    "club": "Club",
    "position": "Pos",
    "Status Label": "Status Type",
    "chance_next": "Chance %",
    "news": "News",
    "cost": "Cost",
    "selected_by": "Sel%",
    "total_points": "Pts",
}

display_df = filtered_df[display_cols].copy().reset_index(drop=True)
display_df = display_df.rename(columns=column_rename)

st.subheader(f"Player News ({len(display_df)} players)")

# Calculate height to fit all rows (35px per row + header)
table_height = (len(display_df) + 1) * 35 + 3

st.dataframe(
    style_alternating_rows(display_df),
    width="stretch",
    hide_index=True,
    height=table_height,
    column_config={
        "Chance %": st.column_config.NumberColumn("Chance %", format="%d"),
        "Cost": st.column_config.NumberColumn("Cost", format="%.1f"),
        "Sel%": st.column_config.NumberColumn("Sel%", format="%.1f"),
        "Pts": st.column_config.NumberColumn("Pts", format="%d"),
    }
)
