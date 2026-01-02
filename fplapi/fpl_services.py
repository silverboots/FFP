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


