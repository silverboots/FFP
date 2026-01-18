from database.db import SessionLocal
from database.models import User, UserPlayers, Player, PlayerMetric, Team, TeamMetric, PlayerUpcomingFixture, PlayerPastFixture
from sqlalchemy import text, select


def get_current_gameweek():
    with SessionLocal() as db:
        result = db.execute(
            text("SELECT MAX(round) AS game_week FROM PlayerPastFixtures")
        )

        gameweek = result.scalar_one_or_none()
        return gameweek


def get_user_team_id(user_email: str) -> int | None:
    """Get the FPL team ID for a user by email."""
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == user_email))
        return user.team_id if user else None


def get_user_team(user_email: str) -> list[dict] | None:
    """
    Retrieve the logged-in user's fantasy team with full player stats and next 6 fixtures.

    Returns list of player dicts sorted by squad position, or None if no team found.
    """
    with SessionLocal() as db:
        # Get user's team_id
        user = db.scalar(select(User).where(User.email == user_email))
        if not user:
            return None

        # Get all user's players
        user_players = db.execute(
            select(UserPlayers).where(UserPlayers.user_team_id == user.team_id)
        ).scalars().all()

        if not user_players:
            return None

        # Build team lookup for names
        teams = {t.team_id: t for t in db.execute(select(Team)).scalars().all()}
        team_metrics = {tm.team_id: tm for tm in db.execute(select(TeamMetric)).scalars().all()}

        result = []
        for up in user_players:
            # Get player data
            player = db.scalar(select(Player).where(Player.player_id == up.element))
            if not player:
                continue

            # Get player metrics
            metric = db.scalar(select(PlayerMetric).where(PlayerMetric.player_id == up.element))

            # Get player's club
            club = teams.get(player.team)
            club_name = club.short_name if club else "???"

            # Position type mapping
            pos_map = {1: "GK", 2: "DEF", 3: "MID", 4: "FWD"}

            # Build player dict
            player_data = {
                # Core info
                "squad_pos": up.position,
                "player_id": player.player_id,
                "pos_type": pos_map.get(up.element_type, "???"),
                "name": player.web_name,
                "full_name": f"{player.first_name} {player.second_name}",
                "club": club_name,
                "is_captain": up.is_captain,
                "is_vice_captain": up.is_vice_captain,
                "multiplier": up.multiplier,
                "status": player.status,
                "chance_next": player.chance_of_playing_next_round,
                "news": player.news,

                # Performance
                "total_points": player.total_points,
                "event_points": player.event_points,
                "form": player.form,
                "ppg": player.points_per_game,
                "minutes": player.minutes,

                # Value
                "cost": player.now_cost / 10,  # Convert to millions
                "value_form": player.value_form,
                "value_season": player.value_season,

                # Advanced stats
                "ict_index": player.ict_index,
                "influence": player.influence,
                "creativity": player.creativity,
                "threat": player.threat,
            }

            # Add metrics if available
            if metric:
                player_data.update({
                    "pts_per_pound": metric.total_points_per_pound,
                    "pts_per_pound_l3": metric.points_per_pound_last_3_games,
                    "min_per_90": metric.min_per_90,
                    "early_sub": metric.early_sub,
                    "selection_likelihood": metric.selection_likelihood,
                    "diff_next_3": metric.team_difficulty_next_3,
                    "player_rating": metric.player_rating,
                    "player_rank": metric.position_rank,
                })
            else:
                player_data.update({
                    "pts_per_pound": 0.0,
                    "pts_per_pound_l3": 0.0,
                    "min_per_90": 0.0,
                    "early_sub": False,
                    "selection_likelihood": 0,
                    "diff_next_3": 0.0,
                    "player_rating": 0.0,
                    "player_rank": 0,
                })

            # Get next 6 fixtures
            upcoming = db.execute(
                select(PlayerUpcomingFixture)
                .where(PlayerUpcomingFixture.player_id == up.element)
                .where(PlayerUpcomingFixture.finished == False)
                .order_by(PlayerUpcomingFixture.event)
                .limit(6)
            ).scalars().all()

            fixtures = []
            for i, fix in enumerate(upcoming):
                # Determine opponent team
                if fix.is_home:
                    opp_team_id = fix.team_a
                    venue = "H"
                else:
                    opp_team_id = fix.team_h
                    venue = "A"

                opp_team = teams.get(opp_team_id)
                opp_name = opp_team.short_name if opp_team else "???"
                opp_metric = team_metrics.get(opp_team_id)

                # Get appropriate strength metrics based on venue
                # If we're home, opponent is away - use their away attack/defence
                # If we're away, opponent is home - use their home attack/defence
                if opp_metric:
                    if fix.is_home:
                        opp_attack = opp_metric.away_strength_attack
                        opp_defence = opp_metric.away_strength_defence
                    else:
                        opp_attack = opp_metric.home_strength_attack
                        opp_defence = opp_metric.home_strength_defence
                else:
                    opp_attack = 0.0
                    opp_defence = 0.0

                fixtures.append({
                    "opponent": f"{opp_name} ({venue})",
                    "difficulty": fix.difficulty,
                    "opp_attack": opp_attack,
                    "opp_defence": opp_defence,
                    "event": fix.event,
                })

            # Pad to 6 fixtures if fewer available
            while len(fixtures) < 6:
                fixtures.append({
                    "opponent": "-",
                    "difficulty": 0,
                    "opp_attack": 0.0,
                    "opp_defence": 0.0,
                    "event": 0,
                })

            for i, fix in enumerate(fixtures):
                player_data[f"fix_{i+1}"] = fix["opponent"]
                player_data[f"fix_{i+1}_diff"] = fix["difficulty"]
                player_data[f"fix_{i+1}_atk"] = fix["opp_attack"]
                player_data[f"fix_{i+1}_def"] = fix["opp_defence"]

            result.append(player_data)

        # Sort by squad position
        result.sort(key=lambda x: x["squad_pos"])
        return result


def get_all_player_news() -> list[dict]:
    """
    Retrieve all players with news/availability updates.

    Returns list of player dicts with news info, sorted by status severity then name.
    """
    with SessionLocal() as db:
        # Get all players with news
        players = db.execute(
            select(Player).where(Player.news != "")
        ).scalars().all()

        # Build team lookup for names
        teams = {t.team_id: t for t in db.execute(select(Team)).scalars().all()}

        # Position type mapping
        pos_map = {1: "GK", 2: "DEF", 3: "MID", 4: "FWD"}

        # Status priority for sorting (lower = more severe)
        status_priority = {"i": 0, "s": 1, "n": 2, "d": 3, "u": 4, "a": 5}

        result = []
        for player in players:
            club = teams.get(player.team)
            club_name = club.short_name if club else "???"

            result.append({
                "name": player.web_name,
                "full_name": f"{player.first_name} {player.second_name}",
                "club": club_name,
                "position": pos_map.get(player.element_type, "???"),
                "status": player.status,
                "chance_next": player.chance_of_playing_next_round,
                "chance_this": player.chance_of_playing_this_round,
                "news": player.news,
                "news_added": player.news_added,
                "cost": player.now_cost / 10,
                "selected_by": player.selected_by_percent,
                "total_points": player.total_points,
            })

        # Sort by status severity, then by name
        result.sort(key=lambda x: (status_priority.get(x["status"], 5), x["name"]))
        return result


def get_all_teams() -> list[dict]:
    """Get all teams for filter dropdown."""
    with SessionLocal() as db:
        teams = db.execute(select(Team).order_by(Team.name)).scalars().all()
        return [{"team_id": t.team_id, "name": t.name, "short_name": t.short_name} for t in teams]


def get_user_team_player_ids(user_email: str, position: int | None = None) -> list[int]:
    """
    Get player IDs from user's fantasy team, optionally filtered by position.

    Args:
        user_email: User's email
        position: element_type (1=GK, 2=DEF, 3=MID, 4=FWD) or None for all

    Returns list of player IDs.
    """
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == user_email))
        if not user:
            return []

        user_players = db.execute(
            select(UserPlayers).where(UserPlayers.user_team_id == user.team_id)
        ).scalars().all()

        if not user_players:
            return []

        if position is None:
            return [up.element for up in user_players]

        # Filter by position
        return [up.element for up in user_players if up.element_type == position]


def search_players(
    positions: list[int] | None = None,
    team_ids: list[int] | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search players with optional filters.

    Args:
        positions: List of element_type values (1=GK, 2=DEF, 3=MID, 4=FWD)
        team_ids: List of team IDs to filter by
        min_price: Minimum price in millions
        max_price: Maximum price in millions

    Returns list of player dicts sorted by position_rank.
    """
    with SessionLocal() as db:
        # Build query with filters
        query = select(Player)

        if positions:
            query = query.where(Player.element_type.in_(positions))
        if team_ids:
            query = query.where(Player.team.in_(team_ids))
        if min_price is not None:
            query = query.where(Player.now_cost >= min_price * 10)
        if max_price is not None:
            query = query.where(Player.now_cost <= max_price * 10)

        players = db.execute(query).scalars().all()

        # Build team lookup
        teams = {t.team_id: t for t in db.execute(select(Team)).scalars().all()}

        # Build metrics lookup
        metrics = {m.player_id: m for m in db.execute(select(PlayerMetric)).scalars().all()}

        # Position type mapping
        pos_map = {1: "GK", 2: "DEF", 3: "MID", 4: "FWD"}

        result = []
        for player in players:
            club = teams.get(player.team)
            metric = metrics.get(player.player_id)

            player_data = {
                "player_id": player.player_id,
                "name": player.web_name,
                "full_name": f"{player.first_name} {player.second_name}",
                "club": club.short_name if club else "???",
                "position": pos_map.get(player.element_type, "???"),
                "element_type": player.element_type,
                "cost": player.now_cost / 10,
                "form": player.form,
                "total_points": player.total_points,
                "event_points": player.event_points,
                "ppg": player.points_per_game,
                "ict_index": player.ict_index,
                "influence": player.influence,
                "creativity": player.creativity,
                "threat": player.threat,
                "selected_by": player.selected_by_percent,
                "minutes": player.minutes,
                "starts": player.starts,
                "status": player.status,
            }

            # Add metrics if available
            if metric:
                player_data.update({
                    "position_rank": metric.position_rank,
                    "player_rating": metric.player_rating,
                    "diff_next_3": metric.team_difficulty_next_3,
                    "min_per_90": metric.min_per_90,
                })
            else:
                player_data.update({
                    "position_rank": 9999,
                    "player_rating": 0.0,
                    "diff_next_3": 0.0,
                    "min_per_90": 0.0,
                })

            result.append(player_data)

        # Sort by position_rank (lowest = best)
        result.sort(key=lambda x: x["position_rank"])
        return result



def get_player_details(player_ids: list[int]) -> list[dict]:
    """
    Get comprehensive player data including all stats from Player, PlayerMetrics,
    TeamMetrics, and next 6 fixtures with opponent team metrics.

    Args:
        player_ids: List of player IDs to fetch

    Returns list of player dicts with full details.
    """
    if not player_ids:
        return []

    with SessionLocal() as db:
        players = db.execute(
            select(Player).where(Player.player_id.in_(player_ids))
        ).scalars().all()

        # Build lookups
        teams = {t.team_id: t for t in db.execute(select(Team)).scalars().all()}
        team_metrics = {tm.team_id: tm for tm in db.execute(select(TeamMetric)).scalars().all()}
        metrics = {m.player_id: m for m in db.execute(select(PlayerMetric)).scalars().all()}

        # Position type mapping
        pos_map = {1: "GK", 2: "DEF", 3: "MID", 4: "FWD"}

        result = []
        for player in players:
            club = teams.get(player.team)
            club_metric = team_metrics.get(player.team)
            metric = metrics.get(player.player_id)

            player_data = {
                # Core info
                "player_id": player.player_id,
                "name": player.web_name,
                "full_name": f"{player.first_name} {player.second_name}",
                "club": club.short_name if club else "???",
                "club_name": club.name if club else "???",
                "position": pos_map.get(player.element_type, "???"),
                "element_type": player.element_type,
                "status": player.status,
                "news": player.news,
                "news_added": player.news_added,
                "chance_next": player.chance_of_playing_next_round,
                "chance_this": player.chance_of_playing_this_round,

                # Value
                "cost": player.now_cost / 10,
                "cost_change_event": player.cost_change_event,
                "cost_change_start": player.cost_change_start,
                "value_form": player.value_form,
                "value_season": player.value_season,

                # Points & Form
                "total_points": player.total_points,
                "event_points": player.event_points,
                "form": player.form,
                "ppg": player.points_per_game,
                "ep_next": player.ep_next,
                "ep_this": player.ep_this,

                # Playing time
                "minutes": player.minutes,
                "starts": player.starts,

                # Goals & Assists
                "goals_scored": player.goals_scored,
                "assists": player.assists,
                "expected_goals": player.expected_goals,
                "expected_assists": player.expected_assists,
                "expected_goal_involvements": player.expected_goal_involvements,

                # Defense
                "clean_sheets": player.clean_sheets,
                "goals_conceded": player.goals_conceded,
                "expected_goals_conceded": player.expected_goals_conceded,
                "own_goals": player.own_goals,

                # GK specific
                "saves": player.saves,
                "penalties_saved": player.penalties_saved,
                "penalties_missed": player.penalties_missed,

                # Cards
                "yellow_cards": player.yellow_cards,
                "red_cards": player.red_cards,

                # Bonus
                "bonus": player.bonus,
                "bps": player.bps,

                # ICT
                "ict_index": player.ict_index,
                "influence": player.influence,
                "creativity": player.creativity,
                "threat": player.threat,

                # ICT Ranks
                "ict_index_rank": player.ict_index_rank,
                "ict_index_rank_type": player.ict_index_rank_type,
                "influence_rank": player.influence_rank,
                "influence_rank_type": player.influence_rank_type,
                "creativity_rank": player.creativity_rank,
                "creativity_rank_type": player.creativity_rank_type,
                "threat_rank": player.threat_rank,
                "threat_rank_type": player.threat_rank_type,

                # Defensive stats
                "clearances_blocks_interceptions": player.clearances_blocks_interceptions,
                "recoveries": player.recoveries,
                "tackles": player.tackles,
                "defensive_contribution": player.defensive_contribution,

                # Per 90 stats
                "expected_goals_per_90": player.expected_goals_per_90,
                "expected_assists_per_90": player.expected_assists_per_90,
                "expected_goal_involvements_per_90": player.expected_goal_involvements_per_90,
                "expected_goals_conceded_per_90": player.expected_goals_conceded_per_90,
                "goals_conceded_per_90": player.goals_conceded_per_90,
                "saves_per_90": player.saves_per_90,
                "starts_per_90": player.starts_per_90,
                "clean_sheets_per_90": player.clean_sheets_per_90,
                "defensive_contribution_per_90": player.defensive_contribution_per_90,

                # Transfer activity
                "selected_by": player.selected_by_percent,
                "transfers_in": player.transfers_in,
                "transfers_in_event": player.transfers_in_event,
                "transfers_out": player.transfers_out,
                "transfers_out_event": player.transfers_out_event,

                # Rankings
                "now_cost_rank": player.now_cost_rank,
                "now_cost_rank_type": player.now_cost_rank_type,
                "form_rank": player.form_rank,
                "form_rank_type": player.form_rank_type,
                "ppg_rank": player.points_per_game_rank,
                "ppg_rank_type": player.points_per_game_rank_type,
                "selected_rank": player.selected_rank,
                "selected_rank_type": player.selected_rank_type,

                # Set pieces
                "corners_order": player.corners_and_indirect_freekicks_order,
                "corners_text": player.corners_and_indirect_freekicks_text,
                "direct_fk_order": player.direct_freekicks_order,
                "direct_fk_text": player.direct_freekicks_text,
                "penalties_order": player.penalties_order,
                "penalties_text": player.penalties_text,

                # Other
                "dreamteam_count": player.dreamteam_count,
                "in_dreamteam": player.in_dreamteam,
            }

            # Add player's team metrics
            if club_metric:
                player_data.update({
                    "team_home_attack": club_metric.home_strength_attack,
                    "team_home_defence": club_metric.home_strength_defence,
                    "team_away_attack": club_metric.away_strength_attack,
                    "team_away_defence": club_metric.away_strength_defence,
                    "team_games_h": club_metric.no_games_h,
                    "team_goals_scored_h": club_metric.no_goals_scored_h,
                    "team_goals_conceded_h": club_metric.no_goals_conceded_h,
                    "team_games_a": club_metric.no_games_a,
                    "team_goals_scored_a": club_metric.no_goals_scored_a,
                    "team_goals_conceded_a": club_metric.no_goals_conceded_a,
                })
            else:
                player_data.update({
                    "team_home_attack": 0.0,
                    "team_home_defence": 0.0,
                    "team_away_attack": 0.0,
                    "team_away_defence": 0.0,
                    "team_games_h": 0,
                    "team_goals_scored_h": 0,
                    "team_goals_conceded_h": 0,
                    "team_games_a": 0,
                    "team_goals_scored_a": 0,
                    "team_goals_conceded_a": 0,
                })

            # Add player metrics
            if metric:
                player_data.update({
                    "pts_per_pound": metric.total_points_per_pound,
                    "pts_per_pound_l3": metric.points_per_pound_last_3_games,
                    "pts_last_3": metric.points_last_3_games,
                    "min_per_90": metric.min_per_90,
                    "early_sub": metric.early_sub,
                    "selection_likelihood": metric.selection_likelihood,
                    "games_played_factor": metric.games_played_factor,
                    "diff_next_3": metric.team_difficulty_next_3,
                    "player_rating": metric.player_rating,
                    "player_rank": metric.player_rank,
                    "position_rank": metric.position_rank,
                })
            else:
                player_data.update({
                    "pts_per_pound": 0.0,
                    "pts_per_pound_l3": 0.0,
                    "pts_last_3": 0,
                    "min_per_90": 0.0,
                    "early_sub": False,
                    "selection_likelihood": 0,
                    "games_played_factor": 0.0,
                    "diff_next_3": 0.0,
                    "player_rating": 0.0,
                    "player_rank": 0,
                    "position_rank": 9999,
                })

            # Get next 6 fixtures with opponent team metrics
            upcoming = db.execute(
                select(PlayerUpcomingFixture)
                .where(PlayerUpcomingFixture.player_id == player.player_id)
                .where(PlayerUpcomingFixture.finished == False)
                .order_by(PlayerUpcomingFixture.event)
                .limit(6)
            ).scalars().all()

            fixtures = []
            for fix in upcoming:
                # Determine opponent team
                if fix.is_home:
                    opp_team_id = fix.team_a
                    venue = "H"
                else:
                    opp_team_id = fix.team_h
                    venue = "A"

                opp_team = teams.get(opp_team_id)
                opp_name = opp_team.short_name if opp_team else "???"
                opp_metric = team_metrics.get(opp_team_id)

                # Get opponent's strength metrics based on venue
                if opp_metric:
                    if fix.is_home:
                        # We're home, opponent is away
                        opp_attack = opp_metric.away_strength_attack
                        opp_defence = opp_metric.away_strength_defence
                        opp_games = opp_metric.no_games_a
                        opp_goals_scored = opp_metric.no_goals_scored_a
                        opp_goals_conceded = opp_metric.no_goals_conceded_a
                    else:
                        # We're away, opponent is home
                        opp_attack = opp_metric.home_strength_attack
                        opp_defence = opp_metric.home_strength_defence
                        opp_games = opp_metric.no_games_h
                        opp_goals_scored = opp_metric.no_goals_scored_h
                        opp_goals_conceded = opp_metric.no_goals_conceded_h
                else:
                    opp_attack = 0.0
                    opp_defence = 0.0
                    opp_games = 0
                    opp_goals_scored = 0
                    opp_goals_conceded = 0

                fixtures.append({
                    "opponent": f"{opp_name} ({venue})",
                    "opp_short": opp_name,
                    "venue": venue,
                    "difficulty": fix.difficulty,
                    "event": fix.event,
                    "opp_attack": opp_attack,
                    "opp_defence": opp_defence,
                    "opp_games": opp_games,
                    "opp_goals_scored": opp_goals_scored,
                    "opp_goals_conceded": opp_goals_conceded,
                })

            # Pad to 6 fixtures if fewer available
            while len(fixtures) < 6:
                fixtures.append({
                    "opponent": "-",
                    "opp_short": "-",
                    "venue": "-",
                    "difficulty": 0,
                    "event": 0,
                    "opp_attack": 0.0,
                    "opp_defence": 0.0,
                    "opp_games": 0,
                    "opp_goals_scored": 0,
                    "opp_goals_conceded": 0,
                })

            # Add fixtures to player data
            for i, fix in enumerate(fixtures):
                player_data[f"fix_{i+1}"] = fix["opponent"]
                player_data[f"fix_{i+1}_diff"] = fix["difficulty"]
                player_data[f"fix_{i+1}_event"] = fix["event"]
                player_data[f"fix_{i+1}_opp_atk"] = fix["opp_attack"]
                player_data[f"fix_{i+1}_opp_def"] = fix["opp_defence"]
                player_data[f"fix_{i+1}_opp_games"] = fix["opp_games"]
                player_data[f"fix_{i+1}_opp_scored"] = fix["opp_goals_scored"]
                player_data[f"fix_{i+1}_opp_conceded"] = fix["opp_goals_conceded"]

            # Get last 6 past fixtures
            past_fixtures = db.execute(
                select(PlayerPastFixture)
                .where(PlayerPastFixture.player_id == player.player_id)
                .order_by(PlayerPastFixture.round.desc())
                .limit(6)
            ).scalars().all()

            past_matches = []
            for pf in past_fixtures:
                opp_team = teams.get(pf.opponent_team)
                opp_name = opp_team.short_name if opp_team else "???"
                venue = "H" if pf.was_home else "A"

                past_matches.append({
                    "round": pf.round,
                    "opponent": f"{opp_name} ({venue})",
                    "minutes": pf.minutes or 0,
                    "points": pf.total_points or 0,
                    "goals": pf.goals_scored or 0,
                    "assists": pf.assists or 0,
                    "clean_sheets": pf.clean_sheets or 0,
                    "goals_conceded": pf.goals_conceded or 0,
                    "bonus": pf.bonus or 0,
                    "bps": pf.bps or 0,
                    "saves": pf.saves or 0,
                    "yellow_cards": pf.yellow_cards or 0,
                    "red_cards": pf.red_cards or 0,
                    "xG": pf.expected_goals or 0.0,
                    "xA": pf.expected_assists or 0.0,
                    "ict_index": pf.ict_index or 0.0,
                })

            # Pad to 6 past matches if fewer available
            while len(past_matches) < 6:
                past_matches.append({
                    "round": 0,
                    "opponent": "-",
                    "minutes": 0,
                    "points": 0,
                    "goals": 0,
                    "assists": 0,
                    "clean_sheets": 0,
                    "goals_conceded": 0,
                    "bonus": 0,
                    "bps": 0,
                    "saves": 0,
                    "yellow_cards": 0,
                    "red_cards": 0,
                    "xG": 0.0,
                    "xA": 0.0,
                    "ict_index": 0.0,
                })

            # Add past matches to player data
            for i, pm in enumerate(past_matches):
                player_data[f"past_{i+1}_round"] = pm["round"]
                player_data[f"past_{i+1}_opp"] = pm["opponent"]
                player_data[f"past_{i+1}_mins"] = pm["minutes"]
                player_data[f"past_{i+1}_pts"] = pm["points"]
                player_data[f"past_{i+1}_goals"] = pm["goals"]
                player_data[f"past_{i+1}_assists"] = pm["assists"]
                player_data[f"past_{i+1}_cs"] = pm["clean_sheets"]
                player_data[f"past_{i+1}_gc"] = pm["goals_conceded"]
                player_data[f"past_{i+1}_bonus"] = pm["bonus"]
                player_data[f"past_{i+1}_bps"] = pm["bps"]
                player_data[f"past_{i+1}_saves"] = pm["saves"]
                player_data[f"past_{i+1}_yc"] = pm["yellow_cards"]
                player_data[f"past_{i+1}_rc"] = pm["red_cards"]
                player_data[f"past_{i+1}_xG"] = pm["xG"]
                player_data[f"past_{i+1}_xA"] = pm["xA"]
                player_data[f"past_{i+1}_ict"] = pm["ict_index"]

            result.append(player_data)

        # Preserve order of player_ids
        result_dict = {p["player_id"]: p for p in result}
        return [result_dict[pid] for pid in player_ids if pid in result_dict]

