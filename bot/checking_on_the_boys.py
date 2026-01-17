import config
import csv
import daily_highs
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
    daily_highs.log_new_daily_kc_highs(player_name, kc_discrepencies)
    write_player_info_to_csv(player_info, player_name, "skills")
    write_player_info_to_csv(kc_info, player_name, "kc")
    return skill_discrepencies, kc_discrepencies, new_milestones


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