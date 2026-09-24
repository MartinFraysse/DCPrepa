import pytest

from dcprepa.domain.matches import GameLine, date_key, group_matches


def row(match_id, game, position, resultat, *, date=None, oppo="Ragavan", note=""):
    return {
        "date": date or match_id.split("-")[0], "match_id": match_id, "game": str(game), "source": "paper",
        "deck": "terra", "version": "v1", "oppo": oppo, "position": position, "resultat": resultat, "note/ressenti": note,
    }


def test_regroupement_et_ordre():
    games = [
        row("01/10/2026-01", 2, "OTD", "L"), row("01/10/2026-01", 1, "OTP", "W", note="bien"), row("01/10/2026-01", 3, "OTP", "W"),
        row("02/10/2026-01", 1, "OTP", "L", oppo="Kess"),
        row("01/10/2026-02", 1, "OTD", "W"), row("01/10/2026-02", 2, "OTP", "L"),
        row("30/09/2026-10", 1, "OTP", "W"),
    ]
    matches = group_matches(games)
    assert [m.match_id for m in matches] == ["02/10/2026-01", "01/10/2026-02", "01/10/2026-01", "30/09/2026-10"]
    bo3 = matches[2]
    assert bo3.games == [GameLine("1", "OTP", "W", "bien"), GameLine("2", "OTD", "L", ""), GameLine("3", "OTP", "W", "")]
    assert (bo3.is_bo3, bo3.score, bo3.outcome) == (True, "2-1", "W")
    assert (matches[0].is_bo3, matches[0].score, matches[0].outcome, matches[0].oppo) == (False, "0-1", "L", "Kess")
    assert (matches[1].score, matches[1].outcome) == ("1-1", "nul")


def test_numero_de_bo_trie_comme_un_nombre():
    games = [row(f"01/10/2026-{n:02d}", 1, "OTP", "W") for n in (2, 10, 1)]
    assert [m.match_id for m in group_matches(games)] == ["01/10/2026-10", "01/10/2026-02", "01/10/2026-01"]


def test_bo3_perdu_et_vide():
    lost = group_matches([row("01/10/2026-01", 1, "OTP", "L"), row("01/10/2026-01", 2, "OTD", "L")])[0]
    assert (lost.score, lost.outcome) == ("0-2", "L")
    assert group_matches([]) == []


@pytest.mark.parametrize(
    "date, expected",
    [("05/10/2026", (2026, 10, 5)), ("", (0, 0, 0)), ("2026-10-05", (0, 0, 0))],
)
def test_date_key(date, expected):
    assert date_key(date) == expected
    assert date_key("", unreadable=(9999, 99, 99)) == (9999, 99, 99)
