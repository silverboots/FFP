import streamlit as st
st.set_page_config(page_title="Player Assessment", page_icon="🎯", layout="wide")

import pandas as pd
from auth.session_manager import get_cookie_manager, check_auth
from database.lookup_helpers import get_all_teams, search_players, get_player_details, get_user_team

# Cookie manager for session persistence
cookie_manager = get_cookie_manager()

# Check authentication
auth_status = check_auth(cookie_manager)

if auth_status is None:
    st.rerun()

if not auth_status:
    st.switch_page("Home.py")

# Initialize session state
if "comparison_players" not in st.session_state:
    st.session_state.comparison_players = []

if "selected_team_player" not in st.session_state:
    st.session_state.selected_team_player = None

# Get user email for team lookup
user_email = st.session_state.auth["user_email"]


def style_alternating_rows(df: pd.DataFrame):
    """Apply alternating row colors to a dataframe."""
    def highlight_rows(row):
        if row.name % 2 == 0:
            return ["background-color: #f8f9fa"] * len(row)
        return ["background-color: #ffffff"] * len(row)
    return df.style.apply(highlight_rows, axis=1)


def select_team_player(player_data: dict):
    """Select a team player for comparison."""
    st.session_state.selected_team_player = player_data
    st.session_state["price_range"] = (3.5, player_data["cost"])
    st.session_state.comparison_players = []  # Clear any added players when switching


def add_to_comparison(player_id: int):
    """Add a player to comparison list."""
    if player_id not in st.session_state.comparison_players:
        st.session_state.comparison_players.append(player_id)


def remove_from_comparison(player_id: int):
    """Remove a player from comparison list."""
    if player_id in st.session_state.comparison_players:
        st.session_state.comparison_players.remove(player_id)


# Page title
st.title("Player Exchange")

# Get user's team data
team_data = get_user_team(user_email)

if not team_data:
    st.warning("No team data found. Please ensure your team has been synced.")
    st.stop()

# Convert to DataFrame
team_df = pd.DataFrame(team_data)

# Section 1: Select player from your team
with st.expander("Select a Player from Your Team", expanded=True):
    st.caption("Choose a player to compare against other players in the same position")

    # Display team players with select buttons
    # Header row
    header_cols = st.columns([1, 3, 2, 1.5, 1.5, 1.5, 1.5, 1.5, 2])
    headers = ["Pos", "Player", "Club", "Cost", "Pts", "Form", "Rating", "Rank", ""]
    for col, header in zip(header_cols, headers):
        col.markdown(f"**{header}**")

    # Player rows
    for i, player in team_df.iterrows():
        cols = st.columns([1, 3, 2, 1.5, 1.5, 1.5, 1.5, 1.5, 2])

        cols[0].write(player["pos_type"])

        # Highlight if this is the selected player
        if st.session_state.selected_team_player and st.session_state.selected_team_player.get("name") == player["name"]:
            cols[1].markdown(f"**{player['name']}** ⭐")
        else:
            cols[1].write(player["name"])

        cols[2].write(player["club"])
        cols[3].write(f"£{player['cost']:.1f}m")
        cols[4].write(player["total_points"])
        cols[5].write(f"{player['form']:.1f}")
        cols[6].write(f"{player.get('player_rating', 0):.1f}")
        cols[7].write(player.get("player_rank", "-"))

        # Select button
        is_selected = (st.session_state.selected_team_player and
                       st.session_state.selected_team_player.get("name") == player["name"])

        if is_selected:
            cols[8].write("✓ Selected")
        else:
            # Build player data dict for selection
            player_dict = {
                "name": player["name"],
                "club": player["club"],
                "pos_type": player["pos_type"],
                "cost": player["cost"],
                "total_points": player["total_points"],
                "form": player["form"],
                "player_rating": player.get("player_rating", 0),
                "player_rank": player.get("player_rank", 0),
            }
            if cols[8].button("Select", key=f"select_{i}", type="secondary"):
                select_team_player(player_dict)
                st.rerun()

# Only show search and comparison if a team player is selected
if not st.session_state.selected_team_player:
    st.info("Select a player from your team above to search for comparisons.")
    st.stop()

# Get selected player details
selected_player = st.session_state.selected_team_player
pos_map = {"GK": 1, "DEF": 2, "MID": 3, "FWD": 4}
position_id = pos_map.get(selected_player["pos_type"], 3)

# Section 2: Search Players
with st.expander(f"Search {selected_player['pos_type']}s to Compare with {selected_player['name']}", expanded=True):
    # Load teams for filter
    teams_data = get_all_teams()
    team_options = {t["name"]: t["team_id"] for t in teams_data}

    # Filter controls - position is locked
    col1, col2 = st.columns(2)

    with col1:
        st.text_input(
            "Position",
            value=selected_player["pos_type"],
            disabled=True,
            help="Position is locked to the selected player's position"
        )

    with col2:
        selected_teams = st.multiselect(
            "Team",
            options=list(team_options.keys()),
            default=[],
            placeholder="All teams"
        )

    # Price inputs - default max to selected player's cost
    default_max = min(selected_player["cost"], 15.0)

    price_col1, price_col2 = st.columns(2)
    with price_col1:
        min_price = st.number_input(
            "Min Price (£m)",
            min_value=3.5,
            max_value=15.0,
            value=3.5,
            step=0.5,
            key="min_price"
        )

    with price_col2:
        max_price = st.number_input(
            "Max Price (£m)",
            min_value=3.5,
            max_value=15.0,
            value=default_max,
            step=0.5,
            key="max_price"
        )

    # Ensure min <= max
    if min_price > max_price:
        min_price, max_price = max_price, min_price

    # Convert selections to IDs
    team_ids = [team_options[t] for t in selected_teams] if selected_teams else None

    # Search players
    with st.spinner("Searching players..."):
        players = search_players(
            positions=[position_id],
            team_ids=team_ids,
            min_price=min_price,
            max_price=max_price
        )

    if not players:
        st.info("No players found matching your criteria.")
    else:
        st.markdown(f"**Search Results ({len(players)} players)**")

        # Limit to top 20 players
        display_players = players[:20]

        # Header row
        header_cols = st.columns([1, 3, 2, 1, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 2])
        headers = ["Rank", "Player", "Club", "Pos", "Cost", "Form", "Pts", "PPG", "ICT", "Rating", ""]
        for col, header in zip(header_cols, headers):
            col.markdown(f"**{header}**")

        # Player rows with add buttons
        for i, player in enumerate(display_players):
            cols = st.columns([1, 3, 2, 1, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 2])

            cols[0].write(player["position_rank"])
            cols[1].write(player["name"])
            cols[2].write(player["club"])
            cols[3].write(player["position"])
            cols[4].write(f"£{player['cost']:.1f}m")
            cols[5].write(f"{player['form']:.1f}")
            cols[6].write(player["total_points"])
            cols[7].write(f"{player['ppg']:.1f}")
            cols[8].write(f"{player['ict_index']:.1f}")
            cols[9].write(f"{player['player_rating']:.1f}")

            # Add button or already added indicator
            player_id = player["player_id"]
            if player_id in st.session_state.comparison_players:
                cols[10].write("✓ Added")
            else:
                if cols[10].button("Add", key=f"add_{player_id}", type="secondary"):
                    add_to_comparison(player_id)
                    st.rerun()

        if len(players) > 20:
            st.caption(f"Showing top 20 of {len(players)} players by position rank")

# Section 3: Comparison
with st.expander("Player Comparison", expanded=True):
    # Build comparison: selected team player + any added players
    if not st.session_state.comparison_players:
        st.info(f"Add players from the search results to compare with {selected_player['name']}.")
    else:
        # Get comparison data for added players
        comparison_data = get_player_details(st.session_state.comparison_players)

        if comparison_data:
            # Create comparison table with metrics as rows and players as columns
            metrics = [
                ("Cost", "cost", "£{:.1f}m", False),  # lower is better
                ("Position Rank", "position_rank", "{:d}", False),  # lower is better
                ("Difficulty Next 3", "diff_next_3", "{:.1f}", False),  # lower is better
                ("Pts/£ Last 3", "pts_per_pound_l3", "{:.2f}", True),  # higher is better
                ("Selection Likelihood", "selection_likelihood", "{:d}%", True),  # higher is better
                ("Total Points", "total_points", "{:d}", True),  # higher is better
                ("Form", "form", "{:.1f}", True),  # higher is better
                ("Minutes", "minutes", "{:d}", True),  # higher is better
                ("Mins/90", "min_per_90", "{:.1f}", True),  # higher is better
            ]

            # Get team player data for comparison (need to fetch from players list or team data)
            # Find the team player in the search results or use team_data
            team_player_for_comparison = None
            for p in team_data:
                if p["name"] == selected_player["name"]:
                    team_player_for_comparison = {
                        "player_id": -1,  # Placeholder
                        "name": p["name"],
                        "club": p["club"],
                        "cost": p["cost"],
                        "total_points": p["total_points"],
                        "form": p["form"],
                        "minutes": p.get("minutes", 0),
                        "position_rank": p.get("player_rank", 9999),
                        "diff_next_3": p.get("diff_next_3", 0),
                        "pts_per_pound_l3": p.get("pts_per_pound_l3", 0),
                        "selection_likelihood": p.get("selection_likelihood", 0),
                        "min_per_90": p.get("min_per_90", 0.0),
                    }
                    break

            # Combine team player with comparison players
            all_comparison = []
            if team_player_for_comparison:
                all_comparison.append(team_player_for_comparison)
            all_comparison.extend(comparison_data)

            # Build comparison dataframe with raw values for comparison
            comparison_rows = []
            raw_values = []
            player_cols = [f"{p['name']} ({p['club']})" for p in all_comparison]

            for metric_name, metric_key, fmt, higher_is_better in metrics:
                row = {"Metric": metric_name}
                row_raw = []
                for player in all_comparison:
                    value = player.get(metric_key, 0)
                    if value is None:
                        value = 0
                    row_raw.append(value)
                    try:
                        row[f"{player['name']} ({player['club']})"] = fmt.format(value)
                    except (ValueError, TypeError):
                        row[f"{player['name']} ({player['club']})"] = str(value)
                comparison_rows.append(row)
                raw_values.append((row_raw, higher_is_better))

            comparison_df = pd.DataFrame(comparison_rows)

            # Create styling function to highlight best values in green
            def highlight_comparison(df):
                styles = pd.DataFrame("", index=df.index, columns=df.columns)

                for row_idx, (row_raw, higher_is_better) in enumerate(raw_values):
                    if higher_is_better:
                        best_val = max(row_raw)
                    else:
                        best_val = min(row_raw)
                    for col_idx, val in enumerate(row_raw):
                        if val == best_val:
                            col_name = player_cols[col_idx]
                            styles.loc[row_idx, col_name] = "background-color: #d4edda"

                return styles

            styled_df = comparison_df.style.apply(lambda _: highlight_comparison(comparison_df), axis=None)

            # Mark team player column with star
            team_col_name = f"{selected_player['name']} ({selected_player['club']})"

            # Display comparison table
            st.dataframe(
                styled_df,
                width="stretch",
                hide_index=True,
                height=(len(metrics) + 1) * 35 + 3,
                column_config={
                    team_col_name: st.column_config.Column(label=f"⭐ {team_col_name}")
                }
            )

            st.caption("⭐ = Your team player | Green = Best value for metric")

            # Remove buttons for added players
            st.write("**Remove from comparison:**")
            cols = st.columns(len(comparison_data))
            for i, player in enumerate(comparison_data):
                with cols[i]:
                    if st.button(f"Remove {player['name']}", key=f"remove_{player['player_id']}"):
                        remove_from_comparison(player['player_id'])
                        st.rerun()

            # Clear all button
            if st.button("Clear All", type="secondary"):
                st.session_state.comparison_players = []
                st.rerun()
