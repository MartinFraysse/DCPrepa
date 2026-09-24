import pytest

from dcprepa.domain.edits import References, delete_game, delete_match, edit_game, edit_match

REFS = References(
    decks={"terra-midrange": ["v1", "v2"]},
    deck_index={"terra-midrange": "terra-midrange", "terra": "terra-midrange"},
    oppo_index={"ragavan": "Ragavan", "raga": "Ragavan", "kess": "Kess"},
)


def row(match_id, game, position, resultat, *, date="02/10/2026", version="v1", oppo="Ragavan", note=""):
    return {
        "date": date, "match_id": match_id, "game": str(game), "source": "paper", "deck": "terra-midrange",
        "version": version, "oppo": oppo, "position": position, "resultat": resultat, "note/ressenti": note,
    }


@pytest.fixture
def games():
    """Trois BO du 02/10 : un BO3 2-1 (notes différentes par game), un BO1, un BO3 2-0."""
    return [
        row("02/10/2026-01", 1, "OTP", "W", note="bien"),
        row("02/10/2026-01", 2, "OTD", "L", note="mull à 5"),
        row("02/10/2026-01", 3, "OTP", "W"),
        row("02/10/2026-02", 1, "OTD", "L", oppo="Kess"),
        row("02/10/2026-03", 1, "OTP", "W"),
        row("02/10/2026-03", 2, "OTD", "W"),
    ]


def summary(result):
    return [(g["match_id"], g["game"], g["position"], g["resultat"], g["oppo"], g["note/ressenti"]) for g in result.games]


def test_edit_game_resultat(games):
    result = edit_game(games, "02/10/2026-01", "3", {"resultat": "L"}, REFS)
    assert (result.errors, result.match_id, result.changed) == ([], "02/10/2026-01", 3)
    assert summary(result)[:3] == [
        ("02/10/2026-01", "1", "OTP", "W", "Ragavan", "bien"),
        ("02/10/2026-01", "2", "OTD", "L", "Ragavan", "mull à 5"),
        ("02/10/2026-01", "3", "OTP", "L", "Ragavan", ""),
    ]
    assert result.games[3:] == games[3:]


def test_edit_game_perdue_devient_gagnee(games):
    result = edit_game(games, "02/10/2026-02", "1", {"resultat": "W"}, REFS)
    assert (result.errors, result.match_id, result.changed) == ([], "02/10/2026-02", 1)
    assert summary(result)[3] == ("02/10/2026-02", "1", "OTD", "W", "Kess", "")
    assert result.games[:3] == games[:3] and result.games[4:] == games[4:]


def test_edit_game_bo_impossible(games):
    """W L W → W W W : le BO est gagné 2-0 après la game 2, la game 3 n'a pas pu être jouée."""
    result = edit_game(games, "02/10/2026-01", "2", {"resultat": "W"}, REFS)
    assert result.errors == ["02/10/2026-01 : game 3 : en trop, BO déjà terminé (2-0)"]
    assert result.games == []


def test_edit_game_position_et_note(games):
    result = edit_game(games, "02/10/2026-01", "3", {"position": "OTD", "note/ressenti": "  top  deck  "}, REFS)
    assert summary(result)[2] == ("02/10/2026-01", "3", "OTD", "W", "Ragavan", "top deck")


@pytest.mark.parametrize(
    "match_id, number, changes, error",
    [
        ("02/10/2026-09", "1", {"resultat": "W"}, "BO inconnu : 02/10/2026-09"),
        ("02/10/2026-01", "4", {"resultat": "W"}, "game inconnue : 02/10/2026-01 game 4 (le BO a 3 game(s))"),
        ("02/10/2026-01", "1", {}, "rien à modifier"),
        ("02/10/2026-01", "1", {"oppo": "Kess"}, "champ non modifiable ici : oppo (possibles : position, resultat, note/ressenti)"),
    ],
)
def test_edit_game_refuse(games, match_id, number, changes, error):
    result = edit_game(games, match_id, number, changes, REFS)
    assert result.errors == [error] and result.games == []


def test_edit_game_valeur_invalide(games):
    result = edit_game(games, "02/10/2026-01", "1", {"resultat": "X"}, REFS)
    assert result.errors and result.games == []


def test_edit_match_oppo_normalise(games):
    result = edit_match(games, "02/10/2026-01", {"oppo": "kess"}, REFS)
    assert result.errors == []
    assert {g["oppo"] for g in result.games[:3]} == {"Kess"}
    assert [g["note/ressenti"] for g in result.games[:3]] == ["bien", "mull à 5", ""]


def test_edit_match_date_nouveau_match_id(games):
    others = [row("03/10/2026-01", 1, "OTP", "L", date="03/10/2026")]
    result = edit_match(games + others, "02/10/2026-02", {"date": "3/10/2026"}, REFS)
    assert result.match_id == "03/10/2026-02"
    assert summary(result)[3] == ("03/10/2026-02", "1", "OTD", "L", "Kess", "")
    assert result.games[3]["date"] == "03/10/2026"


def test_edit_match_meme_date_ecrite_autrement(games):
    result = edit_match(games, "02/10/2026-01", {"date": "2/10/2026", "version": "v2"}, REFS)
    assert result.match_id == "02/10/2026-01"
    assert {g["version"] for g in result.games[:3]} == {"v2"}


def test_edit_match_version_inconnue(games):
    result = edit_match(games, "02/10/2026-01", {"version": "v9"}, REFS)
    assert result.errors == ["version inconnue pour terra-midrange : v9"] and result.games == []


def test_edit_match_oppo_inconnu_avertissement(games):
    result = edit_match(games, "02/10/2026-01", {"oppo": "Atraxa"}, REFS)
    assert result.errors == [] and len(result.warnings) == 1


def test_delete_game_renumerote(games):
    result = delete_game(games, "02/10/2026-01", "2")
    assert (result.match_id, result.changed, result.warnings) == ("02/10/2026-01", 2, [])
    assert summary(result)[:2] == [
        ("02/10/2026-01", "1", "OTP", "W", "Ragavan", "bien"),
        ("02/10/2026-01", "2", "OTP", "W", "Ragavan", ""),
    ]
    assert len(result.games) == 5


def test_delete_game_bo3_devient_bo1(games):
    result = delete_game(games, "02/10/2026-03", "1")
    assert result.warnings == ["02/10/2026-03 : une seule game restante, le BO devient un BO1 (hors winrate BO3)"]
    assert summary(result)[-1] == ("02/10/2026-03", "1", "OTD", "W", "Ragavan", "")


def test_delete_game_derniere_game(games):
    result = delete_game(games, "02/10/2026-02", "1")
    assert (result.match_id, result.changed, result.warnings) == (None, 0, [])
    assert all(g["match_id"] != "02/10/2026-02" for g in result.games)


def test_delete_match(games):
    result = delete_match(games, "02/10/2026-01")
    assert result.games == games[3:]
    assert delete_match(games, "01/01/2026-01").errors == ["BO inconnu : 01/01/2026-01"]


def test_ordre_du_fichier_garde(games):
    result = edit_match(games, "02/10/2026-02", {"oppo": "raga"}, REFS)
    assert [g["match_id"] for g in result.games] == [g["match_id"] for g in games]
