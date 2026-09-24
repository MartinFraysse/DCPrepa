import shutil
from datetime import date
from pathlib import Path

import pytest

from dcprepa.services.stats import generate_stats
from dcprepa.storage.games import COLUMNS

DATA_DIR = Path(__file__).resolve().parents[3] / "data"
HEADER_CSV = ",".join(COLUMNS) + "\n"
GENERATED = date(2026, 9, 24)
TERRA = "name: Terra Midrange\ncommandant: Terra\nstatut: envisage\nversions:\n    - version: v1\n    - version: v2\n"
TYMNA = "name: Tymna Thrasios\nversions:\n    - version: v1\n"
STATUT_TYMNA = "tymna : statut vide (retenu, envisage ou ecarte) → absent du tableau Méta et des matchups non testés"
GAMES = (
    "01/11/2026,01/11/2026-01,1,paper,terra,v1,Ragavan,OTP,W,\n"
    "01/11/2026,01/11/2026-01,2,paper,terra,v1,Ragavan,OTD,W,\n"
    "01/11/2026,01/11/2026-02,1,mtgo,terra,v2,Kess,OTD,L,\n"
)


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="")


@pytest.fixture
def tournament(tmp_path):
    """Un mini-tournoi : deux fiches deck (terra, tymna), games.csv, stats/ avec un ancien rapport, meta/ vide."""
    tournament = tmp_path / "test"
    write(tournament / "decks" / "terra.yaml", TERRA)
    write(tournament / "decks" / "tymna.yaml", TYMNA)
    write(tournament / "decks" / "_modele.yaml", "versions:\n")
    write(tournament / "games.csv", HEADER_CSV + GAMES)
    write(tournament / "stats" / "terra.md", "ancien rapport\n")
    write(tournament / "meta" / "README.md", "# meta\n")
    write(tournament / "tournament.yaml", "name: RelicFest 2026\nslug: test\n")
    return tournament


def test_un_rapport_par_fiche(tournament):
    report = generate_stats(tournament, GENERATED)
    assert report.ok
    assert (report.decks, report.games, report.meta) == (["terra", "tymna"], 3, None)
    assert report.warnings == [STATUT_TYMNA]

    terra = (tournament / "stats" / "terra.md").read_text(encoding="utf-8")
    assert terra.startswith("# Terra Midrange\n\n> Généré le 24/09/2026 à partir de `games.csv`, `decks/terra.yaml` et `meta/—`.")
    assert "| Winrate | ⚠️ 66.7 % (2/3) | ⚠️ 100 % (1/1) |" in terra

    tymna = (tournament / "stats" / "tymna.md").read_text(encoding="utf-8")
    assert tymna.startswith("# Tymna Thrasios\n")
    assert "| Winrate | — | — |" in tymna
    assert not (tournament / "stats" / "_modele.md").exists()


def test_avec_meta(tournament):
    write(tournament / "meta" / "2026-09-10" / "general.csv", "oppo,decks,poids\nRagavan,50,50\n")  # import précédent
    write(tournament / "meta" / "2026-09-24" / "general.csv", "oppo,decks,poids\nKess,10,20\nRagavan,5,10\n")
    write(tournament / "meta" / "2026-09-24" / "paper.csv", "oppo,decks,poids\nRagavan,8,15\n")
    report = generate_stats(tournament, GENERATED)
    assert report.meta == "2026-09-24"
    terra = (tournament / "stats" / "terra.md").read_text(encoding="utf-8")
    assert "et `meta/2026-09-24/`." in terra
    # tri par poids papier : Ragavan (papier 15 %) avant Kess (absent du papier)
    assert terra.index("| Ragavan | 15 % | 10 % |") < terra.index("| Kess | — | 20 % |")


def assert_nothing_written(tournament):
    assert (tournament / "stats" / "terra.md").read_text(encoding="utf-8") == "ancien rapport\n"
    assert not (tournament / "stats" / "tymna.md").exists()
    assert not (tournament / "stats" / "synthese.md").exists()


def test_games_csv_invalide(tournament):
    write(tournament / "games.csv", HEADER_CSV + GAMES + "01/11/2026,01/11/2026-03,1,mtgo,terra,v2,Kess,OTX,W,\n")
    report = generate_stats(tournament, GENERATED)
    assert report.errors == ["games.csv : ligne 5 : position inconnue (OTP ou OTD) : OTX"]
    assert (report.decks, report.games) == ([], 0)
    assert_nothing_written(tournament)


def test_fiche_invalide(tournament):
    write(tournament / "decks" / "tymna.yaml", "name: Tymna\nversions:\n")
    report = generate_stats(tournament, GENERATED)
    assert not report.ok
    assert report.errors[0].startswith("tymna.yaml : aucune version")
    assert_nothing_written(tournament)


@pytest.mark.parametrize(
    "deck, message",
    [
        ("synthese", "decks/synthese.yaml : nom réservé (stats/synthese.md serait écrasé par la synthèse du tournoi) → renommer la fiche"),
        ("README", "decks/README.yaml : nom réservé (stats/README.md serait écrasé par la page des conventions) → renommer la fiche"),
        ("Synthese", "decks/Synthese.yaml : nom réservé (stats/Synthese.md serait écrasé par la synthèse du tournoi) → renommer la fiche"),
    ],
)
def test_fiche_au_nom_reserve(tournament, deck, message):
    write(tournament / "decks" / f"{deck}.yaml", TYMNA)
    report = generate_stats(tournament, GENERATED)
    assert report.errors == [message]
    assert_nothing_written(tournament)


def test_meta_invalide(tournament):
    write(tournament / "meta" / "2026-09-24" / "general.csv", "oppo,decks,poids\nKess,10,beaucoup\n")
    report = generate_stats(tournament, GENERATED)
    assert report.errors == [
        "meta/2026-09-24/general.csv : ligne 2 : poids attendu en nombre positif (ex. 12.5) : beaucoup",
        "meta/2026-09-24/paper.csv : fichier manquant",
    ]
    assert_nothing_written(tournament)


def test_avertissements(tournament):
    write(
        tournament / "games.csv",
        HEADER_CSV + GAMES
        + "01/11/2026,01/11/2026-03,1,mtgo,terra,v9,Kess,OTP,W,\n"
        + "01/11/2026,01/11/2026-04,1,mtgo,atraxa,v1,Kess,OTP,W,\n"
        + "01/11/2026,01/11/2026-04,2,mtgo,atraxa,v1,Kess,OTD,W,\n",
    )
    report = generate_stats(tournament, GENERATED)
    assert report.ok
    assert report.warnings == [
        "games.csv : deck sans fiche : atraxa (2 game(s)) → pas de rapport",
        "terra : version jouée absente de la fiche : v9",
        STATUT_TYMNA,
    ]
    assert report.decks == ["terra", "tymna"]
    assert "| v9 | 1 |" in (tournament / "stats" / "terra.md").read_text(encoding="utf-8")


def test_synthese_ecrite(tournament):
    write(tournament / "meta" / "2026-09-24" / "general.csv", "oppo,decks,poids\nKess,10,20\nRagavan,5,10\n")
    write(tournament / "meta" / "2026-09-24" / "paper.csv", "oppo,decks,poids\nRagavan,8,15\n")
    report = generate_stats(tournament, GENERATED)
    assert report.ok
    synthese = (tournament / "stats" / "synthese.md").read_text(encoding="utf-8")
    assert synthese.startswith("# Synthèse — RelicFest 2026\n")
    assert "et `meta/2026-09-24/`." in synthese
    assert "| [Terra Midrange](terra.md) | envisage | v2 | ⚠️ 66.7 % (2/3) | ⚠️ 100 % (1/1) |" in synthese
    assert "| Oppo | Poids papier | Poids général | Terra Midrange |" in synthese  # tymna, sans statut : pas de colonne
    assert "| Terra Midrange | Ragavan | 1 | 15 % | 1 | 2 |" in synthese


def test_statut_inconnu(tournament):
    write(tournament / "decks" / "tymna.yaml", "name: Tymna\nstatut: envisagé\nversions:\n    - version: v1\n")
    report = generate_stats(tournament, GENERATED)
    assert report.warnings == [
        "tymna : statut inconnu « envisagé » (retenu, envisage ou ecarte) → absent du tableau Méta et des matchups non testés"
    ]


def test_nom_du_tournoi_absent(tournament):
    (tournament / "tournament.yaml").unlink()
    generate_stats(tournament, GENERATED)
    assert (tournament / "stats" / "synthese.md").read_text(encoding="utf-8").startswith("# Synthèse — test\n")


def test_date_du_jour_par_defaut(tournament):
    generate_stats(tournament)
    terra = (tournament / "stats" / "terra.md").read_text(encoding="utf-8")
    assert f"Généré le {date.today().strftime('%d/%m/%Y')}" in terra


def test_test_tournoi(tmp_path):
    """Le tournoi de test du dépôt (données fictives qui changent), copié : aucune erreur, un rapport par fiche."""
    tournament = tmp_path / "test_tournoi"
    shutil.copytree(DATA_DIR / "tournaments" / "test_tournoi", tournament)
    report = generate_stats(tournament, GENERATED)
    assert report.errors == []
    sheets = sorted(path.stem for path in (tournament / "decks").glob("*.yaml") if not path.name.startswith("_"))
    assert report.decks == sheets
    lines = (tournament / "games.csv").read_text(encoding="utf-8").splitlines()
    assert report.games == len([line for line in lines[1:] if line.strip()])
    assert all((tournament / "stats" / f"{deck}.md").is_file() for deck in sheets)
    assert (tournament / "stats" / "synthese.md").is_file()
