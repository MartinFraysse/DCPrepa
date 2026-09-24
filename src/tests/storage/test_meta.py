from pathlib import Path

import pytest

from dcprepa.storage.meta import load_latest_meta

DATA_DIR = Path(__file__).resolve().parents[3] / "data"
HEADER = "oppo,decks,poids\n"


def write_meta(tournament_dir, name, text):
    meta_dir = tournament_dir / "meta"
    meta_dir.mkdir(exist_ok=True)
    (meta_dir / name).write_text(text, encoding="utf-8")


@pytest.mark.parametrize(
    "tournament_dir",
    [
        DATA_DIR / "tournaments" / "relicfest-2026",
        DATA_DIR / "tournaments" / "test_tournoi",
        DATA_DIR / "templates" / "tournament",
    ],
)
def test_depot_sans_meta(tournament_dir):
    assert load_latest_meta(tournament_dir) == (None, {}, [])


def test_dossier_meta_absent(tmp_path):
    assert load_latest_meta(tmp_path) == (None, {}, [])


def test_fichiers_non_dates_ignores(tmp_path):
    write_meta(tmp_path, "README.md", "# meta\n")
    write_meta(tmp_path, "brouillon.csv", "n'importe quoi\n")
    write_meta(tmp_path, "2026-13-01.csv", "n'importe quoi\n")
    assert load_latest_meta(tmp_path) == (None, {}, [])


def test_lecture(tmp_path):
    write_meta(tmp_path, "2026-10-01.csv", HEADER + "Ragavan,25,12.5\nKess,10,5\n\n")
    assert load_latest_meta(tmp_path) == ("2026-10-01.csv", {"Ragavan": 12.5, "Kess": 5.0}, [])


def test_fichier_le_plus_recent(tmp_path):
    write_meta(tmp_path, "2026-09-15.csv", HEADER + "Ragavan,1,1\n")
    write_meta(tmp_path, "2026-10-01.csv", HEADER + "Kess,2,2\n")
    write_meta(tmp_path, "2026-09-30.csv", HEADER + "Atraxa,3,3\n")
    assert load_latest_meta(tmp_path) == ("2026-10-01.csv", {"Kess": 2.0}, [])


def test_bom_accepte(tmp_path):
    (tmp_path / "meta").mkdir()
    (tmp_path / "meta" / "2026-10-01.csv").write_text(HEADER + "Kess,2,2\n", encoding="utf-8-sig")
    assert load_latest_meta(tmp_path) == ("2026-10-01.csv", {"Kess": 2.0}, [])


@pytest.mark.parametrize("text", ["", "oppo,poids\nKess,2\n"])
def test_en_tete_inattendu(tmp_path, text):
    write_meta(tmp_path, "2026-10-01.csv", text)
    name, weights, errors = load_latest_meta(tmp_path)
    assert (name, weights) == ("2026-10-01.csv", {})
    assert len(errors) == 1 and "en-tête inattendu" in errors[0]


@pytest.mark.parametrize(
    "line, message",
    [
        ("Kess,2\n", "ligne 2 : 2 colonnes au lieu de 3"),
        (",2,2\n", "ligne 2 : oppo vide"),
        ("Kess,deux,2\n", "ligne 2 : decks attendu en nombre entier : deux"),
        ("Kess,2,-1\n", "ligne 2 : poids attendu en nombre positif (ex. 12.5) : -1"),
        ("Kess,2,12%\n", "ligne 2 : poids attendu en nombre positif (ex. 12.5) : 12%"),
        ("Kess,2,nan\n", "ligne 2 : poids attendu en nombre positif (ex. 12.5) : nan"),
    ],
)
def test_ligne_invalide(tmp_path, line, message):
    write_meta(tmp_path, "2026-10-01.csv", HEADER + line)
    assert load_latest_meta(tmp_path) == ("2026-10-01.csv", {}, [f"meta/2026-10-01.csv : {message}"])


def test_oppo_en_double(tmp_path):
    write_meta(tmp_path, "2026-10-01.csv", HEADER + "Kess,2,2\nKess,3,3\n")
    assert load_latest_meta(tmp_path) == ("2026-10-01.csv", {}, ["meta/2026-10-01.csv : ligne 3 : oppo en double : Kess"])
