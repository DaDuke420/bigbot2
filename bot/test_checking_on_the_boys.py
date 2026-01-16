# test_checking_on_the_boys.py

import os
import csv
import types
import importlib
from datetime import date

import pytest

import checking_on_the_boys as bot


class FakeResponse:
    """Mimics requests.Response enough for unpack_info()."""

    def __init__(self, lines, status_code=200):
        self._lines = lines
        self.status_code = status_code

    def iter_lines(self):
        # requests.Response.iter_lines yields bytes
        for line in self._lines:
            yield line

@pytest.fixture(autouse=True)
def _isolate_fs(tmp_path, monkeypatch):
    """
    Force all filesystem writes into a temp directory, including the new data/ folder.
    """
    monkeypatch.chdir(tmp_path)

    # Create a data folder in the temp dir
    (tmp_path / "data").mkdir(parents=True, exist_ok=True)

    # If the module has a configurable data dir constant, patch it:
    if hasattr(bot, "DATA_DIR"):
        monkeypatch.setattr(bot, "DATA_DIR", str(tmp_path / "data"))
    elif hasattr(bot, "DATA_FOLDER"):
        monkeypatch.setattr(bot, "DATA_FOLDER", str(tmp_path / "data"))
    elif hasattr(bot, "DATA_PATH"):
        monkeypatch.setattr(bot, "DATA_PATH", str(tmp_path / "data"))

def _skill_line(rank=1, level=99, xp=0):
    # unpack_info does: str(skill).split(',')[2].strip("'")
    # so we need bytes that stringify to "b'..., ..., ...'"
    return f"{rank},{level},{xp}".encode("utf-8")


def _kc_line(identifier=0, kc=0):
    # unpack_info does: kc_info = str(skill).split(',')
    # and reads kc_info[0] (identifier) and kc_info[1] (kc)
    return f"{identifier},{kc}".encode("utf-8")


@pytest.fixture(autouse=True)
def _isolate_cwd(tmp_path, monkeypatch):
    """The module reads/writes CSVs in CWD. Keep tests isolated."""
    monkeypatch.chdir(tmp_path)


def test_unpack_info_parses_skills_and_kc_mapping_row_32():
    # Build 0..24 (skills) => 25 lines
    skill_lines = [_skill_line(xp=1000 + i) for i in range(25)]

    # Rows 25..31 are "kc section" but not mapped to kc_mapping.
    # Use identifier "-1" so they are skipped.
    filler_kc = [_kc_line(identifier=-1, kc=0) for _ in range(7)]

    # Row 32 should map to "Total Clues"
    row_32 = _kc_line(identifier=0, kc=562)

    # Add one more mapped row (33 => Beginner Clues) to ensure multiple
    row_33 = _kc_line(identifier=0, kc=100)

    response = FakeResponse(skill_lines + filler_kc + [row_32, row_33])

    xp, kc = bot.unpack_info(response)

    # Skills: first 25 should be present (by skill_row_order index)
    assert xp["Total"] == "1000"
    assert xp[bot.skill_row_order[24]] == str(1000 + 24)

    # KC: rows 32 and 33 should map correctly
    assert kc["Total Clues"] == "562"
    assert kc["Beginner Clues"] == "100"


def test_compare_file_to_dict_detects_xp_delta_and_99_milestone(tmp_path):
    # Craft a prior file with Attack just below 99 xp threshold
    player = "Tester"
    data_type = "skills"
    csv_file = bot.create_data_path(player, data_type)
    os.makedirs(os.path.dirname(csv_file), exist_ok=True)

    prior = {"Attack": "13034430"}  # one below 13,034,431
    with open(csv_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(prior.keys()))
        writer.writeheader()
        writer.writerow(prior)

    # New info crosses the threshold => should produce a "99" milestone
    new = {"Attack": 13034431}

    deltas, milestones = bot.compare_file_to_dict(new, player, data_type)
    assert deltas["Attack"] == 1
    assert ["99", "Attack"] in milestones


def test_compare_file_to_dict_detects_kc_delta_and_100_milestone(tmp_path):
    player = "Tester"
    data_type = "kc"
    csv_file = bot.create_data_path(player, data_type)
    os.makedirs(os.path.dirname(csv_file), exist_ok=True)

    prior = {"Zulrah": "199"}
    with open(csv_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(prior.keys()))
        writer.writeheader()
        writer.writerow(prior)

    new = {"Zulrah": 200}
    deltas, milestones = bot.compare_file_to_dict(new, player, data_type)

    assert deltas["Zulrah"] == 1
    assert ["kc", 200, "Zulrah"] in milestones


def test_write_player_info_to_csv_roundtrips_dict(tmp_path):
    player = "Tester"
    info_type = "skills"
    data = {"Attack": 123, "Strength": 456}

    bot.write_player_info_to_csv(data, player, info_type)
    
    csv_file = bot.create_data_path(player, info_type)

    path = tmp_path / csv_file
    assert path.exists()

    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 1
    assert rows[0]["Attack"] == "123"
    assert rows[0]["Strength"] == "456"


def test_format_player_xp_and_kc_updates_to_email_handles_empty():
    out = bot.format_player_xp_and_kc_updates_to_email({}, {}, [], "DaDuke42069")
    assert "has not played" in out


def test_format_player_xp_and_kc_updates_to_email_includes_milestones_and_updates():
    xp = {"Attack": 1234}
    kc = {"Zulrah": 5}
    milestones = [["99", "Attack"], ["kc", 100, "Zulrah"]]

    out = bot.format_player_xp_and_kc_updates_to_email(xp, kc, milestones, "Mike")
    assert "We have milestones to acknowledge" in out
    assert "has achieved 99 Attack" in out
    assert "has surpassed 100 Zulrah kc" in out
    assert "Attack: 1234 xp" in out
    assert "Zulrah: 5 new kc" in out


def test_create_email_string_includes_each_player_block():
    updates = {
        "A": [{"Attack": 1}, {}, []],
        "B": [{}, {"Zulrah": 2}, []],
    }
    email = bot.create_email_string(updates)
    assert "DaKings GIM Newsletter" in email
    assert "A\n" in email
    assert "B\n" in email


def test_check_new_info_and_update_data_compares_and_writes(monkeypatch, tmp_path):
    player = "Tester"

    # Seed existing CSVs
    bot.write_player_info_to_csv({"Attack": 100}, player, "skills")
    bot.write_player_info_to_csv({"Zulrah": 199}, player, "kc")

    # Fake fresh hiscore pull
    def fake_get_player_info(_):
        return ({"Attack": "101"}, {"Zulrah": "200"})

    monkeypatch.setattr(bot, "get_player_info", fake_get_player_info)

    skill_deltas, kc_deltas, milestones = bot.check_new_info_and_update_data(player)

    assert skill_deltas["Attack"] == 1
    assert kc_deltas["Zulrah"] == 1
    assert ["kc", 200, "Zulrah"] in milestones

    # Ensure it wrote the new values back
    
    skills_path = bot.create_data_path(player, "skills")
    kc_path = bot.create_data_path(player, "kc")
    
    with open(tmp_path / skills_path, newline="") as f:
        rows = list(csv.DictReader(f))
    assert rows[0]["Attack"] == "101"

    with open(tmp_path / kc_path, newline="") as f:
        rows = list(csv.DictReader(f))
    assert rows[0]["Zulrah"] == "200"


def test_generate_newsletter_smoke(monkeypatch):
    # Keep newsletter small and deterministic
    monkeypatch.setattr(bot, "gim_members", ["P1", "P2"])
    monkeypatch.setattr(bot, "newsletter_members", ["P1", "P2"])

    def fake_check(player):
        if player == "P1":
            return ({"Attack": 10}, {"Zulrah": 1}, [])
        return ({}, {}, [])

    monkeypatch.setattr(bot, "check_new_info_and_update_data", fake_check)

    email = bot.generate_newsletter()
    assert "P1" in email
    assert "Attack: 10 xp" in email
    assert "Zulrah: 1 new kc" in email
    assert "P2 has not played" in email