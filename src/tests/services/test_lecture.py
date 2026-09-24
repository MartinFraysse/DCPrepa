import shutil
from pathlib import Path

import pytest

from dcprepa.services.lecture import list_matches, list_oppos, list_reports, list_tournaments, read_report, tournament_overview
from dcprepa.services.stats import generate_stats

DATA_DIR = Path(__file__).resolve().parents[3] / "data"


@pytest.fixture
def data(tmp_path):
    """Un data/ copié : les deux tournois du dépôt et oppos.yaml."""
    shutil.copytree(DATA_DIR / "tournaments", tmp_path / "tournaments")
    shutil.copy(DATA_DIR / "oppos.yaml", tmp_path / "oppos.yaml")
    return tmp_path


def test_list_tournaments(data):
    (data / "tournaments" / "sans-fiche").mkdir()
    (data / "tournaments" / "sans-fiche" / "games.csv").write_text("en-tête faux\n", encoding="utf-8")
    tournaments, errors = list_tournaments(data)
    assert [(t.slug, t.name, t.date) for t in tournaments] == [
        ("relicfest-2026", "RelicFest 2026", "31/10/2026"),
        ("test_tournoi", "Tournoi de test", "15/11/2026"),
        ("sans-fiche", "sans-fiche", ""),
    ]
    assert tournaments[1].games > 0 and tournaments[2].games is None
    assert len(errors) == 1 and errors[0].startswith("sans-fiche : games.csv : en-tête inattendu")


def test_list_tournaments_sans_dossier(tmp_path):
    assert list_tournaments(tmp_path) == ([], [])


def test_tournament_overview(data):
    overview, errors = tournament_overview(data / "tournaments" / "test_tournoi")
    assert errors == []
    assert overview.sheet["name"] == "Tournoi de test"
    assert sorted(overview.decks) == ["kinnan-combo", "sythis-enchant", "winota-aggro"]
    assert overview.decks["winota-aggro"]["statut"] == "retenu"
    assert overview.meta is not None


def test_list_matches(data):
    matches, errors = list_matches(data / "tournaments" / "test_tournoi")
    assert errors == [] and matches
    dates = [m.date.split("/")[::-1] for m in matches]
    assert dates == sorted(dates, reverse=True)
    lines = (data / "tournaments" / "test_tournoi" / "games.csv").read_text(encoding="utf-8").splitlines()[1:]
    assert sum(len(m.games) for m in matches) == len([line for line in lines if line.strip()])


def test_list_matches_games_csv_invalide(data):
    (data / "tournaments" / "test_tournoi" / "games.csv").write_text("x\n", encoding="utf-8")
    matches, errors = list_matches(data / "tournaments" / "test_tournoi")
    assert matches == [] and errors


def test_list_oppos(data):
    oppos, errors = list_oppos(data / "oppos.yaml")
    assert errors == [] and list(oppos) == sorted(oppos, key=str.lower)


def test_reports(data):
    tournament = data / "tournaments" / "test_tournoi"
    generate_stats(tournament)
    reports = list_reports(tournament)
    assert reports[0] == "synthese" and "winota-aggro" in reports and "readme" not in reports and "README" not in reports
    text, errors = read_report(tournament, "synthese")
    assert errors == [] and text.startswith("# Synthèse — Tournoi de test")


@pytest.mark.parametrize("name", ["../../oppos", "README", "_modele-deck", "absent", "../stats/synthese"])
def test_read_report_refuse(data, name):
    text, errors = read_report(data / "tournaments" / "test_tournoi", name)
    assert text == "" and errors == [f"rapport introuvable : {name} (lancer les stats d'abord ?)"]
