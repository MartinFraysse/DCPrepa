import shutil
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
    write(tournament / "decks" / "terra.yaml", "name: Terra\nstatut: retenu\nversions:\n    - version: v1\n")
    write(tournament / "games.csv", HEADER_CSV + GAMES)
    write(tournament / "meta" / "README.md", "# meta\n")
    return tournament


def test_module_stats_declare():
    assert MODULES["stats"][0] is run_stats


def test_stats_bilan(tournament, capsys):
    assert run_stats(tournament) == 0
    assert capsys.readouterr().out == (
        "✅ 1 rapport(s) + synthèse écrits à partir de 3 game(s) : terra.\n"
        "   Pas de méta : matchups triés par nombre de games.\n"
    )
    assert (tournament / "stats" / "terra.md").is_file()
    assert (tournament / "stats" / "synthese.md").is_file()


def test_stats_avec_meta_et_avertissement(tournament, capsys):
    write(tournament / "meta" / "2026-09-24" / "general.csv", "oppo,decks,poids\nKess,10,20\n")
    write(tournament / "meta" / "2026-09-24" / "paper.csv", "oppo,decks,poids\nKess,8,25\n")
    with (tournament / "games.csv").open("a", encoding="utf-8") as file:
        file.write("01/11/2026,01/11/2026-03,1,mtgo,atraxa,v1,Kess,OTP,W,\n")
    assert run_stats(tournament) == 0
    assert capsys.readouterr().out == (
        "✅ 1 rapport(s) + synthèse écrits à partir de 4 game(s) : terra.\n"
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


@pytest.fixture
def data(tmp_path, monkeypatch):
    """Un faux data/ (modèle de tournoi réel + oppos.yaml minimal) : les modules de saisie n'écrivent que là."""
    data_dir = tmp_path / "data"
    shutil.copytree(Path(__file__).resolve().parents[2] / "data" / "templates", data_dir / "templates")
    write(data_dir / "oppos.yaml", "Ragavan:\n    - raga\n")
    monkeypatch.setattr(main_module, "DATA_DIR", data_dir)
    monkeypatch.setattr(main_module, "OPPOS_PATH", data_dir / "oppos.yaml")
    return data_dir


def run(capsys, *argv):
    code = main_module.main(list(argv))
    return code, capsys.readouterr().out


def test_aide_liste_tous_les_modules(capsys):
    with pytest.raises(SystemExit) as exit_info:
        main_module.main(["--help"])
    assert exit_info.value.code == 0
    out = capsys.readouterr().out
    assert all(name in out for name in MODULES)


def test_module_inconnu_ou_argument_manquant(capsys):
    for argv in (["inconnu"], ["game-add", "x"], []):
        with pytest.raises(SystemExit) as exit_info:
            main_module.main(argv)
        assert exit_info.value.code == 2


def test_tournoi_introuvable(data, capsys):
    assert run(capsys, "stats", "absent") == (2, f"Tournoi introuvable : {data / 'tournaments' / 'absent'}\n")


def test_parcours_complet(data, capsys, tmp_path):
    """Créer un tournoi et un deck, saisir, corriger, supprimer : chaque module affiche son bilan."""
    assert run(capsys, "tournament-create", "Été Duel #3", "--date", "1/9/2026") == (
        0, "✅ Tournoi créé : data/tournaments/ete-duel-3/ (slug déduit du nom).\n"
    )
    assert run(capsys, "tournament-edit", "ete-duel-3", "--banlist", "01/09/2026")[1] == "✅ tournament.yaml modifié : banlist.\n"

    liste = tmp_path / "kinnan.txt"
    liste.write_text("1 Kinnan, Bonder Prodigy\n99 Island\n", encoding="utf-8")
    assert run(capsys, "deck-create", "ete-duel-3", "Kinnan Combo", "--liste", str(liste)) == (0, "✅ Deck créé : decks/kinnan-combo.yaml (v1).\n")
    assert run(capsys, "deck-alias", "ete-duel-3", "kinnan-combo", "Kinnan")[1] == "✅ Appellation ajoutée : Kinnan → kinnan-combo.\n"
    assert run(capsys, "deck-version", "ete-duel-3", "Kinnan", "--in", "Force of Will", "--in", "Daze", "--out", "Island")[1] == (
        "✅ Version v2 ajoutée à decks/kinnan-combo.yaml.\n"
    )
    assert run(capsys, "deck-status", "ete-duel-3", "kinnan", "retenu")[1] == "✅ decks/kinnan-combo.yaml : statut retenu.\n"

    code, out = run(capsys, "game-add", "ete-duel-3", "--date", "02/10/2026", "--source", "paper", "--deck", "Kinnan",
                    "--version", "v2", "--oppo", "raga", "--games", "OTP W, OTD L, OTP W / OTD L")
    assert (code, out) == (0, "✅ 2 BO, 4 game(s) ajoutés : 02/10/2026-01, 02/10/2026-02.\n")
    assert run(capsys, "game-edit", "ete-duel-3", "02/10/2026-01", "3", "--resultat", "L")[1] == "✅ 02/10/2026-01 game 3 corrigée.\n"
    assert run(capsys, "bo-edit", "ete-duel-3", "02/10/2026-02", "--date", "03/10/2026")[1] == "✅ BO corrigé : 03/10/2026-01 (1 game(s)).\n"
    assert run(capsys, "bo-delete", "ete-duel-3", "03/10/2026-01")[1] == "✅ BO 03/10/2026-01 supprimé.\n"
    assert run(capsys, "game-delete", "ete-duel-3", "02/10/2026-01", "1")[1] == (
        "✅ 02/10/2026-01 game 1 supprimée (2 game(s) restante(s) dans le BO).\n"
    )
    games = (data / "tournaments" / "ete-duel-3" / "games.csv").read_text(encoding="utf-8").splitlines()
    assert [line.split(",")[1:3] + line.split(",")[7:9] for line in games[1:]] == [
        ["02/10/2026-01", "1", "OTD", "L"], ["02/10/2026-01", "2", "OTP", "L"],
    ]

    assert run(capsys, "stats", "ete-duel-3")[0] == 0


def test_erreurs_et_avertissements(data, capsys):
    main_module.main(["tournament-create", "Test"])
    main_module.main(["deck-create", "test", "Terra"])
    capsys.readouterr()
    assert run(capsys, "deck-create", "test", "terra") == (
        1, "❌ Rien n'a été modifié. Erreurs à corriger :\n  - appellation déjà prise : terra → terra\n"
    )
    code, out = run(capsys, "game-add", "test", "--source", "mtgo", "--deck", "terra", "--version", "v1", "--oppo", "Ragavn", "--games", "OTP W")
    assert code == 0 and out.startswith("✅ 1 BO, 1 game(s) ajoutés")
    assert "⚠️  Avertissements :\n  - oppo inconnu : Ragavn" in out
    assert run(capsys, "oppo-add", "Ragavn", "--variant-of", "raga")[1] == "✅ Variante ajoutée : Ragavn → Ragavan.\n"
    assert run(capsys, "tournament-create", "test")[1] == (
        f"❌ Tournoi non créé. Erreurs à corriger :\n  - dossier déjà existant : {data / 'tournaments' / 'test'}\n"
    )
    assert run(capsys, "deck-create", "test", "Kinnan", "--liste", "/absent.txt")[0] == 1


@pytest.mark.parametrize(
    "argv, message",
    [
        (["deck-status", "t", "d", "écarté"], "python -m dcprepa deck-status : erreur : argument statut : valeur invalide : 'écarté' (possibles : 'retenu', 'envisage', 'ecarte')"),
        (["game-add", "t", "--source", "paper"], "python -m dcprepa game-add : erreur : arguments obligatoires manquants : --deck, --version, --oppo, --games"),
        (["stats", "t", "--slug", "x"], "python -m dcprepa : erreur : arguments inconnus : --slug x"),
        (["game-add", "t", "--deck"], "python -m dcprepa game-add : erreur : argument --deck : une valeur est attendue"),
    ],
)
def test_erreurs_d_arguments_en_francais(capsys, argv, message):
    with pytest.raises(SystemExit) as exit_info:
        main_module.main(argv)
    assert exit_info.value.code == 2
    err = capsys.readouterr().err
    assert err.startswith("utilisation : python -m dcprepa")
    assert err.rstrip().endswith(message)


def test_aide_en_francais(capsys):
    with pytest.raises(SystemExit):
        main_module.main(["bo-delete", "--help"])
    out = capsys.readouterr().out
    assert out.startswith("utilisation : python -m dcprepa bo-delete [-h] tournoi match_id\n")
    assert "\narguments:\n" in out and "\noptions:\n" in out and "affiche cette aide" in out
