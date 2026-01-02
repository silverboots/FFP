from sqlalchemy.orm import Mapped, mapped_column
from database.db import Base
from datetime import datetime
from sqlalchemy import Integer, Boolean, String, DateTime,Float


class User(Base):
    __tablename__ = "Users"

    email: Mapped[str] = mapped_column(String(50), primary_key=True, unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    team_id: Mapped[int] = mapped_column(Integer, nullable=False)

class Team(Base):
    __tablename__ = "Teams"

    team_id: Mapped[int] = mapped_column(Integer, primary_key=True, unique=True, index=True, nullable=False)
    code: Mapped[int] = mapped_column(Integer)
    draw: Mapped[int] = mapped_column(Integer, nullable=False)
    form: Mapped[int] = mapped_column(Integer, nullable=True)
    loss: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    played: Mapped[int] = mapped_column(Integer, nullable=False)
    points: Mapped[int] = mapped_column(Integer, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    short_name: Mapped[str] = mapped_column(String, nullable=False)
    strength: Mapped[int] = mapped_column(Integer, nullable=False)
    team_division: Mapped[int] = mapped_column(Integer, nullable=True)
    unavailable: Mapped[bool] = mapped_column(Boolean, nullable=True)
    win: Mapped[int] = mapped_column(Integer, nullable=False)
    strength_overall_home: Mapped[int] = mapped_column(Integer, nullable=False)
    strength_overall_away: Mapped[int] = mapped_column(Integer, nullable=False)
    strength_attack_home: Mapped[int] = mapped_column(Integer, nullable=False)
    strength_attack_away: Mapped[int] = mapped_column(Integer, nullable=False)
    strength_defence_home: Mapped[int] = mapped_column(Integer, nullable=False)
    strength_defence_away: Mapped[int] = mapped_column(Integer, nullable=False)
    pulse_id: Mapped[int] = mapped_column(Integer, nullable=False)


class Player(Base):
    __tablename__ = "Players"

    player_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    can_transact: Mapped[bool] = mapped_column(Boolean, nullable=False)
    can_select: Mapped[bool] = mapped_column(Boolean, nullable=False)

    chance_of_playing_next_round: Mapped[int | None] = mapped_column(Integer, nullable=True)
    chance_of_playing_this_round: Mapped[int | None] = mapped_column(Integer, nullable=True)

    code: Mapped[int] = mapped_column(Integer, nullable=False)

    cost_change_event: Mapped[int] = mapped_column(Integer, nullable=False)
    cost_change_event_fall: Mapped[int] = mapped_column(Integer, nullable=False)
    cost_change_start: Mapped[int] = mapped_column(Integer, nullable=False)
    cost_change_start_fall: Mapped[int] = mapped_column(Integer, nullable=False)

    dreamteam_count: Mapped[int] = mapped_column(Integer, nullable=False)
    element_type: Mapped[int] = mapped_column(Integer, nullable=False)

    ep_next: Mapped[float] = mapped_column(Float, nullable=False)
    ep_this: Mapped[float] = mapped_column(Float, nullable=False)

    event_points: Mapped[int] = mapped_column(Integer, nullable=False)

    first_name: Mapped[str] = mapped_column(String, nullable=False)
    second_name: Mapped[str] = mapped_column(String, nullable=False)
    web_name: Mapped[str] = mapped_column(String, nullable=False)

    form: Mapped[float] = mapped_column(Float, nullable=False)
    points_per_game: Mapped[float] = mapped_column(Float, nullable=False)

    in_dreamteam: Mapped[bool] = mapped_column(Boolean, nullable=False)
    removed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    special: Mapped[bool] = mapped_column(Boolean, nullable=False)
    has_temporary_code: Mapped[bool] = mapped_column(Boolean, nullable=False)

    news: Mapped[str] = mapped_column(String, nullable=False)
    news_added: Mapped[str | None] = mapped_column(String, nullable=True)

    now_cost: Mapped[int] = mapped_column(Integer, nullable=False)
    photo: Mapped[str] = mapped_column(String, nullable=False)
    opta_code: Mapped[str] = mapped_column(String, nullable=False)

    selected_by_percent: Mapped[float] = mapped_column(Float, nullable=False)

    squad_number: Mapped[int | None] = mapped_column(Integer, nullable=True)

    status: Mapped[str] = mapped_column(String(1), nullable=False)

    team: Mapped[int] = mapped_column(Integer, nullable=False)
    team_code: Mapped[int] = mapped_column(Integer, nullable=False)
    region: Mapped[int] = mapped_column(Integer, nullable=True)

    total_points: Mapped[int] = mapped_column(Integer, nullable=False)

    transfers_in: Mapped[int] = mapped_column(Integer, nullable=False)
    transfers_in_event: Mapped[int] = mapped_column(Integer, nullable=False)
    transfers_out: Mapped[int] = mapped_column(Integer, nullable=False)
    transfers_out_event: Mapped[int] = mapped_column(Integer, nullable=False)

    value_form: Mapped[float] = mapped_column(Float, nullable=False)
    value_season: Mapped[float] = mapped_column(Float, nullable=False)

    team_join_date: Mapped[str] = mapped_column(String, nullable=True)
    birth_date: Mapped[str] = mapped_column(String, nullable=True)

    minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    goals_scored: Mapped[int] = mapped_column(Integer, nullable=False)
    assists: Mapped[int] = mapped_column(Integer, nullable=False)
    clean_sheets: Mapped[int] = mapped_column(Integer, nullable=False)
    goals_conceded: Mapped[int] = mapped_column(Integer, nullable=False)

    own_goals: Mapped[int] = mapped_column(Integer, nullable=False)
    penalties_saved: Mapped[int] = mapped_column(Integer, nullable=False)
    penalties_missed: Mapped[int] = mapped_column(Integer, nullable=False)

    yellow_cards: Mapped[int] = mapped_column(Integer, nullable=False)
    red_cards: Mapped[int] = mapped_column(Integer, nullable=False)
    saves: Mapped[int] = mapped_column(Integer, nullable=False)

    bonus: Mapped[int] = mapped_column(Integer, nullable=False)
    bps: Mapped[int] = mapped_column(Integer, nullable=False)

    influence: Mapped[float] = mapped_column(Float, nullable=False)
    creativity: Mapped[float] = mapped_column(Float, nullable=False)
    threat: Mapped[float] = mapped_column(Float, nullable=False)
    ict_index: Mapped[float] = mapped_column(Float, nullable=False)

    clearances_blocks_interceptions: Mapped[int] = mapped_column(Integer, nullable=False)
    recoveries: Mapped[int] = mapped_column(Integer, nullable=False)
    tackles: Mapped[int] = mapped_column(Integer, nullable=False)
    defensive_contribution: Mapped[int] = mapped_column(Integer, nullable=False)

    starts: Mapped[int] = mapped_column(Integer, nullable=False)

    expected_goals: Mapped[float] = mapped_column(Float, nullable=False)
    expected_assists: Mapped[float] = mapped_column(Float, nullable=False)
    expected_goal_involvements: Mapped[float] = mapped_column(Float, nullable=False)
    expected_goals_conceded: Mapped[float] = mapped_column(Float, nullable=False)

    influence_rank: Mapped[int] = mapped_column(Integer, nullable=False)
    influence_rank_type: Mapped[int] = mapped_column(Integer, nullable=False)
    creativity_rank: Mapped[int] = mapped_column(Integer, nullable=False)
    creativity_rank_type: Mapped[int] = mapped_column(Integer, nullable=False)
    threat_rank: Mapped[int] = mapped_column(Integer, nullable=False)
    threat_rank_type: Mapped[int] = mapped_column(Integer, nullable=False)
    ict_index_rank: Mapped[int] = mapped_column(Integer, nullable=False)
    ict_index_rank_type: Mapped[int] = mapped_column(Integer, nullable=False)

    corners_and_indirect_freekicks_order: Mapped[int | None] = mapped_column(Integer, nullable=True)
    corners_and_indirect_freekicks_text: Mapped[str] = mapped_column(String, nullable=False)
    direct_freekicks_order: Mapped[int | None] = mapped_column(Integer, nullable=True)
    direct_freekicks_text: Mapped[str] = mapped_column(String, nullable=False)
    penalties_order: Mapped[int | None] = mapped_column(Integer, nullable=True)
    penalties_text: Mapped[str] = mapped_column(String, nullable=True)

    expected_goals_per_90: Mapped[float] = mapped_column(Float, nullable=False)
    saves_per_90: Mapped[float] = mapped_column(Float, nullable=False)
    expected_assists_per_90: Mapped[float] = mapped_column(Float, nullable=False)
    expected_goal_involvements_per_90: Mapped[float] = mapped_column(Float, nullable=False)
    expected_goals_conceded_per_90: Mapped[float] = mapped_column(Float, nullable=False)
    goals_conceded_per_90: Mapped[float] = mapped_column(Float, nullable=False)

    now_cost_rank: Mapped[int] = mapped_column(Integer, nullable=False)
    now_cost_rank_type: Mapped[int] = mapped_column(Integer, nullable=False)
    form_rank: Mapped[int] = mapped_column(Integer, nullable=False)
    form_rank_type: Mapped[int] = mapped_column(Integer, nullable=False)
    points_per_game_rank: Mapped[int] = mapped_column(Integer, nullable=False)
    points_per_game_rank_type: Mapped[int] = mapped_column(Integer, nullable=False)
    selected_rank: Mapped[int] = mapped_column(Integer, nullable=False)
    selected_rank_type: Mapped[int] = mapped_column(Integer, nullable=False)

    starts_per_90: Mapped[float] = mapped_column(Float, nullable=False)
    clean_sheets_per_90: Mapped[float] = mapped_column(Float, nullable=False)
    defensive_contribution_per_90: Mapped[float] = mapped_column(Float, nullable=False)

class PlayerPastFixture(Base):
    __tablename__ = "PlayerPastFixtures"

    fixture_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[int] = mapped_column(Integer, primary_key=True)

    opponent_team: Mapped[int] = mapped_column(Integer, nullable=False)
    round: Mapped[int] = mapped_column(Integer, nullable=False)

    was_home: Mapped[bool] = mapped_column(Boolean, nullable=False)
    kickoff_time: Mapped[DateTime | None] = mapped_column(DateTime, nullable=True)

    team_h_score: Mapped[int] = mapped_column(Integer, nullable=False)
    team_a_score: Mapped[int] = mapped_column(Integer, nullable=False)

    total_points: Mapped[int] = mapped_column(Integer, nullable=False)
    minutes: Mapped[int] = mapped_column(Integer, nullable=False)

    goals_scored: Mapped[int] = mapped_column(Integer, nullable=False)
    assists: Mapped[int] = mapped_column(Integer, nullable=False)
    clean_sheets: Mapped[int] = mapped_column(Integer, nullable=False)
    goals_conceded: Mapped[int] = mapped_column(Integer, nullable=False)
    own_goals: Mapped[int] = mapped_column(Integer, nullable=False)

    penalties_saved: Mapped[int] = mapped_column(Integer, nullable=False)
    penalties_missed: Mapped[int] = mapped_column(Integer, nullable=False)

    yellow_cards: Mapped[int] = mapped_column(Integer, nullable=False)
    red_cards: Mapped[int] = mapped_column(Integer, nullable=False)

    saves: Mapped[int] = mapped_column(Integer, nullable=False)
    bonus: Mapped[int] = mapped_column(Integer, nullable=False)
    bps: Mapped[int] = mapped_column(Integer, nullable=False)

    influence: Mapped[float] = mapped_column(nullable=False)
    creativity: Mapped[float] = mapped_column(nullable=False)
    threat: Mapped[float] = mapped_column(nullable=False)
    ict_index: Mapped[float] = mapped_column(nullable=False)

    clearances_blocks_interceptions: Mapped[int] = mapped_column(Integer, nullable=False)
    recoveries: Mapped[int] = mapped_column(Integer, nullable=False)
    tackles: Mapped[int] = mapped_column(Integer, nullable=False)
    defensive_contribution: Mapped[int] = mapped_column(Integer, nullable=False)
    starts: Mapped[int] = mapped_column(Integer, nullable=False)

    expected_goals: Mapped[float] = mapped_column(nullable=False)
    expected_assists: Mapped[float] = mapped_column(nullable=False)
    expected_goal_involvements: Mapped[float] = mapped_column(nullable=False)
    expected_goals_conceded: Mapped[float] = mapped_column(nullable=False)

    value: Mapped[int] = mapped_column(Integer, nullable=False)
    transfers_balance: Mapped[int] = mapped_column(Integer, nullable=False)
    selected: Mapped[int] = mapped_column(Integer, nullable=False)
    transfers_in: Mapped[int] = mapped_column(Integer, nullable=False)
    transfers_out: Mapped[int] = mapped_column(Integer, nullable=False)

    modified: Mapped[bool] = mapped_column(Boolean, nullable=False)

class PlayerPastSeason(Base):
    __tablename__ = "PlayerPastSeasons"

    season_name: Mapped[str] = mapped_column(String, primary_key=True)
    player_id: Mapped[int] = mapped_column(Integer, primary_key=True)

    element_code: Mapped[int] = mapped_column(Integer, nullable=False)
    start_cost: Mapped[int] = mapped_column(Integer, nullable=False)
    end_cost: Mapped[int] = mapped_column(Integer, nullable=False)

    total_points: Mapped[int] = mapped_column(Integer, nullable=False)
    minutes: Mapped[int] = mapped_column(Integer, nullable=False)

    goals_scored: Mapped[int] = mapped_column(Integer, nullable=False)
    assists: Mapped[int] = mapped_column(Integer, nullable=False)
    clean_sheets: Mapped[int] = mapped_column(Integer, nullable=False)
    goals_conceded: Mapped[int] = mapped_column(Integer, nullable=False)
    own_goals: Mapped[int] = mapped_column(Integer, nullable=False)

    penalties_saved: Mapped[int] = mapped_column(Integer, nullable=False)
    penalties_missed: Mapped[int] = mapped_column(Integer, nullable=False)

    yellow_cards: Mapped[int] = mapped_column(Integer, nullable=False)
    red_cards: Mapped[int] = mapped_column(Integer, nullable=False)

    saves: Mapped[int] = mapped_column(Integer, nullable=False)
    bonus: Mapped[int] = mapped_column(Integer, nullable=False)
    bps: Mapped[int] = mapped_column(Integer, nullable=False)

    influence: Mapped[float] = mapped_column(nullable=False)
    creativity: Mapped[float] = mapped_column(nullable=False)
    threat: Mapped[float] = mapped_column(nullable=False)
    ict_index: Mapped[float] = mapped_column(nullable=False)

    clearances_blocks_interceptions: Mapped[int] = mapped_column(Integer, nullable=False)
    recoveries: Mapped[int] = mapped_column(Integer, nullable=False)
    tackles: Mapped[int] = mapped_column(Integer, nullable=False)
    defensive_contribution: Mapped[int] = mapped_column(Integer, nullable=False)
    starts: Mapped[int] = mapped_column(Integer, nullable=False)

    expected_goals: Mapped[float] = mapped_column(nullable=False)
    expected_assists: Mapped[float] = mapped_column(nullable=False)
    expected_goal_involvements: Mapped[float] = mapped_column(nullable=False)
    expected_goals_conceded: Mapped[float] = mapped_column(nullable=False)

class PlayerUpcomingFixture(Base):
    __tablename__ = "PlayerUpcomingFixtures"

    fixture_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[int] = mapped_column(Integer, primary_key=True)

    code: Mapped[int] = mapped_column(Integer, nullable=False)

    team_h: Mapped[int] = mapped_column(Integer, nullable=False)
    team_h_score: Mapped[int | None] = mapped_column(Integer, nullable=True)

    team_a: Mapped[int] = mapped_column(Integer, nullable=False)
    team_a_score: Mapped[int | None] = mapped_column(Integer, nullable=True)

    event: Mapped[int] = mapped_column(Integer, nullable=False)
    event_name: Mapped[str] = mapped_column(String, nullable=False)

    finished: Mapped[bool] = mapped_column(Boolean, nullable=False)
    minutes: Mapped[int] = mapped_column(Integer, nullable=False)

    provisional_start_time: Mapped[bool] = mapped_column(Boolean, nullable=False)
    kickoff_time: Mapped[DateTime | None] = mapped_column(DateTime, nullable=True)

    is_home: Mapped[bool] = mapped_column(Boolean, nullable=False)
    difficulty: Mapped[int] = mapped_column(Integer, nullable=False)



class TeamMetric(Base):
    __tablename__ = "TeamMetric"

    team_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        unique=True,
        index=True,
        nullable=False,
    )

    # Away game aggregates (last up to 3)
    no_games_a: Mapped[int] = mapped_column(Integer, nullable=False)
    no_goals_scored_a: Mapped[int] = mapped_column(Integer, nullable=False)
    no_goals_conceded_a: Mapped[int] = mapped_column(Integer, nullable=False)

    # Home game aggregates (last up to 3)
    no_games_h: Mapped[int] = mapped_column(Integer, nullable=False)
    no_goals_scored_h: Mapped[int] = mapped_column(Integer, nullable=False)
    no_goals_conceded_h: Mapped[int] = mapped_column(Integer, nullable=False)

    # Derived strength metrics (calculated later)
    home_strength_defence: Mapped[float] = mapped_column(Float, nullable=False)
    away_strength_defence: Mapped[float] = mapped_column(Float, nullable=False)
    home_strength_attack: Mapped[float] = mapped_column(Float, nullable=False)
    away_strength_attack: Mapped[float] = mapped_column(Float, nullable=False)