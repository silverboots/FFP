from sqlalchemy.dialects.sqlite import insert
from sqlalchemy import delete
from sqlalchemy.orm import Session
from datetime import datetime

from database.models import (
    Team,
    Player,
    PlayerPastFixture,
    PlayerUpcomingFixture,
    PlayerPastSeason,
    TeamMetric
)


from database.db import engine, Base

from itertools import islice


def parse_dt(value):
    if value is None:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def init_db():
    Base.metadata.create_all(bind=engine)

def sync_teams(session: Session, api_teams: list[dict]):
    print(f"sync teams : {len(api_teams)}")
    rows = [
        {
            "team_id": t["id"],
            "code": t["code"],
            "draw": t["draw"],
            "form": t["form"],
            "loss": t["loss"],
            "name": t["name"],
            "played": t["played"],
            "points": t["points"],
            "position": t["position"],
            "short_name": t["short_name"],
            "strength": t["strength"],
            "team_division": t["team_division"],
            "unavailable": t["unavailable"],
            "win": t["win"],
            "strength_overall_home": t["strength_overall_home"],
            "strength_overall_away": t["strength_overall_away"],
            "strength_attack_home": t["strength_attack_home"],
            "strength_attack_away": t["strength_attack_away"],
            "strength_defence_home": t["strength_defence_home"],
            "strength_defence_away": t["strength_defence_away"],
            "pulse_id": t["pulse_id"],
        }
        for t in api_teams
    ]
    ids = [t["id"] for t in api_teams]

    with session.begin():
        if rows:
            session.execute(delete(Team))
            session.execute(insert(Team).values(rows))


def chunked(iterable, size):
    it = iter(iterable)
    while chunk := list(islice(it, size)):
        yield chunk


def sync_players(session: Session, api_players: list[dict]):
    print(f"sync players : {len(api_players)}")

    rows = [
        {
            "player_id": p["id"],
            "can_transact": p["can_transact"],
            "can_select": p["can_select"],
            "chance_of_playing_next_round": p["chance_of_playing_next_round"],
            "chance_of_playing_this_round": p["chance_of_playing_this_round"],
            "code": p["code"],
            "cost_change_event": p["cost_change_event"],
            "cost_change_event_fall": p["cost_change_event_fall"],
            "cost_change_start": p["cost_change_start"],
            "cost_change_start_fall": p["cost_change_start_fall"],
            "dreamteam_count": p["dreamteam_count"],
            "element_type": p["element_type"],
            "ep_next": float(p["ep_next"]),
            "ep_this": float(p["ep_this"]),
            "event_points": p["event_points"],
            "first_name": p["first_name"],
            "form": float(p["form"]),
            "in_dreamteam": p["in_dreamteam"],
            "news": p["news"],
            "news_added": p["news_added"],
            "now_cost": p["now_cost"],
            "photo": p["photo"],
            "points_per_game": float(p["points_per_game"]),
            "removed": p["removed"],
            "second_name": p["second_name"],
            "selected_by_percent": float(p["selected_by_percent"]),
            "special": p["special"],
            "squad_number": p["squad_number"],
            "status": p["status"],
            "team": p["team"],
            "team_code": p["team_code"],
            "total_points": p["total_points"],
            "transfers_in": p["transfers_in"],
            "transfers_in_event": p["transfers_in_event"],
            "transfers_out": p["transfers_out"],
            "transfers_out_event": p["transfers_out_event"],
            "value_form": float(p["value_form"]),
            "value_season": float(p["value_season"]),
            "web_name": p["web_name"],
            "region": p["region"],
            "team_join_date": p["team_join_date"],
            "birth_date": p["birth_date"],
            "has_temporary_code": p["has_temporary_code"],
            "opta_code": p["opta_code"],
            "minutes": p["minutes"],
            "goals_scored": p["goals_scored"],
            "assists": p["assists"],
            "clean_sheets": p["clean_sheets"],
            "goals_conceded": p["goals_conceded"],
            "own_goals": p["own_goals"],
            "penalties_saved": p["penalties_saved"],
            "penalties_missed": p["penalties_missed"],
            "yellow_cards": p["yellow_cards"],
            "red_cards": p["red_cards"],
            "saves": p["saves"],
            "bonus": p["bonus"],
            "bps": p["bps"],
            "influence": float(p["influence"]),
            "creativity": float(p["creativity"]),
            "threat": float(p["threat"]),
            "ict_index": float(p["ict_index"]),
            "clearances_blocks_interceptions": p["clearances_blocks_interceptions"],
            "recoveries": p["recoveries"],
            "tackles": p["tackles"],
            "defensive_contribution": p["defensive_contribution"],
            "starts": p["starts"],
            "expected_goals": float(p["expected_goals"]),
            "expected_assists": float(p["expected_assists"]),
            "expected_goal_involvements": float(p["expected_goal_involvements"]),
            "expected_goals_conceded": float(p["expected_goals_conceded"]),
            "influence_rank": p["influence_rank"],
            "influence_rank_type": p["influence_rank_type"],
            "creativity_rank": p["creativity_rank"],
            "creativity_rank_type": p["creativity_rank_type"],
            "threat_rank": p["threat_rank"],
            "threat_rank_type": p["threat_rank_type"],
            "ict_index_rank": p["ict_index_rank"],
            "ict_index_rank_type": p["ict_index_rank_type"],
            "corners_and_indirect_freekicks_order": p["corners_and_indirect_freekicks_order"],
            "corners_and_indirect_freekicks_text": p["corners_and_indirect_freekicks_text"],
            "direct_freekicks_order": p["direct_freekicks_order"],
            "direct_freekicks_text": p["direct_freekicks_text"],
            "penalties_order": p["penalties_order"],
            "penalties_text": p["penalties_text"],
            "expected_goals_per_90": float(p["expected_goals_per_90"]),
            "saves_per_90": float(p["saves_per_90"]),
            "expected_assists_per_90": float(p["expected_assists_per_90"]),
            "expected_goal_involvements_per_90": float(p["expected_goal_involvements_per_90"]),
            "expected_goals_conceded_per_90": float(p["expected_goals_conceded_per_90"]),
            "goals_conceded_per_90": float(p["goals_conceded_per_90"]),
            "now_cost_rank": p["now_cost_rank"],
            "now_cost_rank_type": p["now_cost_rank_type"],
            "form_rank": p["form_rank"],
            "form_rank_type": p["form_rank_type"],
            "points_per_game_rank": p["points_per_game_rank"],
            "points_per_game_rank_type": p["points_per_game_rank_type"],
            "selected_rank": p["selected_rank"],
            "selected_rank_type": p["selected_rank_type"],
            "starts_per_90": float(p["starts_per_90"]),
            "clean_sheets_per_90": float(p["clean_sheets_per_90"]),
            "defensive_contribution_per_90": float(p["defensive_contribution_per_90"]),
        }
        for p in api_players
    ]

    ids = [p["id"] for p in api_players]

    with session.begin():
        if rows:
            session.execute(delete(Player))
            # 1) Chunked insert
            for batch in chunked(rows, 25):  # safe batch size for SQLite
                session.execute(insert(Player).values(batch))


def sync_player_past_fixtures(
    session: Session,
    api_fixtures: list[dict],
):
    print(f"sync player_past_fixtures : {len(api_fixtures)}")

    rows = [
        {
            "fixture_id": f["fixture"],
            "player_id": f["element"],
            "opponent_team": f["opponent_team"],
            "round": f["round"],
            "was_home": f["was_home"],
            "kickoff_time": parse_dt(f["kickoff_time"]),
            "team_h_score": f["team_h_score"],
            "team_a_score": f["team_a_score"],
            "total_points": f["total_points"],
            "minutes": f["minutes"],
            "goals_scored": f["goals_scored"],
            "assists": f["assists"],
            "clean_sheets": f["clean_sheets"],
            "goals_conceded": f["goals_conceded"],
            "own_goals": f["own_goals"],
            "penalties_saved": f["penalties_saved"],
            "penalties_missed": f["penalties_missed"],
            "yellow_cards": f["yellow_cards"],
            "red_cards": f["red_cards"],
            "saves": f["saves"],
            "bonus": f["bonus"],
            "bps": f["bps"],
            "influence": float(f["influence"]),
            "creativity": float(f["creativity"]),
            "threat": float(f["threat"]),
            "ict_index": float(f["ict_index"]),
            "clearances_blocks_interceptions": f["clearances_blocks_interceptions"],
            "recoveries": f["recoveries"],
            "tackles": f["tackles"],
            "defensive_contribution": f["defensive_contribution"],
            "starts": f["starts"],
            "expected_goals": float(f["expected_goals"]),
            "expected_assists": float(f["expected_assists"]),
            "expected_goal_involvements": float(f["expected_goal_involvements"]),
            "expected_goals_conceded": float(f["expected_goals_conceded"]),
            "value": f["value"],
            "transfers_balance": f["transfers_balance"],
            "selected": f["selected"],
            "transfers_in": f["transfers_in"],
            "transfers_out": f["transfers_out"],
            "modified": f["modified"],
        }
        for f in api_fixtures
    ]

    with session.begin():
        if rows:
            session.execute(
                delete(PlayerPastFixture)
            )
            # 1) Chunked insert
            for batch in chunked(rows, 100):  # safe batch size for SQLite
                session.execute(
                    insert(PlayerPastFixture).values(batch)
                )


def sync_player_upcoming_fixtures(
    session: Session,
    api_fixtures: list[dict],
):
    print(f"sync player_upcoming_fixtures : {len(api_fixtures)}")

    rows = [
        {
            "fixture_id": f["id"],
            "player_id": f["player_id"],
            "code": f["code"],
            "team_h": f["team_h"],
            "team_h_score": f["team_h_score"],
            "team_a": f["team_a"],
            "team_a_score": f["team_a_score"],
            "event": f["event"],
            "event_name": f["event_name"],
            "finished": f["finished"],
            "minutes": f["minutes"],
            "provisional_start_time": f["provisional_start_time"],
            "kickoff_time": parse_dt(f["kickoff_time"]),
            "is_home": f["is_home"],
            "difficulty": f["difficulty"],
        }
        for f in api_fixtures
    ]

    with session.begin():
        if rows:
            session.execute(
                delete(PlayerUpcomingFixture)
            )

            # 1) Chunked insert
            for batch in chunked(rows, 100):  # safe batch size for SQLite
                session.execute(
                    insert(PlayerUpcomingFixture).values(batch)
                )

def sync_player_past_seasons(
    session: Session,
    api_seasons: list[dict],
):
    print(f"sync player_past_seasons : {len(api_seasons)}")

    rows = [
        {
            "season_name": s["season_name"],
            "player_id": s["player_id"],
            "element_code": s["element_code"],
            "start_cost": s["start_cost"],
            "end_cost": s["end_cost"],
            "total_points": s["total_points"],
            "minutes": s["minutes"],
            "goals_scored": s["goals_scored"],
            "assists": s["assists"],
            "clean_sheets": s["clean_sheets"],
            "goals_conceded": s["goals_conceded"],
            "own_goals": s["own_goals"],
            "penalties_saved": s["penalties_saved"],
            "penalties_missed": s["penalties_missed"],
            "yellow_cards": s["yellow_cards"],
            "red_cards": s["red_cards"],
            "saves": s["saves"],
            "bonus": s["bonus"],
            "bps": s["bps"],
            "influence": float(s["influence"]),
            "creativity": float(s["creativity"]),
            "threat": float(s["threat"]),
            "ict_index": float(s["ict_index"]),
            "clearances_blocks_interceptions": s["clearances_blocks_interceptions"],
            "recoveries": s["recoveries"],
            "tackles": s["tackles"],
            "defensive_contribution": s["defensive_contribution"],
            "starts": s["starts"],
            "expected_goals": float(s["expected_goals"]),
            "expected_assists": float(s["expected_assists"]),
            "expected_goal_involvements": float(s["expected_goal_involvements"]),
            "expected_goals_conceded": float(s["expected_goals_conceded"]),
        }
        for s in api_seasons
    ]

    with session.begin():
        if rows:
            session.execute(
                delete(PlayerPastSeason)
            )

             # 1) Chunked insert
            for batch in chunked(rows, 100):  # safe batch size for SQLite
                session.execute(
                    insert(PlayerPastSeason).values(batch)
                )
def sync_team_metrics(
    session: Session,
    team_metrics: list[dict],
):
    print(f"sync team_metrics : {len(team_metrics)}")

    rows = [
        {
            "team_id": t["team_id"],

            "home_strength_attack": t.get("home_strength_attack"),
            "home_strength_defence": t.get("home_strength_defence"),
            "away_strength_attack": t.get("away_strength_attack"),
            "away_strength_defence": t.get("away_strength_defence"),

            "no_games_h": t["no_games_h"],
            "no_games_a": t["no_games_a"],
            "no_goals_scored_h": t["no_goals_scored_h"],
            "no_goals_conceded_h": t["no_goals_conceded_h"],
            "no_goals_scored_a": t["no_goals_scored_a"],
            "no_goals_conceded_a": t["no_goals_conceded_a"],
        }
        for t in team_metrics
    ]

    with session.begin():
        if rows:
            # wipe and reinsert (same approach as teams / players)
            session.execute(delete(TeamMetric))

            for batch in chunked(rows, 25):  # SQLite safe
                session.execute(
                    insert(TeamMetric).values(batch)
                )