import requests

FPL_BASE_URL = "https://fantasy.premierleague.com/api"

class FPLError(RuntimeError):
    """ Raised when the FPL API call fails or returns unexpected data """
    

def fetch_fpl_entry(entry_id: int) -> dict:
    if entry_id <= 0:
        raise ValueError("entry_id must be a positive integer")

    url = f"{FPL_BASE_URL}/entry/{entry_id}"

    try:
        resp = requests.get(url)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.HTTPError as e:
        raise FPLError(f"FPL HTTP error: {e}") from e
    except requests.exceptions.RequestException as e:
        raise FPLError(f"FPL request failed: {e}") from e
    except ValueError as e:
        # .json() parse error
        raise FPLError("FPL response was not valid JSON") from e

    # Optional sanity checks (fields may evolve)
    if not isinstance(data, dict) or "name" not in data or "player_first_name" not in data:
        raise FPLError("FPL response shape unexpected (missing 'name' or 'player_first_name')")

    return data


def fetch_fpl_bootstrap() -> dict:
    url = f"{FPL_BASE_URL}/bootstrap-static/"

    try:
        resp = requests.get(url)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.HTTPError as e:
        raise FPLError(f"FPL HTTP error: {e}") from e
    except requests.exceptions.RequestException as e:
        raise FPLError(f"FPL request failed: {e}") from e
    except ValueError as e:
        # .json() parse error
        raise FPLError("FPL response was not valid JSON") from e

    return data


def fetch_fpl_fixtures() -> list[dict]:
    url = f"{FPL_BASE_URL}/fixtures/"

    try:
        resp = requests.get(url)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.HTTPError as e:
        raise FPLError(f"FPL HTTP error: {e}") from e
    except requests.exceptions.RequestException as e:
        raise FPLError(f"FPL request failed: {e}") from e
    except ValueError as e:
        # .json() parse error
        raise FPLError("FPL response was not valid JSON") from e

    # Optional sanity check (fixtures endpoint returns a list)
    if not isinstance(data, list):
        raise FPLError("FPL fixtures response shape unexpected (expected list)")

    return data


def fetch_fpl_player_summary(player_id: int) -> dict:
    if player_id <= 0:
        raise ValueError("player_id must be a positive integer")

    url = f"{FPL_BASE_URL}/element-summary/{player_id}/"

    try:
        resp = requests.get(url)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.HTTPError as e:
        raise FPLError(f"FPL HTTP error: {e}") from e
    except requests.exceptions.RequestException as e:
        raise FPLError(f"FPL request failed: {e}") from e
    except ValueError as e:
        # .json() parse error
        raise FPLError("FPL response was not valid JSON") from e

    # Optional sanity check (element-summary returns a dict)
    if not isinstance(data, dict) or "history" not in data:
        raise FPLError("FPL player summary response shape unexpected")

    return data

def fetch_fpl_team(entry_id: int, gameweek: int) -> dict:
    """
    Fetch a team's picks for a specific gameweek using their FPL entry ID.
    """
    if entry_id <= 0:
        raise ValueError("entry_id must be a positive integer")

    if gameweek <= 0:
        raise ValueError("gameweek must be a positive integer")

    url = f"{FPL_BASE_URL}/entry/{entry_id}/event/{gameweek}/picks/"

    try:
        resp = requests.get(url)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.HTTPError as e:
        raise FPLError(f"FPL HTTP error: {e}") from e
    except requests.exceptions.RequestException as e:
        raise FPLError(f"FPL request failed: {e}") from e
    except ValueError as e:
        # .json() parse error
        raise FPLError("FPL response was not valid JSON") from e

    # Sanity checks (documented response shape)
    if (
        not isinstance(data, dict)
        or "picks" not in data
        or "entry_history" not in data
    ):
        raise FPLError("FPL team response shape unexpected (missing 'picks' or 'entry_history')")

    return data


def fetch_fpl_entry_leagues(entry_id: int) -> list[dict]:
    """
    Fetch all leagues a team is participating in.
    Returns list of league dicts with id, name, and type info.
    """
    if entry_id <= 0:
        raise ValueError("entry_id must be a positive integer")

    # Get the entry data which contains league info
    entry_data = fetch_fpl_entry(entry_id)

    leagues = []

    # Classic leagues (private and public)
    if "leagues" in entry_data:
        league_data = entry_data["leagues"]

        # Classic leagues
        for league in league_data.get("classic", []):
            leagues.append({
                "id": league["id"],
                "name": league["name"],
                "type": "classic",
                "entry_rank": league.get("entry_rank"),
                "entry_last_rank": league.get("entry_last_rank"),
            })

        # Head-to-head leagues
        for league in league_data.get("h2h", []):
            leagues.append({
                "id": league["id"],
                "name": league["name"],
                "type": "h2h",
                "entry_rank": league.get("entry_rank"),
                "entry_last_rank": league.get("entry_last_rank"),
            })

    return leagues


def fetch_fpl_league_standings(league_id: int, league_type: str = "classic", page: int = 1) -> dict:
    """
    Fetch standings for a specific league.

    Args:
        league_id: The league ID
        league_type: "classic" or "h2h"
        page: Page number for pagination (50 entries per page)

    Returns dict with league info and standings.
    """
    if league_id <= 0:
        raise ValueError("league_id must be a positive integer")

    if league_type == "h2h":
        url = f"{FPL_BASE_URL}/leagues-h2h/{league_id}/standings/?page_standings={page}"
    else:
        url = f"{FPL_BASE_URL}/leagues-classic/{league_id}/standings/?page_standings={page}"

    try:
        resp = requests.get(url)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.HTTPError as e:
        raise FPLError(f"FPL HTTP error: {e}") from e
    except requests.exceptions.RequestException as e:
        raise FPLError(f"FPL request failed: {e}") from e
    except ValueError as e:
        raise FPLError("FPL response was not valid JSON") from e

    if not isinstance(data, dict) or "standings" not in data:
        raise FPLError("FPL league standings response shape unexpected")

    return data


def fetch_all_league_standings(league_id: int, league_type: str = "classic", max_pages: int = 10) -> dict:
    """
    Fetch all standings for a league, handling pagination.

    Args:
        league_id: The league ID
        league_type: "classic" or "h2h"
        max_pages: Maximum pages to fetch (safety limit)

    Returns dict with league info and all standings.
    """
    all_results = []
    league_info = None
    page = 1

    while page <= max_pages:
        data = fetch_fpl_league_standings(league_id, league_type, page)

        if league_info is None:
            league_info = data.get("league", {})

        standings = data.get("standings", {})
        results = standings.get("results", [])

        if not results:
            break

        all_results.extend(results)

        # Check if there are more pages
        if not standings.get("has_next", False):
            break

        page += 1

    return {
        "league": league_info,
        "standings": all_results
    }
