import shutil
from pathlib import Path

import pytest
import yaml

from dcprepa.services.stats import generate_stats
from dcprepa.services.tournament import create_tournament, edit_tournament

DATA_DIR = Path(__file__).resolve().parents[3] / "data"


@pytest.fixture
def data(tmp_path):
    """Un data/ minimal : le vrai modèle de tournoi, pas encore de tournoi."""
    shutil.copytree(DATA_DIR / "templates", tmp_path / "templates")
    return tmp_path


def fiche(folder):
    return yaml.safe_load((folder / "tournament.yaml").read_text(encoding="utf-8"))


def test_creation(data):
    report = create_tournament(data, "RelicFest 2026", {"date": "31/10/2026", "location": " Toulouse "})
    assert (report.ok, report.slug, report.folder) == (True, "relicfest-2026", data / "tournaments" / "relicfest-2026")
    assert fiche(report.folder) == {
        "name": "RelicFest 2026", "slug": "relicfest-2026", "format": "Duel Commander",
        "date": "31/10/2026", "location": "Toulouse", "banlist": None, "notes": None,
    }
    files = sorted(str(path.relative_to(report.folder)) for path in report.folder.rglob("*") if path.is_file())
    assert files == [
        "decks/_alias.yaml", "decks/_modele.yaml", "games.csv", "inbox.yaml",
        "meta/README.md", "stats/README.md", "stats/synthese.md", "tournament.yaml",
    ]
    assert "_modele-deck.md" not in (report.folder / "stats" / "README.md").read_text(encoding="utf-8")
    assert "# nom affiché" in (report.folder / "tournament.yaml").read_text(encoding="utf-8")


def test_le_tournoi_cree_passe_stats(data):
    folder = create_tournament(data, "Test Stats").folder
    report = generate_stats(folder)
    assert report.errors == [] and report.decks == []
    assert (folder / "stats" / "synthese.md").read_text(encoding="utf-8").startswith("# Synthèse — Test Stats\n")


def test_slug_deja_pris(data):
    create_tournament(data, "RelicFest 2026")
    report = create_tournament(data, "relicfest 2026 !")
    assert report.errors == [f"dossier déjà existant : {data / 'tournaments' / 'relicfest-2026'}"]
    assert report.slug is None


@pytest.mark.parametrize(
    "name, fields, error",
    [
        ("", None, "nom du tournoi vide"),
        ("???", None, "nom du tournoi sans lettre ni chiffre : ???"),
        ("X", {"date": "2026-10-31"}, "date invalide (attendu : JJ/MM/AAAA) : 2026-10-31"),
        ("X", {"slug": "y"}, "champ non modifiable ici : slug (possibles : name, format, date, location, banlist, notes)"),
    ],
)
def test_creation_refusee_rien_n_est_cree(data, name, fields, error):
    report = create_tournament(data, name, fields)
    assert report.errors == [error]
    assert not (data / "tournaments").exists()


def test_date_avec_ses_zeros(data):
    assert fiche(create_tournament(data, "X", {"date": "1/9/2026"}).folder)["date"] == "01/09/2026"


def test_modification(data):
    folder = create_tournament(data, "RelicFest 2026").folder
    report = edit_tournament(folder, {"banlist": "01/09/2026", "notes": "Top 8 à 16 h", "name": "RelicFest 2026 (J1)"})
    assert (report.ok, report.slug) == (True, "relicfest-2026")
    values = fiche(folder)
    assert (values["banlist"], values["notes"], values["name"], values["slug"]) == (
        "01/09/2026", "Top 8 à 16 h", "RelicFest 2026 (J1)", "relicfest-2026"
    )
    assert "# date ou lien de la banlist en vigueur" in (folder / "tournament.yaml").read_text(encoding="utf-8")


def test_modification_refusee(data):
    folder = create_tournament(data, "RelicFest 2026").folder
    before = (folder / "tournament.yaml").read_text(encoding="utf-8")
    assert edit_tournament(folder, {"date": "32/01/2026"}).errors == ["date invalide (attendu : JJ/MM/AAAA) : 32/01/2026"]
    assert edit_tournament(folder, {}).errors == ["rien à modifier"]
    assert (folder / "tournament.yaml").read_text(encoding="utf-8") == before
    assert edit_tournament(data / "tournaments" / "absent", {"notes": "x"}).errors[0].startswith("fichier introuvable")


def test_vrai_tournoi_modifie_sans_perte(tmp_path):
    """tournament.yaml de RelicFest, copié : seul le champ modifié change."""
    folder = tmp_path / "relicfest-2026"
    shutil.copytree(DATA_DIR / "tournaments" / "relicfest-2026", folder)
    before = (folder / "tournament.yaml").read_text(encoding="utf-8")
    assert edit_tournament(folder, {"banlist": "01/09/2026"}).ok
    after = (folder / "tournament.yaml").read_text(encoding="utf-8")
    assert [line for line in after.split("\n") if line not in before.split("\n")] == [
        line for line in after.split("\n") if line.startswith("banlist:")
    ]
