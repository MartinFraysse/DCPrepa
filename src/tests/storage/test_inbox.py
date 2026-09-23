from pathlib import Path

import pytest

from dcprepa.storage.inbox import clear_inbox, read_inbox

DATA_DIR = Path(__file__).resolve().parents[3] / "data"

HEADER = "# Boîte de réception\n# Un bloc par session, blocs séparés par ---\n#\n# date: 02/10/2026\n# ---\n\n"

BLOCK_A = "date: 02/10/2026\nsource: paper\nparties: OTP W, OTD L, OTP W\n"
BLOCK_B = "date: 03/10/2026\nsource: mtgo\nparties: OTD W\n"
DATA_A = {"date": "02/10/2026", "source": "paper", "parties": "OTP W, OTD L, OTP W"}
DATA_B = {"date": "03/10/2026", "source": "mtgo", "parties": "OTD W"}


def write_inbox(tmp_path, text):
    path = tmp_path / "inbox.yaml"
    path.write_text(text, encoding="utf-8", newline="")
    return path


@pytest.mark.parametrize(
    "path",
    [
        DATA_DIR / "tournaments" / "relicfest-2026" / "inbox.yaml",
        DATA_DIR / "templates" / "tournament" / "inbox.yaml",
    ],
)
def test_vraies_inbox_vides(path):
    assert read_inbox(path) == ([], [])


def test_fichier_absent(tmp_path):
    path = tmp_path / "inbox.yaml"
    assert read_inbox(path) == ([], [f"fichier introuvable : {path}"])


@pytest.mark.parametrize("text", ["", HEADER, "\n\n", "---\n", "---\n---\n", "# commentaire\n---\n# autre\n"])
def test_inbox_sans_bloc(tmp_path, text):
    assert read_inbox(write_inbox(tmp_path, text)) == ([], [])


@pytest.mark.parametrize(
    "text",
    [
        BLOCK_A,
        HEADER + BLOCK_A,
        HEADER + BLOCK_A + "---\n",
        "---\n" + BLOCK_A,
        HEADER + "\n\n" + BLOCK_A + "\n\n",
    ],
)
def test_un_bloc(tmp_path, text):
    assert read_inbox(write_inbox(tmp_path, text)) == ([DATA_A], [])


@pytest.mark.parametrize(
    "text",
    [
        BLOCK_A + "---\n" + BLOCK_B,
        HEADER + BLOCK_A + "---\n" + BLOCK_B + "---\n",
        BLOCK_A + "---\n---\n" + BLOCK_B,
        BLOCK_A + "  ---  \n" + BLOCK_B,
        BLOCK_A + "---\n# commentaire entre deux blocs\n\n" + BLOCK_B,
    ],
)
def test_deux_blocs(tmp_path, text):
    assert read_inbox(write_inbox(tmp_path, text)) == ([DATA_A, DATA_B], [])


def test_fins_de_ligne_windows(tmp_path):
    text = (BLOCK_A + "---\n" + BLOCK_B).replace("\n", "\r\n")
    assert read_inbox(write_inbox(tmp_path, text)) == ([DATA_A, DATA_B], [])


def test_accents_et_deux_points_dans_la_note(tmp_path):
    text = 'note/ressenti: "Matchup jouable : le mull paie, Éowyn au top"\n'
    blocks, errors = read_inbox(write_inbox(tmp_path, text))
    assert errors == []
    assert blocks == [{"note/ressenti": "Matchup jouable : le mull paie, Éowyn au top"}]


def test_tirets_dans_une_valeur_ne_separent_pas(tmp_path):
    text = "note/ressenti: parties serrées --- à revoir\nsource: paper\n"
    assert read_inbox(write_inbox(tmp_path, text)) == (
        [{"note/ressenti": "parties serrées --- à revoir", "source": "paper"}],
        [],
    )


def test_bloc_non_dictionnaire_renvoye_tel_quel(tmp_path):
    assert read_inbox(write_inbox(tmp_path, "juste du texte\n")) == (["juste du texte"], [])


def test_bloc_illisible(tmp_path):
    text = BLOCK_A + "---\n# commentaire\nnote/ressenti: a: b\n"
    assert read_inbox(write_inbox(tmp_path, text)) == (
        [],
        ["bloc 2 : YAML illisible ligne 6 : mapping values are not allowed here"],
    )


def test_tout_ou_rien_et_toutes_les_erreurs(tmp_path):
    text = (
        BLOCK_A              # lignes 1-3   bloc 1 : valide
        + "---\n"            # ligne 4
        + "note: a: b\n"     # ligne 5      bloc 2 : illisible
        + "---\n"            # ligne 6
        + BLOCK_B            # lignes 7-9   bloc 3 : valide
        + "---\n"            # ligne 10
        + "parties: [OTP\n"  # ligne 11     bloc 4 : illisible
    )
    blocks, errors = read_inbox(write_inbox(tmp_path, text))
    assert blocks == []
    assert len(errors) == 2
    assert errors[0].startswith("bloc 2 : YAML illisible ligne 5 :")
    assert errors[1].startswith("bloc 4 : YAML illisible ligne 11 :")


def read_raw(path):
    with path.open(encoding="utf-8", newline="") as file:
        return file.read()


@pytest.mark.parametrize(
    "text",
    [
        HEADER + BLOCK_A,
        HEADER + BLOCK_A + "---\n" + BLOCK_B + "---\n",
        HEADER + "---\n" + BLOCK_A,
        HEADER,
    ],
)
def test_clear_inbox_garde_l_en_tete(tmp_path, text):
    path = write_inbox(tmp_path, text)
    clear_inbox(path)
    assert read_raw(path) == HEADER
    assert read_inbox(path) == ([], [])


def test_clear_inbox_sans_en_tete(tmp_path):
    path = write_inbox(tmp_path, BLOCK_A + "---\n" + BLOCK_B)
    clear_inbox(path)
    assert read_raw(path) == ""


def test_clear_inbox_garde_les_fins_de_ligne_windows(tmp_path):
    path = write_inbox(tmp_path, (HEADER + BLOCK_A).replace("\n", "\r\n"))
    clear_inbox(path)
    assert read_raw(path) == HEADER.replace("\n", "\r\n")


def test_clear_inbox_ne_laisse_pas_de_fichier_temporaire(tmp_path):
    clear_inbox(write_inbox(tmp_path, HEADER + BLOCK_A))
    assert sorted(p.name for p in tmp_path.iterdir()) == ["inbox.yaml"]


def test_clear_inbox_sur_le_vrai_modele_ne_change_rien(tmp_path):
    original = read_raw(DATA_DIR / "templates" / "tournament" / "inbox.yaml")
    path = write_inbox(tmp_path, original + "date: 02/10/2026\nsource: paper\n")
    clear_inbox(path)
    assert read_raw(path) == original


def test_clear_inbox_fichier_absent(tmp_path):
    with pytest.raises(FileNotFoundError):
        clear_inbox(tmp_path / "inbox.yaml")

