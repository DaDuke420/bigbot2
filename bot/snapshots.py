# snapshots.py
from . import config
import csv
from . import daily_highs
from . import hiscores
import math
import os
from . import storage

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