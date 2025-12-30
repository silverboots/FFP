from sqlalchemy.dialects.sqlite import insert
from sqlalchemy import delete
from sqlalchemy.orm import Session

from database.models import Team, Player
from database.db import engine, Base

from itertools import islice

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
        # 1) Upsert (INSERT or UPDATE)
        if rows:
            stmt = insert(Team).values(rows)
            stmt = stmt.on_conflict_do_update(
                index_elements=[Team.team_id],
                set_={c.name: getattr(stmt.excluded, c.name) for c in Team.__table__.columns if c.name != "team_id"},
            )
            session.execute(stmt)

        # 2) Delete rows not in API
        if ids:
            session.execute(
                delete(Team).where(Team.team_id.not_in(ids))
            )
        else:
            # API returned empty list → delete all teams
            session.execute(delete(Team))


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
        # 1) Chunked upsert
        for batch in chunked(rows, 25):  # safe batch size for SQLite
            stmt = insert(Player).values(batch)
            stmt = stmt.on_conflict_do_update(
                index_elements=[Player.player_id],
                set_={
                    c.name: getattr(stmt.excluded, c.name)
                    for c in Player.__table__.columns
                    if c.name != "player_id"
                },
            )
            session.execute(stmt)

        # 2) Delete players not in API
        if ids:
            session.execute(delete(Player).where(Player.player_id.not_in(ids)))
        else:
            session.execute(delete(Player))
