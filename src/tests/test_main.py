from pathlib import Path

import pytest

from dcprepa.__main__ import MODULES, run_stats
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
