import bot.hiscores as hiscores
import bot.newsletter as newsletter
import bot.config as config
import pytest


class FakeResponse:
    """Mimics requests.Response enough for unpack_info()."""

    def __init__(self, lines, status_code=200):
        self._lines = lines
        self.status_code = status_code

    def iter_lines(self):
        for line in self._lines:
            yield line


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


def _skill_line(rank=1, level=99, xp=0):
    return f"{rank},{level},{xp}".encode("utf-8")


def _kc_line(identifier=0, kc=0):
    return f"{identifier},{kc}".encode("utf-8")


@pytest.fixture(autouse=True)
def _isolate_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


def test_unpack_info_parses_skills_and_kc_mapping_row_32():
    skill_lines = [_skill_line(xp=1000 + i) for i in range(25)]
    filler_kc = [_kc_line(identifier=-1, kc=0) for _ in range(7)]
    row_32 = _kc_line(identifier=0, kc=562)
    row_33 = _kc_line(identifier=0, kc=100)

    response = FakeResponse(skill_lines + filler_kc + [row_32, row_33])

    xp, kc = hiscores.unpack_info(response)

    assert xp["Total"] == "1000"
    assert xp[config.SKILL_ROW_ORDER[24]] == str(1000 + 24)

    assert kc["Total Clues"] == "562"
    assert kc["Beginner Clues"] == "100"
