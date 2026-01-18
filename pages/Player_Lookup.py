import streamlit as st
st.set_page_config(page_title="Player Lookup", page_icon="🔍", layout="wide")

import pandas as pd
from auth.session_manager import get_cookie_manager, check_auth
from database.lookup_helpers import get_all_teams, search_players, get_player_details

# Cookie manager for session persistence
cookie_manager = get_cookie_manager()

# Check authentication
auth_status = check_auth(cookie_manager)

if auth_status is None:
    st.rerun()

if not auth_status:
    st.switch_page("Home.py")

st.title("Player Lookup")

# Initialize session state for selected player
if "lookup_selected_player_id" not in st.session_state:
    st.session_state.lookup_selected_player_id = None


def select_player(player_id: int):
    """Select a player to view details."""
    st.session_state.lookup_selected_player_id = player_id


def clear_selection():
    """Clear selected player."""
    st.session_state.lookup_selected_player_id = None


# Get all teams for filter
all_teams = get_all_teams()
team_options = {t["name"]: t["team_id"] for t in all_teams}

# Search filters
st.subheader("Search Players")

col1, col2, col3, col4 = st.columns([2, 2, 1, 1])

with col1:
    position_filter = st.multiselect(
        "Position",
        options=["GK", "DEF", "MID", "FWD"],
        default=[]
    )
    position_map = {"GK": 1, "DEF": 2, "MID": 3, "FWD": 4}
    positions = [position_map[p] for p in position_filter] if position_filter else None

with col2:
    team_filter = st.multiselect(
        "Team",
        options=list(team_options.keys()),
        default=[]
    )
    team_ids = [team_options[t] for t in team_filter] if team_filter else None

with col3:
    min_price = st.number_input(
        "Min Price (£m)",
        min_value=3.5,
        max_value=15.0,
        value=3.5,
        step=0.5
    )

with col4:
    max_price = st.number_input(
        "Max Price (£m)",
        min_value=3.5,
        max_value=15.0,
        value=15.0,
        step=0.5
    )

# Ensure min <= max
if min_price > max_price:
    min_price, max_price = max_price, min_price

# Search for players
players = search_players(
    positions=positions,
    team_ids=team_ids,
    min_price=min_price,
    max_price=max_price
)

if not players:
    st.info("No players found with the selected filters.")
    st.stop()

# Check if we have a selected player
if st.session_state.lookup_selected_player_id is None:
    # Show player list with select buttons
    st.subheader(f"Players ({len(players)})")

    # Limit display to top 50 by position rank
    display_players = players[:50]

    # Header row
    header_cols = st.columns([1, 3, 2, 1, 1.5, 1.5, 1.5, 1.5, 1.5, 2])
    headers = ["Rank", "Player", "Club", "Pos", "Cost", "Pts", "Form", "PPG", "ICT", ""]
    for col, header in zip(header_cols, headers):
        col.markdown(f"**{header}**")

    # Player rows with select buttons
    for i, player in enumerate(display_players):
        cols = st.columns([1, 3, 2, 1, 1.5, 1.5, 1.5, 1.5, 1.5, 2])

        cols[0].write(player["position_rank"])
        cols[1].write(player["name"])
        cols[2].write(player["club"])
        cols[3].write(player["position"])
        cols[4].write(f"£{player['cost']:.1f}m")
        cols[5].write(player["total_points"])
        cols[6].write(f"{player['form']:.1f}")
        cols[7].write(f"{player['ppg']:.1f}")
        cols[8].write(f"{player['ict_index']:.1f}")

        if cols[9].button("Select", key=f"select_{player['player_id']}", type="secondary"):
            select_player(player["player_id"])
            st.rerun()

    if len(players) > 50:
        st.caption(f"Showing top 50 of {len(players)} players by position rank")

    st.stop()

# Get full player details for selected player
player_details = get_player_details([st.session_state.lookup_selected_player_id])

if not player_details:
    st.error("Could not load player details.")
    st.stop()

p = player_details[0]

# Back button
if st.button("← Back to Search Results", type="secondary"):
    clear_selection()
    st.rerun()

# Player header
st.divider()
col1, col2 = st.columns([2, 1])
with col1:
    st.header(f"{p['full_name']}")
    st.caption(f"{p['club_name']} | {p['position']}")
with col2:
    st.metric("Cost", f"£{p['cost']:.1f}m")
    if p["news"]:
        status_emoji = {"a": "✅", "d": "⚠️", "i": "🔴", "s": "🔴", "u": "❓", "n": "🚫"}.get(p["status"], "❓")
        st.warning(f"{status_emoji} {p['news']}")

# Summary metrics
st.subheader("Summary")
cols = st.columns(6)
with cols[0]:
    st.metric("Total Points", p["total_points"])
with cols[1]:
    st.metric("GW Points", p["event_points"])
with cols[2]:
    st.metric("Form", f"{p['form']:.1f}")
with cols[3]:
    st.metric("PPG", f"{p['ppg']:.1f}")
with cols[4]:
    st.metric("Rating", f"{p['player_rating']:.1f}")
with cols[5]:
    st.metric("Pos Rank", p["position_rank"])

st.divider()

# Tabs for different stat categories
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "Performance", "Value", "ICT Stats", "Team Metrics", "Last 6 Matches", "Fixtures", "All Stats"
])

with tab1:
    st.subheader("Performance Stats")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Playing Time**")
        st.write(f"Minutes: {p['minutes']}")
        st.write(f"Starts: {p['starts']}")
        st.write(f"Min/90: {p['min_per_90']:.1f}")
        st.write(f"Selection Likelihood: {p['selection_likelihood']}%")
        st.write(f"Early Sub: {'Yes' if p['early_sub'] else 'No'}")

        st.markdown("**Goals & Assists**")
        st.write(f"Goals: {p['goals_scored']}")
        st.write(f"Assists: {p['assists']}")
        st.write(f"xG: {p['expected_goals']:.2f}")
        st.write(f"xA: {p['expected_assists']:.2f}")
        st.write(f"xGI: {p['expected_goal_involvements']:.2f}")

    with col2:
        st.markdown("**Defense**")
        st.write(f"Clean Sheets: {p['clean_sheets']}")
        st.write(f"Goals Conceded: {p['goals_conceded']}")
        st.write(f"xGC: {p['expected_goals_conceded']:.2f}")
        st.write(f"Tackles: {p['tackles']}")
        st.write(f"Recoveries: {p['recoveries']}")

        st.markdown("**Bonus & Cards**")
        st.write(f"Bonus: {p['bonus']}")
        st.write(f"BPS: {p['bps']}")
        st.write(f"Yellow Cards: {p['yellow_cards']}")
        st.write(f"Red Cards: {p['red_cards']}")

with tab2:
    st.subheader("Value Analysis")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Price**")
        st.write(f"Current Cost: £{p['cost']:.1f}m")
        st.write(f"GW Price Change: £{p['cost_change_event'] / 10:.1f}m")
        st.write(f"Season Price Change: £{p['cost_change_start'] / 10:.1f}m")

        st.markdown("**Value Metrics**")
        st.write(f"Pts/£ (Season): {p['pts_per_pound']:.2f}")
        st.write(f"Pts/£ (Last 3): {p['pts_per_pound_l3']:.2f}")
        st.write(f"Value Form: {p['value_form']:.1f}")
        st.write(f"Value Season: {p['value_season']:.1f}")

    with col2:
        st.markdown("**Ownership**")
        st.write(f"Selected By: {p['selected_by']:.1f}%")
        st.write(f"Transfers In (GW): {p['transfers_in_event']:,}")
        st.write(f"Transfers Out (GW): {p['transfers_out_event']:,}")
        st.write(f"Net Transfers (GW): {p['transfers_in_event'] - p['transfers_out_event']:,}")

        st.markdown("**Expected Points**")
        st.write(f"EP This GW: {p['ep_this']:.1f}")
        st.write(f"EP Next GW: {p['ep_next']:.1f}")

with tab3:
    st.subheader("ICT Index")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**ICT Values**")
        st.write(f"ICT Index: {p['ict_index']:.1f}")
        st.write(f"Influence: {p['influence']:.1f}")
        st.write(f"Creativity: {p['creativity']:.1f}")
        st.write(f"Threat: {p['threat']:.1f}")

    with col2:
        st.markdown("**ICT Rankings (Overall / Position)**")
        st.write(f"ICT Rank: {p['ict_index_rank']} / {p['ict_index_rank_type']}")
        st.write(f"Influence Rank: {p['influence_rank']} / {p['influence_rank_type']}")
        st.write(f"Creativity Rank: {p['creativity_rank']} / {p['creativity_rank_type']}")
        st.write(f"Threat Rank: {p['threat_rank']} / {p['threat_rank_type']}")

with tab4:
    st.subheader("Team Metrics")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Team Strength (Normalized 0-1)**")
        st.write(f"Home Attack: {p['team_home_attack']:.2f}")
        st.write(f"Home Defence: {p['team_home_defence']:.2f}")
        st.write(f"Away Attack: {p['team_away_attack']:.2f}")
        st.write(f"Away Defence: {p['team_away_defence']:.2f}")

    with col2:
        st.markdown("**Recent Home Games (Last 3)**")
        st.write(f"Games: {p['team_games_h']}")
        st.write(f"Goals Scored: {p['team_goals_scored_h']}")
        st.write(f"Goals Conceded: {p['team_goals_conceded_h']}")

        st.markdown("**Recent Away Games (Last 3)**")
        st.write(f"Games: {p['team_games_a']}")
        st.write(f"Goals Scored: {p['team_goals_scored_a']}")
        st.write(f"Goals Conceded: {p['team_goals_conceded_a']}")

with tab5:
    st.subheader("Last 6 Matches")

    # Build past matches table
    past_match_data = []
    for i in range(1, 7):
        gw = p.get(f"past_{i}_round", 0)
        if gw and gw > 0:
            past_match_data.append({
                "GW": gw,
                "Opponent": p.get(f"past_{i}_opp", "-"),
                "Mins": p.get(f"past_{i}_mins", 0),
                "Pts": p.get(f"past_{i}_pts", 0),
                "G": p.get(f"past_{i}_goals", 0),
                "A": p.get(f"past_{i}_assists", 0),
                "CS": p.get(f"past_{i}_cs", 0),
                "GC": p.get(f"past_{i}_gc", 0),
                "Bonus": p.get(f"past_{i}_bonus", 0),
                "BPS": p.get(f"past_{i}_bps", 0),
                "xG": f"{p.get(f'past_{i}_xG', 0):.2f}",
                "xA": f"{p.get(f'past_{i}_xA', 0):.2f}",
                "ICT": f"{p.get(f'past_{i}_ict', 0):.1f}",
            })

    if past_match_data:
        past_df = pd.DataFrame(past_match_data)
        st.dataframe(past_df, hide_index=True, width="stretch")
    else:
        st.info("No past match data available for this player.")

with tab6:
    st.subheader("Upcoming Fixtures")
    st.write(f"Difficulty Next 3: {p['diff_next_3']:.1f}")

    # Build fixtures table
    fixture_data = []
    for i in range(1, 7):
        fixture_data.append({
            "GW": p[f"fix_{i}_event"] if p[f"fix_{i}_event"] > 0 else "-",
            "Opponent": p[f"fix_{i}"],
            "Difficulty": p[f"fix_{i}_diff"] if p[f"fix_{i}_diff"] > 0 else "-",
            "Opp Attack": f"{p[f'fix_{i}_opp_atk']:.2f}" if p[f"fix_{i}_opp_atk"] > 0 else "-",
            "Opp Defence": f"{p[f'fix_{i}_opp_def']:.2f}" if p[f"fix_{i}_opp_def"] > 0 else "-",
            "Opp Goals/Game": f"{p[f'fix_{i}_opp_scored'] / p[f'fix_{i}_opp_games']:.1f}" if p[f"fix_{i}_opp_games"] > 0 else "-",
            "Opp Conceded/Game": f"{p[f'fix_{i}_opp_conceded'] / p[f'fix_{i}_opp_games']:.1f}" if p[f"fix_{i}_opp_games"] > 0 else "-",
        })

    fixture_df = pd.DataFrame(fixture_data)
    st.dataframe(fixture_df, hide_index=True, width="stretch")

with tab7:
    st.subheader("All Stats")

    # Display all stats in a clean format
    stats_data = []
    for key, value in p.items():
        if not key.startswith("fix_"):
            if isinstance(value, float):
                stats_data.append({"Stat": key, "Value": f"{value:.2f}"})
            else:
                stats_data.append({"Stat": key, "Value": str(value)})

    stats_df = pd.DataFrame(stats_data)
    st.dataframe(stats_df, hide_index=True, height=600, width="stretch")