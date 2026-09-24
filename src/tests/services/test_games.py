import pytest

from dcprepa.services.games import add_games
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
