from pathlib import Path

import pytest

from dcprepa.storage.oppos import load_oppos

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
