import shutil
from pathlib import Path

from dcprepa.__main__ import MODULES, run_stats

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def copy_test_tournament(tmp_path):
    tournament = tmp_path / "test_tournoi"
    shutil.copytree(DATA_DIR / "tournaments" / "test_tournoi", tournament)
    return tournament


def test_module_stats_declare():
    assert MODULES["stats"][0] is run_stats


def test_stats_bilan(tmp_path, capsys):
    tournament = copy_test_tournament(tmp_path)
    assert run_stats(tournament) == 0
    assert capsys.readouterr().out == (
        "✅ 1 rapport(s) écrit(s) à partir de 19 game(s) : test-deck.\n"
        "   Pas de méta : matchups triés par nombre de parties.\n"
    )
    assert (tournament / "stats" / "test-deck.md").is_file()


def test_stats_avec_meta_et_avertissement(tmp_path, capsys):
    tournament = copy_test_tournament(tmp_path)
    (tournament / "meta" / "2026-10-01.csv").write_text("oppo,decks,poids\nKess,10,20\n", encoding="utf-8")
    with (tournament / "games.csv").open("a", encoding="utf-8") as file:
        file.write("01/11/2026,01/11/2026-09,1,mtgo,atraxa,v1,Kess,OTP,W,\n")
    assert run_stats(tournament) == 0
    assert capsys.readouterr().out == (
        "✅ 1 rapport(s) écrit(s) à partir de 20 game(s) : test-deck.\n"
        "   Méta : meta/2026-10-01.csv (matchups triés par poids).\n"
        "⚠️  Avertissements :\n"
        "  - games.csv : deck sans fiche : atraxa (1 game(s)) → pas de rapport\n"
    )


def test_stats_erreur(tmp_path, capsys):
    tournament = copy_test_tournament(tmp_path)
    (tournament / "meta" / "2026-10-01.csv").write_text("oppo,poids\n", encoding="utf-8")
    assert run_stats(tournament) == 1
    out = capsys.readouterr().out
    assert out.startswith("❌ Stats annulées, aucun rapport écrit. Erreurs à corriger :\n  - meta/2026-10-01.csv : en-tête inattendu")
    assert not (tournament / "stats" / "test-deck.md").exists()
