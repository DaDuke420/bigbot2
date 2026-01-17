import bot.newsletter as newsletter
import bot.config as config
import bot.snapshots as snapshots
import pytest


@pytest.fixture(autouse=True)
def _isolate_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


def test_format_player_xp_and_kc_updates_to_email_handles_empty():
    out = newsletter.format_player_xp_and_kc_updates_to_email({}, {}, [], "DaDuke42069")
    assert "has not played" in out


def test_format_player_xp_and_kc_updates_to_email_includes_milestones_and_updates():
    xp = {"Attack": 1234}
    kc = {"Zulrah": 5}
    milestones = [["99", "Attack"], ["kc", 100, "Zulrah"]]

    out = newsletter.format_player_xp_and_kc_updates_to_email(xp, kc, milestones, "Mike")
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
    email = newsletter.create_email_string(updates)
    assert "DaKings GIM Newsletter" in email
    assert "A\n" in email
    assert "B\n" in email


def test_generate_newsletter_smoke(monkeypatch):
    monkeypatch.setattr(config, "GIM_MEMBERS", ["P1", "P2"])
    monkeypatch.setattr(config, "NEWSLETTER_MEMBERS", ["P1", "P2"])

    def fake_check(player):
        if player == "P1":
            return ({"Attack": 10}, {"Zulrah": 1}, [])
        return ({}, {}, [])

    monkeypatch.setattr(snapshots, "check_new_info_and_update_data", fake_check)

    email = newsletter.generate_newsletter()
    assert "P1" in email
    assert "Attack: 10 xp" in email
    assert "Zulrah: 1 new kc" in email
    assert "P2 has not played" in email
