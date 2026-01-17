import os
import csv
import bot.snapshots as snapshots
import bot.storage as storage
import bot.hiscores as hiscores
import bot.newsletter as newsletter
import pytest


@pytest.fixture(autouse=True)
def _isolate_fs(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data").mkdir(parents=True, exist_ok=True)
    if hasattr(newsletter, "DATA_DIR"):
        monkeypatch.setattr(newsletter, "DATA_DIR", str(tmp_path / "data"))
    elif hasattr(newsletter, "DATA_FOLDER"):
        monkeypatch.setattr(newsletter, "DATA_FOLDER", str(tmp_path / "data"))
    elif hasattr(newsletter, "DATA_PATH"):
        monkeypatch.setattr(newsletter, "DATA_PATH", str(tmp_path / "data"))


@pytest.fixture(autouse=True)
def _isolate_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


def test_compare_file_to_dict_detects_xp_delta_and_99_milestone(tmp_path):
    player = "Tester"
    data_type = "skills"
    csv_file = storage.create_data_path(player, data_type)
    os.makedirs(os.path.dirname(csv_file), exist_ok=True)

    prior = {"Attack": "13034430"}
    with open(csv_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(prior.keys()))
        writer.writeheader()
        writer.writerow(prior)

    new = {"Attack": 13034431}

    deltas, milestones = snapshots.compare_file_to_dict(new, player, data_type)
    assert deltas["Attack"] == 1
    assert ["99", "Attack"] in milestones


def test_compare_file_to_dict_detects_kc_delta_and_100_milestone(tmp_path):
    player = "Tester"
    data_type = "kc"
    csv_file = storage.create_data_path(player, data_type)
    os.makedirs(os.path.dirname(csv_file), exist_ok=True)

    prior = {"Zulrah": "199"}
    with open(csv_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(prior.keys()))
        writer.writeheader()
        writer.writerow(prior)

    new = {"Zulrah": 200}
    deltas, milestones = snapshots.compare_file_to_dict(new, player, data_type)

    assert deltas["Zulrah"] == 1
    assert ["kc", 200, "Zulrah"] in milestones


def test_write_player_info_to_csv_roundtrips_dict(tmp_path):
    player = "Tester"
    info_type = "skills"
    data = {"Attack": 123, "Strength": 456}

    snapshots.write_player_info_to_csv(data, player, info_type)
    csv_file = storage.create_data_path(player, info_type)

    path = tmp_path / csv_file
    assert path.exists()

    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 1
    assert rows[0]["Attack"] == "123"
    assert rows[0]["Strength"] == "456"


def test_check_new_info_and_update_data_compares_and_writes(monkeypatch, tmp_path):
    player = "Tester"

    snapshots.write_player_info_to_csv({"Attack": 100}, player, "skills")
    snapshots.write_player_info_to_csv({"Zulrah": 199}, player, "kc")

    def fake_get_player_info(_):
        return ({"Attack": "101"}, {"Zulrah": "200"})

    monkeypatch.setattr(hiscores, "get_player_info", fake_get_player_info)

    skill_deltas, kc_deltas, milestones = snapshots.check_new_info_and_update_data(player)

    assert skill_deltas["Attack"] == 1
    assert kc_deltas["Zulrah"] == 1
    assert ["kc", 200, "Zulrah"] in milestones

    skills_path = storage.create_data_path(player, "skills")
    kc_path = storage.create_data_path(player, "kc")

    with open(tmp_path / skills_path, newline="") as f:
        rows = list(csv.DictReader(f))
    assert rows[0]["Attack"] == "101"

    with open(tmp_path / kc_path, newline="") as f:
        rows = list(csv.DictReader(f))
    assert rows[0]["Zulrah"] == "200"
