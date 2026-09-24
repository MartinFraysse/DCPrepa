from pathlib import Path

import pytest

from dcprepa.storage.oppos import append_oppos, insert_variant, load_oppos

DATA_DIR = Path(__file__).resolve().parents[3] / "data"


def write_oppos(tmp_path, text):
    path = tmp_path / "oppos.yaml"
    path.write_text(text, encoding="utf-8")
    return path


def test_vrai_fichier_lisible():
    oppos, errors = load_oppos(DATA_DIR / "oppos.yaml")
    assert errors == []
    assert isinstance(oppos, dict)


def test_fichier_absent(tmp_path):
    path = tmp_path / "oppos.yaml"
    assert load_oppos(path) == ({}, [f"fichier introuvable : {path}"])


@pytest.mark.parametrize("text", ["", "# seulement des commentaires\n", "\n\n"])
def test_fichier_sans_entree(tmp_path, text):
    assert load_oppos(write_oppos(tmp_path, text)) == ({}, [])


def test_references_et_variantes(tmp_path):
    text = (
        "Ragavan:\n"
        "    - Ragavan, Nimble Pilferer\n"
        "    - raga\n"
        "Tymna/Thrasios:\n"
        "    - Tymna Thrasios\n"
    )
    assert load_oppos(write_oppos(tmp_path, text)) == (
        {"Ragavan": ["Ragavan, Nimble Pilferer", "raga"], "Tymna/Thrasios": ["Tymna Thrasios"]},
        [],
    )


@pytest.mark.parametrize("text", ["Ragavan:\n", "Ragavan: []\n", "Ragavan:\n    -\n"])
def test_reference_sans_variante(tmp_path, text):
    assert load_oppos(write_oppos(tmp_path, text)) == ({"Ragavan": []}, [])


def test_valeurs_converties_en_texte_et_nettoyees(tmp_path):
    text = "Kess:\n    - 42\n    - '  kess  '\n"
    assert load_oppos(write_oppos(tmp_path, text)) == ({"Kess": ["42", "kess"]}, [])


def test_variantes_pas_en_liste(tmp_path):
    assert load_oppos(write_oppos(tmp_path, "Ragavan: raga\n")) == (
        {},
        ["oppos.yaml : Ragavan : variantes attendues sous forme de liste (« - variante »)"],
    )


@pytest.mark.parametrize("text", ["- Ragavan\n- Kess\n", "juste du texte\n"])
def test_structure_invalide(tmp_path, text):
    assert load_oppos(write_oppos(tmp_path, text)) == (
        {},
        ["oppos.yaml : attendu « Nom de référence: » suivi de ses variantes"],
    )


def test_yaml_illisible(tmp_path):
    oppos, errors = load_oppos(write_oppos(tmp_path, "Ragavan: [raga\n"))
    assert oppos == {}
    assert len(errors) == 1
    assert errors[0].startswith("oppos.yaml : YAML illisible")


ORIGINAL = "# Noms de référence des decks adverses.\n\nRagavan:\n    - raga\n"
NEW = {"Phelia": ["Phelia, Exuberant Shepherd"], "Tifa Lockhart": [], "Brigid": ["Brigid, Clachan's Heart"]}


def test_ajout_a_la_fin(tmp_path):
    path = tmp_path / "oppos.yaml"
    path.write_text(ORIGINAL, encoding="utf-8")
    append_oppos(path, NEW, "Ajoutés par l'import du méta du 24/09/2026")
    assert path.read_text(encoding="utf-8") == (
        ORIGINAL
        + "\n# Ajoutés par l'import du méta du 24/09/2026\n"
        + "Phelia:\n    - Phelia, Exuberant Shepherd\n"
        + "Tifa Lockhart:\n"
        + "Brigid:\n    - Brigid, Clachan's Heart\n"
    )
    assert [p.name for p in tmp_path.iterdir()] == ["oppos.yaml"]  # pas de .tmp restant


def test_ajout_relu_par_load_oppos(tmp_path):
    path = tmp_path / "oppos.yaml"
    path.write_text(ORIGINAL, encoding="utf-8")
    append_oppos(path, {**NEW, "a: b": ["- x", "yes"]}, "Ajout")
    oppos, errors = load_oppos(path)
    assert errors == []
    assert oppos == {"Ragavan": ["raga"], **NEW, "a: b": ["- x", "yes"]}


def test_fichier_sans_fin_de_ligne(tmp_path):
    path = tmp_path / "oppos.yaml"
    path.write_text("Ragavan:\n    - raga", encoding="utf-8")
    append_oppos(path, {"Tifa Lockhart": []}, "Ajout")
    assert path.read_text(encoding="utf-8") == "Ragavan:\n    - raga\n\n# Ajout\nTifa Lockhart:\n"


def test_rien_a_ajouter(tmp_path):
    path = tmp_path / "oppos.yaml"
    path.write_text(ORIGINAL, encoding="utf-8")
    append_oppos(path, {}, "Ajout")
    assert path.read_text(encoding="utf-8") == ORIGINAL


def test_ajout_au_vrai_fichier(tmp_path):
    path = tmp_path / "oppos.yaml"
    path.write_text((DATA_DIR / "oppos.yaml").read_text(encoding="utf-8"), encoding="utf-8")
    before, _ = load_oppos(path)
    append_oppos(path, NEW, "Ajout")
    after, errors = load_oppos(path)
    assert errors == []
    assert after == {**before, **NEW}


OPPOS_TEXT = (
    "# Noms de référence\n"
    "Ragavan:\n"
    "    - raga\n"
    "    # commentaire dans le bloc\n"
    "\n"
    '"Tymna/Thrasios":\n'
    "Kess:\n"
    "    - kess\n"
)


@pytest.mark.parametrize(
    "reference, variant, expected",
    [
        ("Ragavan", "Ragavn", OPPOS_TEXT.replace("    # commentaire dans le bloc\n", "    # commentaire dans le bloc\n    - Ragavn\n")),
        ("Tymna/Thrasios", "Tymna Thrasios", OPPOS_TEXT.replace('"Tymna/Thrasios":\n', '"Tymna/Thrasios":\n    - Tymna Thrasios\n')),
        ("Kess", "Kess, Dissident Mage", OPPOS_TEXT + "    - Kess, Dissident Mage\n"),
    ],
)
def test_insert_variant(tmp_path, reference, variant, expected):
    path = write_oppos(tmp_path, OPPOS_TEXT)
    assert insert_variant(path, reference, variant) is True
    assert path.read_text(encoding="utf-8") == expected
    oppos, errors = load_oppos(path)
    assert errors == [] and variant in oppos[reference]


def test_insert_variant_fichier_sans_fin_de_ligne(tmp_path):
    path = write_oppos(tmp_path, "Kess:\n    - kess")
    assert insert_variant(path, "Kess", "Kess2")
    assert path.read_text(encoding="utf-8") == "Kess:\n    - kess\n    - Kess2"


def test_insert_variant_reference_introuvable(tmp_path):
    path = write_oppos(tmp_path, OPPOS_TEXT)
    assert insert_variant(path, "Atraxa", "atra") is False
    assert path.read_text(encoding="utf-8") == OPPOS_TEXT
    assert not (tmp_path / "oppos.yaml.tmp").exists()
