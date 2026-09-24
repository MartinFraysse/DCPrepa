import shutil
from pathlib import Path

import pytest

from dcprepa.services.import_inbox import import_inbox
from dcprepa.storage.games import COLUMNS

DATA_DIR = Path(__file__).resolve().parents[3] / "data"
HEADER_CSV = ",".join(COLUMNS) + "\n"
INBOX_HEADER = "# Boîte de réception\n# un bloc par session\n\n"

BLOCK_1 = (
    "date: 02/10/2026\n"
    "source: paper\n"
    "deck: terra-midrange\n"
    "version: v1\n"
    "oppo: raga\n"
    "games: OTP W, OTD W / OTD L\n"
    "note/ressenti: Matchup jouable\n"
)
BLOCK_2 = (
    "date: 02/10/2026\n"
    "source: mtgo\n"
    "deck: terra-midrange\n"
    "version: v2\n"
    "oppo: Atraxa\n"
    "games: OTD L, OTP W, OTD W\n"
)
EXPECTED_ROWS = (
    "02/10/2026,02/10/2026-01,1,paper,terra-midrange,v1,Ragavan,OTP,W,Matchup jouable\n"
    "02/10/2026,02/10/2026-01,2,paper,terra-midrange,v1,Ragavan,OTD,W,Matchup jouable\n"
    "02/10/2026,02/10/2026-02,1,paper,terra-midrange,v1,Ragavan,OTD,L,Matchup jouable\n"
    "02/10/2026,02/10/2026-03,1,mtgo,terra-midrange,v2,Atraxa,OTD,L,\n"
    "02/10/2026,02/10/2026-03,2,mtgo,terra-midrange,v2,Atraxa,OTP,W,\n"
    "02/10/2026,02/10/2026-03,3,mtgo,terra-midrange,v2,Atraxa,OTD,W,\n"
)


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="")


def read_raw(path):
    with path.open(encoding="utf-8", newline="") as file:
        return file.read()


@pytest.fixture
def setup(tmp_path):
    """Un mini-dépôt : data/oppos.yaml + un tournoi avec un deck (v1, v2), games.csv et inbox.yaml."""
    tournament = tmp_path / "tournaments" / "test"
    oppos = tmp_path / "oppos.yaml"
    write(oppos, "Ragavan:\n    - raga\n")
    write(tournament / "decks" / "terra-midrange.yaml", "versions:\n    - version: v1\n    - version: v2\n")
    write(tournament / "games.csv", HEADER_CSV)
    write(tournament / "inbox.yaml", INBOX_HEADER + BLOCK_1 + "---\n" + BLOCK_2)
    return tournament, oppos


def snapshot(tournament):
    return read_raw(tournament / "inbox.yaml"), read_raw(tournament / "games.csv")


def test_import_reussi(setup):
    tournament, oppos = setup
    report = import_inbox(tournament, oppos)
    assert report.ok
    assert (report.blocks, report.matches, report.games) == (2, 3, 6)
    assert report.warnings == ["bloc 2 : oppo inconnu : Atraxa → à ajouter dans data/oppos.yaml"]
    assert read_raw(tournament / "games.csv") == HEADER_CSV + EXPECTED_ROWS
    assert read_raw(tournament / "inbox.yaml") == INBOX_HEADER


def test_second_import_continue_la_numerotation(setup):
    tournament, oppos = setup
    import_inbox(tournament, oppos)
    write(tournament / "inbox.yaml", INBOX_HEADER + BLOCK_1)
    report = import_inbox(tournament, oppos)
    assert report.ok
    lines = read_raw(tournament / "games.csv").splitlines()
    assert [line.split(",")[1] for line in lines[-3:]] == ["02/10/2026-04", "02/10/2026-04", "02/10/2026-05"]


def test_un_bloc_invalide_rien_n_est_importe(setup):
    tournament, oppos = setup
    write(tournament / "inbox.yaml", INBOX_HEADER + BLOCK_1 + "---\n" + BLOCK_2.replace("v2", "v9"))
    before = snapshot(tournament)
    report = import_inbox(tournament, oppos)
    assert not report.ok
    assert report.errors == ["bloc 2 : version inconnue pour terra-midrange : v9"]
    assert (report.blocks, report.matches, report.games) == (0, 0, 0)
    assert snapshot(tournament) == before


def test_toutes_les_erreurs_de_tous_les_blocs(setup):
    tournament, oppos = setup
    bad_1 = BLOCK_1.replace("paper", "arena")
    bad_2 = BLOCK_2.replace("OTD L, OTP W, OTD W", "OTP W, OTD W, OTP L")
    write(tournament / "inbox.yaml", INBOX_HEADER + bad_1 + "---\n" + bad_2)
    before = snapshot(tournament)
    report = import_inbox(tournament, oppos)
    assert report.errors == [
        "bloc 1 : source inconnue (paper, mtgo ou cockatrice) : arena",
        "bloc 2 : games : BO 1 : game 3 : en trop, BO déjà terminé (2-0)",
    ]
    assert snapshot(tournament) == before


def test_bloc_yaml_illisible_rien_n_est_importe(setup):
    tournament, oppos = setup
    write(tournament / "inbox.yaml", INBOX_HEADER + BLOCK_1 + "---\nnote: a: b\n")
    before = snapshot(tournament)
    report = import_inbox(tournament, oppos)
    assert len(report.errors) == 1
    assert report.errors[0].startswith("bloc 2 : YAML illisible")
    assert snapshot(tournament) == before


def test_inbox_vide_rien_ne_change(setup):
    tournament, oppos = setup
    write(tournament / "inbox.yaml", INBOX_HEADER)
    before = snapshot(tournament)
    report = import_inbox(tournament, oppos)
    assert report.ok
    assert (report.blocks, report.games) == (0, 0)
    assert snapshot(tournament) == before


@pytest.mark.parametrize(
    "broken, message_start",
    [
        ("games.csv", "fichier introuvable"),
        ("oppos.yaml", "fichier introuvable"),
        ("inbox.yaml", "fichier introuvable"),
    ],
)
def test_fichier_manquant_rien_n_est_ecrit(setup, broken, message_start):
    tournament, oppos = setup
    target = oppos if broken == "oppos.yaml" else tournament / broken
    target.unlink()
    files = {path: read_raw(path) for path in tournament.rglob("*") if path.is_file()}
    report = import_inbox(tournament, oppos)
    assert not report.ok
    assert report.errors[0].startswith(message_start)
    assert {path: read_raw(path) for path in tournament.rglob("*") if path.is_file()} == files


def test_oppos_ambigu_bloque(setup):
    tournament, oppos = setup
    write(oppos, "Ragavan:\n    - raga\nKess:\n    - raga\n")
    before = snapshot(tournament)
    report = import_inbox(tournament, oppos)
    assert report.errors == ["oppos.yaml : « raga » renvoie à la fois vers Ragavan et Kess"]
    assert snapshot(tournament) == before


def test_self_play_sans_avertissement(setup):
    tournament, oppos = setup
    write(tournament / "inbox.yaml", BLOCK_1.replace("oppo: raga", "oppo: terra-midrange@v2"))
    report = import_inbox(tournament, oppos)
    assert report.ok
    assert report.warnings == []
    assert ",terra-midrange@v2,OTP,W," in read_raw(tournament / "games.csv")


def test_avec_le_vrai_modele_de_tournoi(tmp_path):
    tournament = tmp_path / "mon-tournoi"
    shutil.copytree(DATA_DIR / "templates" / "tournament", tournament)
    shutil.copy(tournament / "decks" / "_modele.yaml", tournament / "decks" / "terra-midrange.yaml")
    header = read_raw(tournament / "inbox.yaml")
    newline = "\r\n" if "\r\n" in header else "\n"
    write(tournament / "inbox.yaml", header + BLOCK_1.replace("\n", newline))
    oppos = tmp_path / "oppos.yaml"
    shutil.copy(DATA_DIR / "oppos.yaml", oppos)

    report = import_inbox(tournament, oppos)
    assert report.ok, report.errors
    assert (report.blocks, report.matches, report.games) == (1, 2, 3)
    assert read_raw(tournament / "inbox.yaml") == header
    assert read_raw(tournament / "games.csv").count("02/10/2026-0") == 3


@pytest.mark.parametrize("deck", ["terra-midrange", "Terra Midrange", "terra", "  TERRA  mid "])
def test_deck_saisi_par_fichier_name_ou_alias(setup, deck):
    tournament, oppos = setup
    write(tournament / "decks" / "terra-midrange.yaml", "name: Terra Midrange\nversions:\n    - version: v1\n")
    write(tournament / "decks" / "_alias.yaml", "terra-midrange:\n    - Terra\n    - Terra mid\n")
    write(tournament / "inbox.yaml", BLOCK_1.replace("deck: terra-midrange", f"deck: {deck}"))
    report = import_inbox(tournament, oppos)
    assert report.ok, report.errors
    assert all(line.split(",")[4] == "terra-midrange" for line in read_raw(tournament / "games.csv").splitlines()[1:])


def test_deck_inconnu_liste_les_decks(setup):
    tournament, oppos = setup
    write(tournament / "inbox.yaml", BLOCK_1.replace("deck: terra-midrange", "deck: test_deck"))
    before = snapshot(tournament)
    report = import_inbox(tournament, oppos)
    assert report.errors == ["bloc 1 : deck inconnu : test_deck (decks disponibles : terra-midrange)"]
    assert snapshot(tournament) == before


def test_self_play_par_alias(setup):
    tournament, oppos = setup
    write(tournament / "decks" / "_alias.yaml", "terra-midrange:\n    - Terra mid\n")
    write(tournament / "inbox.yaml", BLOCK_1.replace("oppo: raga", "oppo: terra mid@v2"))
    report = import_inbox(tournament, oppos)
    assert report.ok and report.warnings == []
    assert ",terra-midrange@v2,OTP,W," in read_raw(tournament / "games.csv")


def test_self_play_deck_inconnu_avertissement(setup):
    tournament, oppos = setup
    write(tournament / "inbox.yaml", BLOCK_1.replace("oppo: raga", "oppo: atraxa@v1"))
    report = import_inbox(tournament, oppos)
    assert report.ok
    assert report.warnings == ["bloc 1 : self-play : deck inconnu : atraxa"]


@pytest.mark.parametrize(
    "alias, message",
    [
        ("terra:\n    - Terra mid\n", "_alias.yaml : deck inconnu : terra (decks disponibles : terra-midrange)"),
        ("terra-midrange: Terra\n", "_alias.yaml : terra-midrange : variantes attendues sous forme de liste (« - variante »)"),
    ],
)
def test_alias_invalide_bloque(setup, alias, message):
    tournament, oppos = setup
    write(tournament / "decks" / "_alias.yaml", alias)
    before = snapshot(tournament)
    report = import_inbox(tournament, oppos)
    assert report.errors == [message]
    assert snapshot(tournament) == before


def test_alias_ambigu_bloque(setup):
    tournament, oppos = setup
    write(tournament / "decks" / "terra-mono.yaml", "versions:\n    - version: v1\n")
    write(tournament / "decks" / "_alias.yaml", "terra-midrange:\n    - Terra\nterra-mono:\n    - terra\n")
    before = snapshot(tournament)
    report = import_inbox(tournament, oppos)
    assert report.errors == ["decks : « terra » renvoie à la fois vers terra-midrange et terra-mono"]
    assert snapshot(tournament) == before


def test_games_csv_invalide_rien_n_est_importe(setup):
    tournament, oppos = setup
    write(tournament / "games.csv", HEADER_CSV + "02/10/2026,02/10/2026-01,1,paper,terra-midrange,v1,Ragavan,OTX,W,\n")
    before = snapshot(tournament)
    report = import_inbox(tournament, oppos)
    assert report.errors == ["games.csv : ligne 2 : position inconnue (OTP ou OTD) : OTX"]
    assert snapshot(tournament) == before
