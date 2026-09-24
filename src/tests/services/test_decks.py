import shutil
from datetime import date
from pathlib import Path

import pytest

from dcprepa.services.decks import add_deck_alias, add_version, create_deck, edit_deck, set_status
from dcprepa.services.games import add_games
from dcprepa.services.stats import generate_stats
from dcprepa.storage.decks import load_deck_aliases, load_deck_sheets, load_decks

DATA_DIR = Path(__file__).resolve().parents[3] / "data"
TODAY = date(2026, 9, 24)
LISTE = "1 Kinnan, Bonder Prodigy\n99 Island\n"


@pytest.fixture
def tournament(tmp_path):
    """RelicFest copié : un deck terra-midrange (v1, alias « Terra », « Terra mid »), games.csv vide."""
    folder = tmp_path / "relicfest-2026"
    shutil.copytree(DATA_DIR / "tournaments" / "relicfest-2026", folder)
    return folder


def sheets(folder):
    return load_deck_sheets(folder)[0]


def snapshot(folder):
    return {path.name: path.read_text(encoding="utf-8") for path in (folder / "decks").iterdir()}


def test_create_deck(tournament):
    report = create_deck(tournament, "Kinnan Combo", "Kinnan, Bonder Prodigy", liste=LISTE, notes="Première liste", today=TODAY)
    assert (report.ok, report.deck, report.version, report.warnings) == (True, "kinnan-combo", "v1", [])
    assert sheets(tournament)["kinnan-combo"] == {
        "name": "Kinnan Combo", "commandant": "Kinnan, Bonder Prodigy", "statut": "envisage", "versions": ["v1"],
    }
    text = (tournament / "decks" / "kinnan-combo.yaml").read_text(encoding="utf-8")
    assert text.startswith("# Fiche deck créée par la saisie le 24/09/2026.\n")
    assert "                99 Island\n        notes: Première liste\n" in text


def test_create_deck_sans_liste_et_liste_incomplete(tournament):
    assert create_deck(tournament, "Sans liste").ok
    report = create_deck(tournament, "Kinnan", liste="1 Kinnan\n")
    assert report.ok and report.warnings == ["liste de 1 cartes (100 attendues, commandant compris)"]


@pytest.mark.parametrize(
    "name, kwargs, error",
    [
        ("Terra mid", {}, "appellation déjà prise : Terra mid → terra-midrange"),
        ("Terra Midrange", {}, "appellation déjà prise : Terra Midrange → terra-midrange"),
        ("Synthèse", {}, "nom réservé : synthese (stats/synthese.md est un fichier du tournoi)"),
        ("Kinnan", {"statut": "retenue"}, "statut inconnu : retenue (retenu, envisage ou ecarte)"),
        ("Kinnan", {"liste": "Kinnan\n"}, "liste : ligne 1 : attendu « 1 Nom de carte » : Kinnan"),
    ],
)
def test_create_deck_refuse_rien_n_est_ecrit(tournament, name, kwargs, error):
    before = snapshot(tournament)
    report = create_deck(tournament, name, **kwargs)
    assert report.errors == [error]
    assert snapshot(tournament) == before


def test_add_version_automatique_par_appellation(tournament):
    report = add_version(tournament, "Terra mid", cards_in=["Force of Will"], cards_out=["Dismember"], notes="Plus d'interaction")
    assert (report.ok, report.deck, report.version) == (True, "terra-midrange", "v2")
    assert sheets(tournament)["terra-midrange"]["versions"] == ["v1", "v2"]
    assert add_version(tournament, "terra", version="v2-bis", liste=LISTE).version == "v2-bis"
    assert add_version(tournament, "terra", cards_in=["X"]).version == "v3"


@pytest.mark.parametrize(
    "deck, kwargs, error",
    [
        ("atraxa", {"cards_in": ["X"]}, "deck inconnu : atraxa (decks disponibles : terra-midrange)"),
        ("terra", {"version": "v1", "cards_in": ["X"]}, "version déjà présente : v1"),
        ("terra", {}, "version sans changement : in, out ou liste attendus"),
    ],
)
def test_add_version_refusee(tournament, deck, kwargs, error):
    before = snapshot(tournament)
    assert add_version(tournament, deck, **kwargs).errors == [error]
    assert snapshot(tournament) == before


def test_la_nouvelle_version_est_utilisable(tournament):
    """Une version ajoutée est acceptée par la saisie des games, puis par les stats."""
    add_version(tournament, "terra", cards_in=["Force of Will"])
    block = {"date": "02/10/2026", "source": "paper", "deck": "Terra", "version": "v2", "oppo": "Cloud", "games": "OTP W, OTD W"}
    assert add_games(tournament, block, DATA_DIR / "oppos.yaml").ok
    report = generate_stats(tournament)
    assert report.errors == []
    assert "| v2 | 2 |" in (tournament / "stats" / "terra-midrange.md").read_text(encoding="utf-8")


def test_set_status(tournament):
    report = set_status(tournament, "Terra", "retenu")
    assert (report.ok, report.deck) == (True, "terra-midrange")
    assert sheets(tournament)["terra-midrange"]["statut"] == "retenu"
    assert set_status(tournament, "terra", "écarté").errors == ["statut inconnu : écarté (retenu, envisage ou ecarte)"]
    assert sheets(tournament)["terra-midrange"]["statut"] == "retenu"


def test_edit_deck(tournament):
    create_deck(tournament, "Kinnan Combo")
    report = edit_deck(tournament, "kinnan-combo", {"name": "Kinnan Turbo", "commandant": "Kinnan, Bonder Prodigy"})
    assert report.ok
    assert sheets(tournament)["kinnan-combo"]["name"] == "Kinnan Turbo"
    assert "kinnan-combo" in load_decks(tournament)[0]
    assert edit_deck(tournament, "kinnan-combo", {"name": "Terra mid"}).errors == ["appellation déjà prise : Terra mid → terra-midrange"]
    assert edit_deck(tournament, "kinnan-combo", {"statut": "retenu"}).errors == ["champ non modifiable ici : statut (possibles : name, commandant)"]
    assert edit_deck(tournament, "kinnan-combo", {}).errors == ["rien à modifier"]


def test_add_deck_alias(tournament):
    create_deck(tournament, "Kinnan Combo")
    report = add_deck_alias(tournament, "Kinnan Combo", "Kinnan")
    assert (report.ok, report.deck) == (True, "kinnan-combo")
    decks = load_decks(tournament)[0]
    assert load_deck_aliases(tournament, decks)[0]["kinnan-combo"] == ["kinnan-combo", "Kinnan Combo", "Kinnan"]
    assert add_deck_alias(tournament, "kinnan", "terra").errors == ["appellation déjà prise : terra → terra-midrange"]
    assert add_deck_alias(tournament, "kinnan", " ").errors == ["appellation vide"]
