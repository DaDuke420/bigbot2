# newsletter.py
import config
import logging
import snapshots
from datetime import date

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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

def generate_newsletter():
    updates = {}
    for player in config.GIM_MEMBERS:
        try:
            xp_update, kc_update, new_milestones = snapshots.check_new_info_and_update_data(player)
            character_updates = [xp_update, kc_update, new_milestones]
            logger.info(player)
            logger.info(character_updates)
            if player in config.NEWSLETTER_MEMBERS:
                updates[player] = character_updates
        except Exception as e:
            logger.info(player)
            logger.info(f"Not enough data: {e}")
    return(create_email_string(updates))