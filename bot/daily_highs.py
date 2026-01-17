# daily_highs.py
import csv
import os
from . import storage
from datetime import date
from typing import Dict, Optional, Tuple
from . import config

def _safe_int(val) -> Optional[int]:
    """Convert a value to int safely. Returns None if not convertible."""
    try:
        return int(val)
    except (TypeError, ValueError):
        return None

def log_new_daily_kc_highs(
    player_name: str,
    kc_deltas: Dict[str, int],
    as_of: Optional[date] = None,
    storage_dir: str = ".",
) -> Dict[str, Tuple[int, int]]:
    """
    Logs any new 'highest KC in a single day' for each boss for a given player.

    Expected input:
      - kc_deltas: dict like {"Vorkath": 12, "Zulrah": 0, ...}
        (i.e. the *delta* since last snapshot/newsletter)

    Persistence:
      Writes/updates a CSV at:
        <storage_dir>/<player_name>_kc_daily_highs.csv

      CSV schema:
        boss,highest_kc,achieved_on

    Returns:
      dict mapping boss -> (new_highest_kc, old_highest_kc) for bosses that set a new record.
    """
    if as_of is None:
        as_of = date.today()

    os.makedirs(storage_dir, exist_ok=True)
    csv_path = storage.create_data_path(player_name, "kc_daily_highs")

    # Load existing highs
    highs: Dict[str, Tuple[int, str]] = {}  # boss -> (highest_kc, achieved_on)
    if os.path.exists(csv_path):
        with open(csv_path, mode="r", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                boss = (row.get("boss") or "").strip()
                hi = _safe_int(row.get("highest_kc"))
                achieved_on = (row.get("achieved_on") or "").strip()
                if boss and hi is not None:
                    highs[boss] = (hi, achieved_on)

    # Apply updates
    updated_records: Dict[str, Tuple[int, int]] = {}
    for boss, delta in (kc_deltas or {}).items():
        boss = str(boss).strip()
        d = _safe_int(delta)
        if not boss or d is None or d <= 0:
            continue  # ignore non-positive or invalid deltas

        old_hi = highs.get(boss, (0, ""))[0]
        if d > old_hi:
            highs[boss] = (d, as_of.isoformat())
            updated_records[boss] = (d, old_hi)

    # Ensure the CSV parent directory exists, then write back.
    dirpath = os.path.dirname(csv_path)
    if dirpath:
        os.makedirs(dirpath, exist_ok=True)

    # Write back (canonical order for stable diffs)
    with open(csv_path, mode="w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["boss", "highest_kc", "achieved_on"])
        writer.writeheader()
        for boss in sorted(highs.keys()):
            hi, achieved_on = highs[boss]
            writer.writerow({"boss": boss, "highest_kc": hi, "achieved_on": achieved_on})

    return updated_records


def get_highest_one_day_kc_per_boss(
    player_name: str,
    storage_dir: str = ".",
) -> Dict[str, int]:
    """
    Returns the highest one-day KC per boss for a given player, as a dict:
      {"Vorkath": 27, "Zulrah": 19, ...}

    Reads:
      <storage_dir>/<player_name>_kc_daily_highs.csv

    If the file doesn't exist yet, returns {}.
    """
    csv_path = storage.create_data_path(player_name, "kc_daily_highs")
    if not os.path.exists(csv_path):
        return {}

    result: Dict[str, int] = {}
    with open(csv_path, mode="r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            boss = (row.get("boss") or "").strip()
            hi = _safe_int(row.get("highest_kc"))
            if boss and hi is not None:
                result[boss] = hi
    return result


def get_player_daily_high_for_boss(player_name: str, boss: str, storage_dir: str = ".") -> Optional[int]:
    """Return the highest one-day KC for `boss` for `player_name`, or None if not present."""
    if not boss:
        return None
    data = get_highest_one_day_kc_per_boss(player_name, storage_dir=storage_dir)
    return data.get(boss)


def get_highest_daily_high_among_members(boss: str, members: Optional[list] = None, storage_dir: str = ".") -> Optional[Tuple[str, int]]:
    """Return (player_name, high) for the highest one-day KC of `boss` among `members`.

    If `members` is None, uses `config.NEWSLETTER_MEMBERS`.
    Returns None when no member has a recorded high for the boss.
    """
    if not boss:
        return None
    if members is None:
        members = getattr(config, "NEWSLETTER_MEMBERS", [])

    top_player: Optional[str] = None
    top_value: Optional[int] = None

    for member in members:
        highs = get_highest_one_day_kc_per_boss(member, storage_dir=storage_dir)
        val = highs.get(boss)
        if val is None:
            continue
        if top_value is None or val > top_value:
            top_value = val
            top_player = member

    if top_player is None:
        return None
    return top_player, top_value