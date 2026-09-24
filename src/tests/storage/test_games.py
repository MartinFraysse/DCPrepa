from pathlib import Path

import pytest

from dcprepa.storage.games import COLUMNS, append_rows, read_games, read_match_ids

DATA_DIR = Path(__file__).resolve().parents[3] / "data"
HEADER = ",".join(COLUMNS) + "\n"

ROW = {
    "date": "02/10/2026",
    "match_id": "02/10/2026-01",
    "game": "1",
    "source": "paper",
    "deck": "terra-midrange",
    "version": "v1",
    "oppo": "Ragavan",
    "position": "OTP",
    "resultat": "W",
    "note/ressenti": "",
}
LINE = "02/10/2026,02/10/2026-01,1,paper,terra-midrange,v1,Ragavan,OTP,W,\n"


def write_games(tmp_path, text):
    path = tmp_path / "games.csv"
    path.write_text(text, encoding="utf-8", newline="")
    return path


def read_raw(path):
    with path.open(encoding="utf-8", newline="") as file:
        return file.read()


@pytest.mark.parametrize(
    "path",
    [
        DATA_DIR / "tournaments" / "relicfest-2026" / "games.csv",
        DATA_DIR / "templates" / "tournament" / "games.csv",
    ],
)
def test_vrais_fichiers_lisibles(path):
    match_ids, errors = read_match_ids(path)
    assert errors == []
    assert isinstance(match_ids, set)


def test_en_tete_seul(tmp_path):
    assert read_match_ids(write_games(tmp_path, HEADER)) == (set(), [])


def test_match_ids_lus(tmp_path):
    text = HEADER + LINE + LINE.replace("-01,1", "-01,2") + LINE.replace("-01", "-02")
    assert read_match_ids(write_games(tmp_path, text)) == ({"02/10/2026-01", "02/10/2026-02"}, [])


def test_fins_de_ligne_windows_et_bom(tmp_path):
    text = "\ufeff" + (HEADER + LINE).replace("\n", "\r\n")
    assert read_match_ids(write_games(tmp_path, text)) == ({"02/10/2026-01"}, [])


def test_fichier_absent(tmp_path):
    path = tmp_path / "games.csv"
    assert read_match_ids(path) == (set(), [f"fichier introuvable : {path}"])


@pytest.mark.parametrize(
    "text, found",
    [
        ("", "(fichier vide)"),
        ("date,match_id\n", "date,match_id"),
        (LINE, LINE.strip()),
    ],
)
def test_en_tete_inattendu(tmp_path, text, found):
    assert read_match_ids(write_games(tmp_path, text)) == (
        set(),
        [f"games.csv : en-tête inattendu : {found} (attendu : {','.join(COLUMNS)})"],
    )


def test_ajout_apres_en_tete(tmp_path):
    path = write_games(tmp_path, HEADER)
    append_rows(path, [ROW])
    assert read_raw(path) == HEADER + LINE


def test_ajout_a_la_suite(tmp_path):
    path = write_games(tmp_path, HEADER + LINE)
    append_rows(path, [{**ROW, "match_id": "02/10/2026-02"}])
    assert read_raw(path) == HEADER + LINE + LINE.replace("-01", "-02")


def test_ajout_sans_retour_a_la_ligne_final(tmp_path):
    path = write_games(tmp_path, HEADER.rstrip("\n"))
    append_rows(path, [ROW])
    assert read_raw(path) == HEADER + LINE


def test_ajout_garde_les_fins_de_ligne_windows(tmp_path):
    path = write_games(tmp_path, HEADER.replace("\n", "\r\n"))
    append_rows(path, [ROW, ROW])
    assert read_raw(path) == (HEADER + LINE + LINE).replace("\n", "\r\n")


def test_note_avec_virgule_et_guillemets(tmp_path):
    path = write_games(tmp_path, HEADER)
    append_rows(path, [{**ROW, "note/ressenti": 'serré, le "mull" paie'}])
    assert read_raw(path).endswith(',W,"serré, le ""mull"" paie"\n')
    assert read_match_ids(path) == ({"02/10/2026-01"}, [])


def test_ajout_de_rien(tmp_path):
    path = write_games(tmp_path, HEADER + LINE)
    append_rows(path, [])
    assert read_raw(path) == HEADER + LINE


def test_pas_de_fichier_temporaire_restant(tmp_path):
    append_rows(write_games(tmp_path, HEADER), [ROW])
    assert sorted(p.name for p in tmp_path.iterdir()) == ["games.csv"]


# read_games


def test_lecture_des_games(tmp_path):
    path = write_games(tmp_path, HEADER + LINE + LINE.replace(",1,", ",2,").replace("OTP,W", "OTD,L"))
    games, errors = read_games(path)
    assert errors == []
    assert games == [ROW, {**ROW, "game": "2", "position": "OTD", "resultat": "L"}]


def test_lecture_en_tete_seul(tmp_path):
    assert read_games(write_games(tmp_path, HEADER)) == ([], [])


def test_lecture_note_avec_virgule(tmp_path):
    path = write_games(tmp_path, HEADER + LINE.rstrip("\n") + '"serré, OK"\n')
    games, errors = read_games(path)
    assert errors == []
    assert games[0]["note/ressenti"] == "serré, OK"


def test_lecture_fins_de_ligne_windows(tmp_path):
    path = write_games(tmp_path, (HEADER + LINE).replace("\n", "\r\n"))
    assert read_games(path) == ([ROW], [])


def test_lecture_lignes_vides_ignorees(tmp_path):
    assert read_games(write_games(tmp_path, HEADER + "\n" + LINE + ",,,,,,,,,\n")) == ([ROW], [])


def test_lecture_fichier_absent(tmp_path):
    games, errors = read_games(tmp_path / "games.csv")
    assert games == []
    assert errors[0].startswith("fichier introuvable")


@pytest.mark.parametrize("text", ["", "date,deck\n" + LINE])
def test_lecture_en_tete_invalide(tmp_path, text):
    games, errors = read_games(write_games(tmp_path, text))
    assert games == []
    assert len(errors) == 1 and "en-tête inattendu" in errors[0]


def test_lecture_colonnes_manquantes(tmp_path):
    games, errors = read_games(write_games(tmp_path, HEADER + LINE + "02/10/2026,02/10/2026-01,1\n"))
    assert games == []
    assert errors == ["games.csv : ligne 3 : 3 colonnes au lieu de 10"]


def test_lecture_position_et_resultat_invalides(tmp_path):
    games, errors = read_games(write_games(tmp_path, HEADER + LINE.replace("OTP,W", "otp,D")))
    assert games == []
    assert errors == [
        "games.csv : ligne 2 : position inconnue (OTP ou OTD) : otp",
        "games.csv : ligne 2 : résultat inconnu (W ou L) : D",
    ]


def test_lecture_toutes_les_erreurs(tmp_path):
    text = HEADER + LINE.replace("OTP", "XX") + LINE + LINE.replace(",W,", ",N,")
    games, errors = read_games(write_games(tmp_path, text))
    assert games == []
    assert [error.split(" : ")[1] for error in errors] == ["ligne 2", "ligne 4"]


@pytest.mark.parametrize(
    "path",
    [
        DATA_DIR / "tournaments" / "relicfest-2026" / "games.csv",
        DATA_DIR / "tournaments" / "test_tournoi" / "games.csv",
        DATA_DIR / "templates" / "tournament" / "games.csv",
    ],
)
def test_lecture_des_vrais_fichiers(path):
    games, errors = read_games(path)
    assert errors == []
