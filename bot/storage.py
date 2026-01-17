# storage.py
import config
import os

def create_data_path(player, data_type):
    return os.path.join(config.DATA_DIR, f"{player}_{data_type}.csv")

def ensure_data_dir():
    os.makedirs(config.DATA_DIR, exist_ok=True)