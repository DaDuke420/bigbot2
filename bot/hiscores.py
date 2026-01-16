# hiscores.py
import config
import requests

def get_player_info(player_name):
    response = requests.get(config.HISCORES_URL + player_name)
    attempts = 1

    while attempts < 5:
        if response.status_code == 200:
            return unpack_info(response)
        response = requests.get(config.HISCORES_URL + player_name)
        attempts += 1
    return

def unpack_info(response):
    xp = {}
    kc = {}
    row = 0
    for skill in response.iter_lines():
        line = skill.decode("utf-8").strip()
        parts = line.split(",")
        if row <= 24:
            rank, level, current_xp = parts
            xp[config.SKILL_ROW_ORDER[row]] = current_xp
        else:
            identifier, current_kc = parts
            if row in config.KC_MAPPING.keys():
                monster = config.KC_MAPPING[row]
            else:
                monster = "Unknown Boss" + " " + str(row)
            if identifier != "-1" and row not in config.SKIP_LIST:
                kc[monster] = current_kc
        row = row + 1
    return xp, kc