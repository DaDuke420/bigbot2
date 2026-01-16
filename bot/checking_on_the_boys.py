import config
import csv
import hiscores
import logging
import math
import os
import random
import requests
import storage
from datetime import date
from typing import Dict, Optional, Tuple


def compare_file_to_dict(player_info, player_name, data_type):
    csv_file = storage.create_data_path(player_name, data_type)
    with open(csv_file, mode='r') as f:
        reader = csv.reader(f)
        curr_row = 0
        keys = []
        values = []
        for row in reader:
            if curr_row == 0:
                keys = row
            if curr_row == 1:
                values = row
            curr_row = curr_row + 1
        file_dict = {}
        for i in range(len(keys)):
            file_dict[keys[i]] = values[i]
        discrepencies = {}
        new_milestones = []
        for key in player_info.keys():
            if key not in file_dict.keys():
                discrepencies[key] = int(player_info[key])
            else:
                if player_info[key] != file_dict[key]:
                    discrepencies[key] = int(player_info[key]) - int(file_dict[key])
                    if key in config.SKILL_ROW_ORDER and int(player_info[key]) >= 13034431 and int(file_dict[key]) < 13034431:
                        new_milestones.append(["99", key])
                    if key not in config.SKILL_ROW_ORDER and math.floor(int(player_info[key]) / 100) > math.floor(int(file_dict[key]) / 100):
                        new_milestones.append(["kc", math.floor(int(player_info[key]) / 100) * 100, key])
        return discrepencies, new_milestones


def write_player_info_to_csv(player_info, player_name, data_type):
    os.makedirs(config.DATA_DIR, exist_ok=True)
    
    csv_name = storage.create_data_path(player_name, data_type)
    headers = player_info.keys()
    with open(csv_name, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()
        writer.writerows([player_info])

def check_new_info_and_update_data(player_name):
    player_info, kc_info = hiscores.get_player_info(player_name)
    if not player_info or not kc_info:
        return {}, {}
    xp_updates = None
    skill_discrepencies = {}
    new_milestones = []
    skills_csv_name = storage.create_data_path(player_name, "skills")
    kc_csv_name = storage.create_data_path(player_name, "kc")
    if os.path.exists(skills_csv_name):
        skill_discrepencies, skill_milestones = compare_file_to_dict(player_info, player_name, "skills")
        new_milestones.extend(skill_milestones)
    kc_discrepencies = {}
    if os.path.exists(kc_csv_name):
        kc_discrepencies, kc_milestones = compare_file_to_dict(kc_info, player_name, "kc")
        new_milestones.extend(kc_milestones)
    log_new_daily_kc_highs(player_name, kc_discrepencies)
    write_player_info_to_csv(player_info, player_name, "skills")
    write_player_info_to_csv(kc_info, player_name, "kc")
    return skill_discrepencies, kc_discrepencies, new_milestones


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


def format_player_xp_and_kc_updates_to_email(player_xp, player_kc, player_milestones, player_name):
    if not player_xp.keys() and not player_kc.keys() and len(player_milestones) == 0:
        return player_name + " has not played since the last newsletter."
    formatted_string = player_name + "\n"
    if len(player_milestones) > 0:
        formatted_string = formatted_string + "    We have milestones to acknowledge!\n"
        for milestone in player_milestones:
            if milestone[0] == "99":
                formatted_string = formatted_string + "    " + player_name + " has achieved 99 " + milestone[1] + "! Wowza!\n"
            if milestone[0] == "kc":
                formatted_string = formatted_string + "    " + player_name + " has surpassed " + str(milestone[1]) + " " + milestone[2] + " kc!\n"
        formatted_string = formatted_string + "\n"
    if not player_xp.keys():
        formatted_string = formatted_string + "No new XP to report.\n"
    for skill in player_xp:
        formatted_string = formatted_string + "    " + skill + ": " + str(player_xp[skill]) + " xp" + "\n"
    if not player_kc.keys():
        formatted_string = formatted_string + "\n    No new KC to report."
    for kcs in player_kc:
        formatted_string = formatted_string + "\n"
        formatted_string = formatted_string + "    " + kcs + ": " + str(player_kc[kcs]) + " new kc"
    return formatted_string

def create_email_string(player_updates):
    email_body = f"Hello,\nWelcome to the DaKings GIM Newsletter for {date.today()}! Let's see what the goons have been up to.\n\n"
    for update in player_updates:
        email_body = email_body + format_player_xp_and_kc_updates_to_email(player_updates[update][0], player_updates[update][1], player_updates[update][2], update) + "\n\n"
    return email_body + "Another banger day for the boys! See you next time!"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_newsletter():
    updates = {}
    for player in config.GIM_MEMBERS:
        try:
            xp_update, kc_update, new_milestones = check_new_info_and_update_data(player)
            character_updates = [xp_update, kc_update, new_milestones]
            logger.info(player)
            logger.info(character_updates)
            if player in config.NEWSLETTER_MEMBERS:
                updates[player] = character_updates
        except Exception as e:
            logger.info(player)
            logger.info(f"Not enough data: {e}")
    return(create_email_string(updates))