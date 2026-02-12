from fplapi.fpl_services import fetch_fpl_bootstrap, FPLError, fetch_fpl_player_summary, fetch_fpl_fixtures, fetch_fpl_team
from database.sync_helpers import (
    init_db, 
    sync_teams, 
    sync_players, 
    sync_player_past_fixtures, 
    sync_player_upcoming_fixtures, 
    sync_player_past_seasons,
    sync_team_metrics,
    sync_player_metrics,
    get_users,
    sync_user_players
)
from database.db import SessionLocal
from collections import defaultdict


"""
    This file represents the batch process for the FFP system.  
    - Data is collected from the FPL apis
    - Data is processed and calculated data derived
    - All data is saved to the database for use by the streamlit user web application
    - This batch should be run daily to keep the database up to date
"""
try:
    print("init database")
    init_db()

    print("get bootstrap data")
    data = fetch_fpl_bootstrap()

    if data is None:
        raise FPLError("No data returned by FPL API")

    if "teams" not in data:
        raise FPLError("No teams in FPL bootstrap data")

    if "elements" not in data:
        raise FPLError("No players (elements) in FPL bootstrap data")

    if "events" not in data:
        raise FPLError("No events in FPL bootstrap data")

    gameweek = 1
    for event in data["events"]:
        if event["can_manage"]:
            break
        gameweek = event["id"]
    
    print(f"Gameweek is : {gameweek}")

    print("get users")
    user_players = []
    with SessionLocal() as db:
        users = get_users(db)
        for i, user in enumerate(users):
            print(f"get user picks ({i+1}/{len(users)})")
            user_player_data = fetch_fpl_team(user.team_id, gameweek)
            for item in user_player_data["picks"]:
                item["user_team_id"] = user.team_id

            user_players.extend(user_player_data["picks"])

    print("get team fixture data to calculate strength home and away")
    team_metrics_lookup = {} # used for quick lookup in player calcs
    team_metrics_db = [] # stored in db
    fixture_data = fetch_fpl_fixtures()
    for i, fixture in enumerate(reversed(fixture_data)):
        print(f"calculate team metrics ({i+1}/{len(fixture_data)})")
        if not fixture["finished"]:
            continue
        
        if fixture["team_a"] not in team_metrics_lookup:
            team_metric = {
                "team_id": fixture["team_a"],
                "no_games_a": 1,
                "no_games_h": 0,
                "no_goals_scored_a": fixture["team_a_score"],
                "no_goals_conceded_a": fixture["team_h_score"],
                "no_goals_scored_h": 0,
                "no_goals_conceded_h": 0
            }

            team_metrics_lookup[fixture["team_a"]] = team_metric
        else:
            if team_metrics_lookup[fixture["team_a"]]["no_games_a"] < 3:
                team_metrics_lookup[fixture["team_a"]]["no_games_a"] += 1
                team_metrics_lookup[fixture["team_a"]]["no_goals_scored_a"] += fixture["team_a_score"]
                team_metrics_lookup[fixture["team_a"]]["no_goals_conceded_a"] += fixture["team_h_score"]

        if fixture["team_h"] not in team_metrics_lookup:
            team_metric = {
                "team_id": fixture["team_h"],
                "no_games_a": 0,
                "no_games_h": 1,
                "no_goals_scored_a": 0,
                "no_goals_conceded_a": 0,
                "no_goals_scored_h": fixture["team_h_score"],
                "no_goals_conceded_h": fixture["team_a_score"]
            }
            team_metrics_lookup[fixture["team_h"]] = team_metric
        else:
            if team_metrics_lookup[fixture["team_h"]]["no_games_h"] < 3:
                team_metrics_lookup[fixture["team_h"]]["no_games_h"] += 1
                team_metrics_lookup[fixture["team_h"]]["no_goals_scored_h"] += fixture["team_h_score"]
                team_metrics_lookup[fixture["team_h"]]["no_goals_conceded_h"] += fixture["team_a_score"]


    print("create teams dict - calculating normalized attack/defense scores")
    # Find min/max values across all teams for normalization
    home_gs_values = [tm["no_goals_scored_h"] for tm in team_metrics_lookup.values() if tm["no_games_h"] > 0]
    home_gc_values = [tm["no_goals_conceded_h"] for tm in team_metrics_lookup.values() if tm["no_games_h"] > 0]
    away_gs_values = [tm["no_goals_scored_a"] for tm in team_metrics_lookup.values() if tm["no_games_a"] > 0]
    away_gc_values = [tm["no_goals_conceded_a"] for tm in team_metrics_lookup.values() if tm["no_games_a"] > 0]

    if home_gs_values:
        home_gs_min = min(home_gs_values)
        home_gs_max = max(home_gs_values)
    else:
        home_gs_min = 0
        home_gs_max = 0

    if home_gc_values:
        home_gc_min = min(home_gc_values)
        home_gc_max = max(home_gc_values)
    else:
        home_gc_min = 0
        home_gc_max = 0

    if away_gs_values:
        away_gs_min = min(away_gs_values)
        away_gs_max = max(away_gs_values)
    else:
        away_gs_min = 0
        away_gs_max = 0

    if away_gc_values:
        away_gc_min = min(away_gc_values)
        away_gc_max = max(away_gc_values)
    else:
        away_gc_min = 0
        away_gc_max = 0

    for i, team in enumerate(data["teams"]):
        print(f"processing team ({i+1}/{len(data['teams'])}) {team['name']}")

        # calculate team metrics where we have games for the team available (wont be there for start of season)
        if team["id"] in team_metrics_lookup:
            tm = team_metrics_lookup[team["id"]]

            # Attack score: higher goals scored is better -> direct min-max normalization
            # AttackScore = (GS - GS_min) / (GS_max - GS_min)
            if tm["no_games_h"] > 0 and home_gs_max != home_gs_min:
                tm["home_strength_attack"] = (tm["no_goals_scored_h"] - home_gs_min) / (home_gs_max - home_gs_min)
            else:
                tm["home_strength_attack"] = 0.5

            if tm["no_games_a"] > 0 and away_gs_max != away_gs_min:
                tm["away_strength_attack"] = (tm["no_goals_scored_a"] - away_gs_min) / (away_gs_max - away_gs_min)
            else:
                tm["away_strength_attack"] = 0.5

            # Defense score: lower goals conceded is better -> reversed min-max normalization
            # DefenseScore = (GC_max - GC) / (GC_max - GC_min)
            if tm["no_games_h"] > 0 and home_gc_max != home_gc_min:
                tm["home_strength_defence"] = (home_gc_max - tm["no_goals_conceded_h"]) / (home_gc_max - home_gc_min)
            else:
                tm["home_strength_defence"] = 0.5

            if tm["no_games_a"] > 0 and away_gc_max != away_gc_min:
                tm["away_strength_defence"] = (away_gc_max - tm["no_goals_conceded_a"]) / (away_gc_max - away_gc_min)
            else:
                tm["away_strength_defence"] = 0.5

            team_metrics_db.append(tm)

    # initialise lists for full player details
    past_fixtures = []
    upcoming_fixtures = []
    past_seasons = []

    player_metrics = []

    # Build player lookup for element_type (used for position ranking)
    player_lookup = {p['id']: p for p in data["elements"]}

    for i, player in enumerate(data["elements"]):
        print(f"processing player ({i+1}/{len(data['elements'])}) {player['first_name']} {player['second_name']}")
        # call api to get player summary
        player_data = fetch_fpl_player_summary(player['id'])

        # add player_id to lists where we dont have it
        for item in player_data["fixtures"]:
            item["player_id"] = player['id']

        for item in player_data["history_past"]:
            item["player_id"] = player['id']

        # append player data to full player lists for saving to db
        past_fixtures.extend(player_data["history"])
        upcoming_fixtures.extend(player_data["fixtures"])
        past_seasons.extend(player_data["history_past"])

        # calculate player metrics
        points_last_3_games = 0
        starts = 0
        starter_minutes = 0
        games_played_last_3_gw = 0

        last_3_count = 0

        # Determine which gameweeks count as "last 3" (e.g., if GW=12, then GW 10, 11, 12)
        min_gw_for_last_3 = max(1, gameweek - 2)

        # calculate metrics for historic games in reverse order or being player
        for f, fixture in enumerate(reversed(player_data["history"])):
            # FPL sometimes provides unset data when in middle of game week, so ignore for calcs
            if fixture['total_points'] is None or fixture['minutes'] is None or fixture['starts'] is None:
                continue

            if last_3_count < 3:
                last_3_count += 1
                points_last_3_games += fixture['total_points']

            # Only count games played in the actual last 3 gameweeks for the factor
            fixture_round = fixture.get('round', 0)
            if fixture_round >= min_gw_for_last_3 and fixture['minutes'] > 0:
                games_played_last_3_gw += 1

            if fixture['starts'] == 1:
                starts += 1
                starter_minutes += fixture['minutes']

        average_points_last_3_games = 0 if last_3_count == 0 else points_last_3_games / last_3_count

        min_per_90 = 0 if starter_minutes == 0 else starter_minutes / starts
        early_sub = min_per_90 < 60

        # Calculate games played factor: games where player got minutes / gameweeks available (max 3)
        # Uses the season gameweek to determine how many gameweeks have occurred
        available_gameweeks = min(gameweek, 3)
        if available_gameweeks == 0:
            games_played_factor = 1.0
        else:
            games_played_factor = games_played_last_3_gw / available_gameweeks

        # calculate metrics for upcoming games
        no_future_games = 0
        total_difficulty_next_3 = 0
        for f, fixture in enumerate(player_data["fixtures"]):
            no_future_games += 1
            opposing_team = fixture["team_a"] if fixture["is_home"] else fixture["team_h"]

            if player["element_type"] in [1, 2]: # GK and def
                if fixture["is_home"]:
                    total_difficulty_next_3 += team_metrics_lookup[opposing_team]["away_strength_attack"]
                else:
                    total_difficulty_next_3 += team_metrics_lookup[opposing_team]["home_strength_attack"]
            else: # mid or attack
                if fixture["is_home"]:
                    total_difficulty_next_3 += team_metrics_lookup[opposing_team]["away_strength_defence"]
                else:
                    total_difficulty_next_3 += team_metrics_lookup[opposing_team]["home_strength_defence"]

            if f >= 2: # only need to look at next 3 games
                break

        average_difficulty_next_3 = 0 if no_future_games == 0 else total_difficulty_next_3 / no_future_games

        # Calculate base selection likelihood from status
        if player['status'] == 'i' or player['status'] == 's': # i = injured s = suspended
            base_selection_likelihood = 0
        elif player['status'] == 'd' and early_sub: # doubtful
            base_selection_likelihood = 50
        elif player['status'] == 'd': # doubtful
            base_selection_likelihood = 67
        elif player['status'] == 'a' and early_sub: # available
            base_selection_likelihood = 80
        else:
            base_selection_likelihood = 95

        # Apply games played factor to selection likelihood
        selection_likelihood = int(base_selection_likelihood * games_played_factor)

        player_metric = {
            "player_id": player['id'],
            "total_points_per_pound": player['total_points'] / player['now_cost'],
            "points_last_3_games": points_last_3_games,
            'points_per_pound_last_3_games': points_last_3_games / player['now_cost'],
            'min_per_90': min_per_90,
            'early_sub': early_sub,
            "selection_likelihood": selection_likelihood,
            "games_played_factor": games_played_factor,
            "team_difficulty_next_3": average_difficulty_next_3,
        }

        player_metric["player_rating"] = (selection_likelihood * player_metric['points_per_pound_last_3_games']) / average_difficulty_next_3

        player_metrics.append(player_metric)

        # used for testing to reduce time
        # if i >= 10:
        #     break

    # calculate overall player rank
    ordered_player_metrics = sorted(
        player_metrics,
        key=lambda d: d["player_rating"],
        reverse=True
    )

    for i, player in enumerate(ordered_player_metrics):
        player["player_rank"] = i + 1

    # Group players by element_type using player_lookup
    players_by_position = defaultdict(list)
    for pm in player_metrics:
        element_type = player_lookup[pm["player_id"]]["element_type"]
        players_by_position[element_type].append(pm)

    # Sort each position group and assign position_rank
    for element_type, players in players_by_position.items():
        ordered_players = sorted(
            players,
            key=lambda d: d["player_rating"],
            reverse=True
        )
        for i, player in enumerate(ordered_players):
            player["position_rank"] = i + 1


    print("save data to db")
    with SessionLocal() as db:
        sync_teams(db, data["teams"])
        sync_players(db, data["elements"])
        sync_player_past_fixtures(db, past_fixtures)
        sync_player_upcoming_fixtures(db, upcoming_fixtures)
        sync_player_past_seasons(db, past_seasons)
        sync_team_metrics(db, team_metrics_db)
        sync_player_metrics(db, player_metrics)
        sync_user_players(db,user_players)
        pass
        
except Exception as e:
    print(f"Failed with : {e}")
