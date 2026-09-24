from pathlib import Path

import pytest

from dcprepa.storage.meta import load_latest_meta, read_meta, write_meta

DATA_DIR = Path(__file__).resolve().parents[3] / "data"
HEADER = "oppo,decks,poids\n"


def write_meta_file(tournament_dir, name, text):
    meta_dir = tournament_dir / "meta"
    meta_dir.mkdir(exist_ok=True)
    (meta_dir / name).write_text(text, encoding="utf-8")


@pytest.mark.parametrize(
    "tournament_dir",
    [
        DATA_DIR / "tournaments" / "relicfest-2026",
        DATA_DIR / "templates" / "tournament",
    ],
)
def test_depot_sans_meta(tournament_dir):
    assert load_latest_meta(tournament_dir) == (None, {}, [])


def test_meta_du_tournoi_de_test():
    name, weights, errors = load_latest_meta(DATA_DIR / "tournaments" / "test_tournoi")
    assert errors == []
    assert name is None or weights


def test_dossier_meta_absent(tmp_path):
    assert load_latest_meta(tmp_path) == (None, {}, [])


def test_fichiers_non_dates_ignores(tmp_path):
    write_meta_file(tmp_path, "README.md", "# meta\n")
    write_meta_file(tmp_path, "brouillon.csv", "n'importe quoi\n")
    write_meta_file(tmp_path, "2026-13-01.csv", "n'importe quoi\n")
    assert load_latest_meta(tmp_path) == (None, {}, [])


def test_lecture(tmp_path):
    write_meta_file(tmp_path, "2026-10-01.csv", HEADER + "Ragavan,25,12.5\nKess,10,5\n\n")
    assert load_latest_meta(tmp_path) == ("2026-10-01.csv", {"Ragavan": 12.5, "Kess": 5.0}, [])


def test_fichier_le_plus_recent(tmp_path):
    write_meta_file(tmp_path, "2026-09-15.csv", HEADER + "Ragavan,1,1\n")
    write_meta_file(tmp_path, "2026-10-01.csv", HEADER + "Kess,2,2\n")
    write_meta_file(tmp_path, "2026-09-30.csv", HEADER + "Atraxa,3,3\n")
    assert load_latest_meta(tmp_path) == ("2026-10-01.csv", {"Kess": 2.0}, [])


def test_bom_accepte(tmp_path):
    (tmp_path / "meta").mkdir()
    (tmp_path / "meta" / "2026-10-01.csv").write_text(HEADER + "Kess,2,2\n", encoding="utf-8-sig")
    assert load_latest_meta(tmp_path) == ("2026-10-01.csv", {"Kess": 2.0}, [])


@pytest.mark.parametrize("text", ["", "oppo,poids\nKess,2\n"])
def test_en_tete_inattendu(tmp_path, text):
    write_meta_file(tmp_path, "2026-10-01.csv", text)
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
    write_meta_file(tmp_path, "2026-10-01.csv", HEADER + line)
    assert load_latest_meta(tmp_path) == ("2026-10-01.csv", {}, [f"meta/2026-10-01.csv : {message}"])


def test_oppo_en_double(tmp_path):
    write_meta_file(tmp_path, "2026-10-01.csv", HEADER + "Kess,2,2\nKess,3,3\n")
    assert load_latest_meta(tmp_path) == ("2026-10-01.csv", {}, ["meta/2026-10-01.csv : ligne 3 : oppo en double : Kess"])


ROWS = [("Phelia", 84, 5.81), ("Brigid, Clachan's Heart", 74, 5.11), ("Partner WUR", 53, 3.66), ("Tifa Lockhart", 10, 1.0)]


def test_ecriture(tmp_path):
    path = tmp_path / "meta" / "2026-09-24" / "general.csv"
    write_meta(path, ROWS)
    assert path.read_text(encoding="utf-8") == (
        "oppo,decks,poids\n"
        "Phelia,84,5.81\n"
        "\"Brigid, Clachan's Heart\",74,5.11\n"  # virgule dans le nom : entre guillemets
        "Partner WUR,53,3.66\n"
        "Tifa Lockhart,10,1\n"  # pas de zéro inutile
    )
    assert [p.name for p in path.parent.iterdir()] == ["general.csv"]  # pas de .tmp restant


def test_aller_retour(tmp_path):
    path = tmp_path / "paper.csv"
    write_meta(path, ROWS)
    assert read_meta(path, "meta/2026-09-24/paper.csv") == ({name: weight for name, _, weight in ROWS}, [])


@pytest.mark.parametrize("weight, text", [(5.8100000000000005, "5.81"), (60.0, "60"), (0.07, "0.07"), (12.345, "12.35"), (0.0, "0")])
def test_format_du_poids(tmp_path, weight, text):
    path = tmp_path / "general.csv"
    write_meta(path, [("X", 1, weight)])
    assert path.read_text(encoding="utf-8").splitlines()[1] == f"X,1,{text}"


def test_remplace_le_fichier_du_jour(tmp_path):
    path = tmp_path / "2026-09-24" / "general.csv"
    write_meta(path, ROWS)
    write_meta(path, [("Cloud", 83, 5.74)])
    assert path.read_text(encoding="utf-8") == "oppo,decks,poids\nCloud,83,5.74\n"


def test_autres_dates_intactes(tmp_path):
    old = tmp_path / "meta" / "2026-09-10" / "general.csv"
    write_meta(old, [("Cloud", 83, 5.74)])
    write_meta(tmp_path / "meta" / "2026-09-24" / "general.csv", ROWS)
    assert old.read_text(encoding="utf-8") == "oppo,decks,poids\nCloud,83,5.74\n"


def test_read_meta_message_avec_label(tmp_path):
    path = tmp_path / "paper.csv"
    path.write_text("oppo,decks,poids\nKess,2,beaucoup\n", encoding="utf-8")
    assert read_meta(path, "meta/2026-09-24/paper.csv") == (
        {}, ["meta/2026-09-24/paper.csv : ligne 2 : poids attendu en nombre positif (ex. 12.5) : beaucoup"]
    )
