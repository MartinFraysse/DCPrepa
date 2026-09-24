from pathlib import Path

import pytest

import dcprepa.__main__ as main_module
from dcprepa.__main__ import MODULES, run_meta, run_stats
from dcprepa.services.import_meta import MetaReport
from dcprepa.storage.games import COLUMNS

HEADER_CSV = ",".join(COLUMNS) + "\n"
GAMES = (
    "01/11/2026,01/11/2026-01,1,paper,terra,v1,Ragavan,OTP,W,\n"
    "01/11/2026,01/11/2026-01,2,paper,terra,v1,Ragavan,OTD,W,\n"
    "01/11/2026,01/11/2026-02,1,mtgo,terra,v1,Kess,OTD,L,\n"
)


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="")


@pytest.fixture
def tournament(tmp_path):
    """Un mini-tournoi : une fiche deck (terra), 3 games, meta/ sans fichier daté."""
    tournament = tmp_path / "test"
    write(tournament / "decks" / "terra.yaml", "name: Terra\nversions:\n    - version: v1\n")
    write(tournament / "games.csv", HEADER_CSV + GAMES)
    write(tournament / "meta" / "README.md", "# meta\n")
    return tournament


def test_module_stats_declare():
    assert MODULES["stats"][0] is run_stats


def test_stats_bilan(tournament, capsys):
    assert run_stats(tournament) == 0
    assert capsys.readouterr().out == (
        "✅ 1 rapport(s) écrit(s) à partir de 3 game(s) : terra.\n"
        "   Pas de méta : matchups triés par nombre de games.\n"
    )
    assert (tournament / "stats" / "terra.md").is_file()


def test_stats_avec_meta_et_avertissement(tournament, capsys):
    write(tournament / "meta" / "2026-09-24" / "general.csv", "oppo,decks,poids\nKess,10,20\n")
    write(tournament / "meta" / "2026-09-24" / "paper.csv", "oppo,decks,poids\nKess,8,25\n")
    with (tournament / "games.csv").open("a", encoding="utf-8") as file:
        file.write("01/11/2026,01/11/2026-03,1,mtgo,atraxa,v1,Kess,OTP,W,\n")
    assert run_stats(tournament) == 0
    assert capsys.readouterr().out == (
        "✅ 1 rapport(s) écrit(s) à partir de 4 game(s) : terra.\n"
        "   Méta : meta/2026-09-24/ (matchups triés par poids papier).\n"
        "⚠️  Avertissements :\n"
        "  - games.csv : deck sans fiche : atraxa (1 game(s)) → pas de rapport\n"
    )


def test_stats_erreur(tournament, capsys):
    write(tournament / "meta" / "2026-09-24" / "general.csv", "oppo,poids\n")
    assert run_stats(tournament) == 1
    out = capsys.readouterr().out
    assert out.startswith("❌ Stats annulées, aucun rapport écrit. Erreurs à corriger :\n  - meta/2026-09-24/general.csv : en-tête inattendu")
    assert not (tournament / "stats" / "terra.md").exists()


def test_module_meta_declare():
    assert MODULES["meta"][0] is run_meta


@pytest.mark.parametrize(
    "report, output, code",
    [
        (
            MetaReport(folder="2026-09-24", metas={"general": (20, 1447), "paper": (20, 1309)}, added_oppos=["Phelia", "Cloud"]),
            "✅ meta/2026-09-24/ écrit : général 20 oppos (1447 decks), papier 20 oppos (1309 decks).\n"
            "📝 2 oppo(s) ajouté(s) à data/oppos.yaml : Phelia, Cloud.\n",
            0,
        ),
        (
            MetaReport(folder="2026-09-24", replaced=True, metas={"general": (20, 1447), "paper": (20, 1309)}),
            "✅ meta/2026-09-24/ écrit (remplace l'import du jour) : général 20 oppos (1447 decks), papier 20 oppos (1309 decks).\n",
            0,
        ),
        (
            MetaReport(errors=["méta papier : MTGTop8 ne répond pas (délai de 20 s dépassé)"]),
            "❌ Import du méta annulé, aucun fichier modifié. Erreurs à corriger :\n"
            "  - méta papier : MTGTop8 ne répond pas (délai de 20 s dépassé)\n",
            1,
        ),
    ],
)
def test_meta_bilan(monkeypatch, tmp_path, capsys, report, output, code):
    monkeypatch.setattr(main_module, "import_meta", lambda tournament_dir, oppos_path: report)
    assert run_meta(tmp_path) == code
    assert capsys.readouterr().out == output
