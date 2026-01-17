import csv
from pathlib import Path
import bot.daily_highs as daily_highs
import bot.storage as storage


def test_log_new_daily_kc_highs_creates_new_records_and_writes_csv(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    deltas = {"Zulrah": 5, "Vorkath": 0, "": 10, "Neg": -1, "StrNum": "3"}

    updated = daily_highs.log_new_daily_kc_highs("Tester", deltas, as_of=None, storage_dir=str(tmp_path))

    # Should record Zulrah (5) and StrNum (3) as they are positive
    assert updated["Zulrah"][0] == 5
    assert updated["Zulrah"][1] == 0
    assert updated["StrNum"][0] == 3

    # CSV should exist and include the new highs
    csv_path = Path(storage.create_data_path("Tester", "kc_daily_highs"))
    assert csv_path.exists()
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    bosses = {r["boss"]: int(r["highest_kc"]) for r in rows}
    assert bosses["Zulrah"] == 5
    assert bosses["StrNum"] == 3


def test_get_highest_one_day_kc_per_boss_reads_file_and_parses(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    csv_path = Path(storage.create_data_path("PlayerX", "kc_daily_highs"))
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["boss", "highest_kc", "achieved_on"])
        writer.writeheader()
        writer.writerow({"boss": "Zulrah", "highest_kc": 3, "achieved_on": "2026-01-01"})
        writer.writerow({"boss": "Vorkath", "highest_kc": 7, "achieved_on": "2026-01-02"})

    result = daily_highs.get_highest_one_day_kc_per_boss("PlayerX")
    assert result == {"Vorkath": 7, "Zulrah": 3}


def test_log_updates_records_when_higher(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    # seed an existing high
    csv_path = Path(storage.create_data_path("PlayerY", "kc_daily_highs"))
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["boss", "highest_kc", "achieved_on"])
        writer.writeheader()
        writer.writerow({"boss": "Zulrah", "highest_kc": 3, "achieved_on": "2026-01-01"})

    updated = daily_highs.log_new_daily_kc_highs("PlayerY", {"Zulrah": 6}, as_of=None)
    assert updated == {"Zulrah": (6, 3)}

    # file should reflect the new high
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        rows = {r["boss"]: int(r["highest_kc"]) for r in reader}
    assert rows["Zulrah"] == 6
