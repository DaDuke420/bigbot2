import bot.storage as storage


def test_create_data_path_returns_reasonable_string():
    p = storage.create_data_path("Tester", "skills")
    assert isinstance(p, str)
    assert "Tester" in p
    assert "skills" in p
    assert p.lower().endswith(".csv")
