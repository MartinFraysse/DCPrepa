import pytest

from dcprepa.services.games import add_games, delete_game, delete_match, edit_game, edit_match
from dcprepa.services.import_inbox import import_inbox
from dcprepa.storage.games import COLUMNS

HEADER_CSV = ",".join(COLUMNS) + "\n"
EXISTING = "02/10/2026,02/10/2026-01,1,paper,terra-midrange,v1,Ragavan,OTP,W,\n"
BLOCK = {
    "date": "2/10/2026",
    "source": "Paper",
    "deck": "Terra",
    "version": "v2",
    "oppo": "raga",
    "games": "OTP W, OTD L, OTP W / OTD L",
    "note/ressenti": "Bon matchup",
}


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="")


def read_raw(path):
    with path.open(encoding="utf-8", newline="") as file:
        return file.read()


@pytest.fixture
def setup(tmp_path):
    """Un mini-dépôt : data/oppos.yaml + un tournoi avec un deck (terra-midrange, alias « Terra », v1 et v2) et un BO déjà joué ce jour."""
    tournament = tmp_path / "tournaments" / "test"
    oppos = tmp_path / "oppos.yaml"
    write(oppos, "Ragavan:\n    - raga\n")
    write(tournament / "decks" / "terra-midrange.yaml", "name: Terra\nversions:\n    - version: v1\n    - version: v2\n")
    write(tournament / "games.csv", HEADER_CSV + EXISTING)
    return tournament, oppos


def test_ajout_reussi(setup):
    tournament, oppos = setup
    report = add_games(tournament, BLOCK, oppos)
    assert report.ok
    assert (report.matches, report.games, report.match_ids, report.warnings) == (2, 4, ["02/10/2026-02", "02/10/2026-03"], [])
    assert read_raw(tournament / "games.csv") == HEADER_CSV + EXISTING + (
        "02/10/2026,02/10/2026-02,1,paper,terra-midrange,v2,Ragavan,OTP,W,Bon matchup\n"
        "02/10/2026,02/10/2026-02,2,paper,terra-midrange,v2,Ragavan,OTD,L,Bon matchup\n"
        "02/10/2026,02/10/2026-02,3,paper,terra-midrange,v2,Ragavan,OTP,W,Bon matchup\n"
        "02/10/2026,02/10/2026-03,1,paper,terra-midrange,v2,Ragavan,OTD,L,Bon matchup\n"
    )


def test_deux_saisies_continuent_la_numerotation(setup):
    tournament, oppos = setup
    add_games(tournament, BLOCK, oppos)
    report = add_games(tournament, {**BLOCK, "games": "OTP W"}, oppos)
    assert report.match_ids == ["02/10/2026-04"]


@pytest.mark.parametrize(
    "field, value",
    [("version", "v9"), ("deck", "atraxa"), ("games", "OTP X"), ("date", "31/02/2026"), ("source", "arena")],
)
def test_bloc_invalide_rien_n_est_ecrit(setup, field, value):
    tournament, oppos = setup
    before = read_raw(tournament / "games.csv")
    report = add_games(tournament, {**BLOCK, field: value}, oppos)
    assert not report.ok
    assert report.errors
    assert (report.matches, report.games, report.match_ids) == (0, 0, [])
    assert read_raw(tournament / "games.csv") == before


def test_memes_erreurs_que_l_import(setup):
    """Les messages viennent de prepare_block, comme pour l'import (sans le préfixe « bloc N : »)."""
    tournament, oppos = setup
    write(tournament / "inbox.yaml", "".join(f"{key}: {value}\n" for key, value in {**BLOCK, "version": "v9"}.items()))
    expected = [message.removeprefix("bloc 1 : ") for message in import_inbox(tournament, oppos).errors]
    assert add_games(tournament, {**BLOCK, "version": "v9"}, oppos).errors == expected


def test_oppo_inconnu_avertissement(setup):
    tournament, oppos = setup
    report = add_games(tournament, {**BLOCK, "oppo": "Ragavn"}, oppos)
    assert report.ok
    assert len(report.warnings) == 1 and "Ragavn" in report.warnings[0]
    assert ",Ragavn,OTP,W," in read_raw(tournament / "games.csv")


def test_self_play(setup):
    tournament, oppos = setup
    report = add_games(tournament, {**BLOCK, "oppo": "Terra@v1", "games": "OTP W"}, oppos)
    assert report.ok and report.warnings == []
    assert ",terra-midrange@v1,OTP,W," in read_raw(tournament / "games.csv")


def test_references_invalides_rien_n_est_ecrit(setup):
    tournament, oppos = setup
    write(oppos, "Ragavan:\n    - raga\nKess:\n    - raga\n")
    before = read_raw(tournament / "games.csv")
    report = add_games(tournament, BLOCK, oppos)
    assert report.errors == ["oppos.yaml : « raga » renvoie à la fois vers Ragavan et Kess"]
    assert read_raw(tournament / "games.csv") == before


BO3 = (
    "02/10/2026,02/10/2026-02,1,paper,terra-midrange,v1,Ragavan,OTP,W,\"bien, vraiment\"\n"
    "02/10/2026,02/10/2026-02,2,paper,terra-midrange,v1,Ragavan,OTD,L,\n"
    "02/10/2026,02/10/2026-02,3,paper,terra-midrange,v1,Ragavan,OTP,W,\n"
)


@pytest.fixture
def played(setup):
    """Le mini-tournoi avec un BO3 2-1 (02/10/2026-02) après le BO1 existant."""
    tournament, oppos = setup
    write(tournament / "games.csv", HEADER_CSV + EXISTING + BO3)
    return tournament, oppos


def test_edit_game_reecrit_seulement_le_bo(played):
    tournament, oppos = played
    report = edit_game(tournament, "02/10/2026-02", "3", {"resultat": "L"}, oppos)
    assert report.ok
    assert (report.matches, report.games, report.match_ids) == (1, 3, ["02/10/2026-02"])
    assert read_raw(tournament / "games.csv") == HEADER_CSV + EXISTING + (
        "02/10/2026,02/10/2026-02,1,paper,terra-midrange,v1,Ragavan,OTP,W,\"bien, vraiment\"\n"
        "02/10/2026,02/10/2026-02,2,paper,terra-midrange,v1,Ragavan,OTD,L,\n"
        "02/10/2026,02/10/2026-02,3,paper,terra-midrange,v1,Ragavan,OTP,L,\n"
    )


def test_edit_match_date(played):
    tournament, oppos = played
    report = edit_match(tournament, "02/10/2026-02", {"date": "03/10/2026", "oppo": "raga"}, oppos)
    assert report.match_ids == ["03/10/2026-01"]
    content = read_raw(tournament / "games.csv")
    assert "02/10/2026-02" not in content
    assert content.count("03/10/2026,03/10/2026-01,") == 3


def test_correction_refusee_rien_n_est_ecrit(played):
    tournament, oppos = played
    before = read_raw(tournament / "games.csv")
    assert edit_game(tournament, "02/10/2026-02", "2", {"resultat": "W"}, oppos).errors == [
        "02/10/2026-02 : game 3 : en trop, BO déjà terminé (2-0)"
    ]
    assert edit_match(tournament, "02/10/2026-02", {"version": "v9"}, oppos).errors
    assert delete_game(tournament, "02/10/2026-09", "1").errors == ["BO inconnu : 02/10/2026-09"]
    assert read_raw(tournament / "games.csv") == before


def test_delete_game_et_delete_match(played):
    tournament, _ = played
    report = delete_game(tournament, "02/10/2026-02", "1")
    assert (report.ok, report.games, report.warnings) == (True, 2, [])
    assert ",02/10/2026-02,1,paper,terra-midrange,v1,Ragavan,OTD,L," in read_raw(tournament / "games.csv")
    report = delete_match(tournament, "02/10/2026-02")
    assert (report.ok, report.matches, report.match_ids) == (True, 0, [])
    assert read_raw(tournament / "games.csv") == HEADER_CSV + EXISTING


def test_fins_de_ligne_crlf_gardees(played):
    tournament, oppos = played
    write(tournament / "games.csv", (HEADER_CSV + EXISTING + BO3).replace("\n", "\r\n"))
    edit_game(tournament, "02/10/2026-02", "3", {"resultat": "L"}, oppos)
    content = read_raw(tournament / "games.csv")
    assert content.count("\r\n") == 5 and "\n" not in content.replace("\r\n", "")


def test_games_csv_invalide(played):
    tournament, oppos = played
    write(tournament / "games.csv", HEADER_CSV + EXISTING.replace(",OTP,", ",OTX,"))
    report = edit_game(tournament, "02/10/2026-01", "1", {"resultat": "L"}, oppos)
    assert report.errors == ["games.csv : ligne 2 : position inconnue (OTP ou OTD) : OTX"]


def test_add_games_refuse_un_games_csv_invalide(setup):
    """Une ligne cassée dans games.csv : rien n'est ajouté (les stats refuseraient le fichier ensuite)."""
    tournament, oppos = setup
    write(tournament / "games.csv", HEADER_CSV + EXISTING.replace(",OTP,", ",OTX,"))
    before = read_raw(tournament / "games.csv")
    report = add_games(tournament, BLOCK, oppos)
    assert report.errors == ["games.csv : ligne 2 : position inconnue (OTP ou OTD) : OTX"]
    assert read_raw(tournament / "games.csv") == before
