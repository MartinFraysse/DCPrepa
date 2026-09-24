from datetime import date
from pathlib import Path

import pytest

from dcprepa.services.oppos import add_oppo
from dcprepa.storage.oppos import load_oppos

OPPOS_TEXT = "# Oppos\nRagavan:\n    - raga\nKess:\n"
TODAY = date(2026, 9, 24)


@pytest.fixture
def oppos(tmp_path):
    path = tmp_path / "oppos.yaml"
    path.write_text(OPPOS_TEXT, encoding="utf-8")
    return path


def test_nouvel_oppo(oppos):
    report = add_oppo(oppos, "  Atraxa ", today=TODAY)
    assert (report.ok, report.name, report.reference) == (True, "Atraxa", "Atraxa")
    assert oppos.read_text(encoding="utf-8") == OPPOS_TEXT + "\n# Ajouté par la saisie le 24/09/2026\nAtraxa:\n"
    assert load_oppos(oppos)[0]["Atraxa"] == []


def test_variante(oppos):
    report = add_oppo(oppos, "Ragavn", variant_of="RAGA")
    assert (report.ok, report.name, report.reference) == (True, "Ragavn", "Ragavan")
    assert load_oppos(oppos)[0]["Ragavan"] == ["raga", "Ragavn"]


def test_variante_d_un_oppo_sans_variante(oppos):
    assert add_oppo(oppos, "Kess, Dissident Mage", variant_of="Kess").ok
    assert load_oppos(oppos)[0]["Kess"] == ["Kess, Dissident Mage"]


@pytest.mark.parametrize(
    "name, variant_of, error",
    [
        ("raga", None, "oppo déjà connu : raga → Ragavan"),
        ("Kinnan", "Atraxa", "oppo de référence inconnu : Atraxa"),
        ("", None, "nom d'oppo vide"),
    ],
)
def test_refus_rien_n_est_ecrit(oppos, name, variant_of, error):
    report = add_oppo(oppos, name, variant_of=variant_of)
    assert report.errors == [error] and report.name is None
    assert oppos.read_text(encoding="utf-8") == OPPOS_TEXT


def test_oppos_ambigu(oppos):
    oppos.write_text("Ragavan:\n    - raga\nKess:\n    - raga\n", encoding="utf-8")
    report = add_oppo(oppos, "Atraxa")
    assert report.errors == ["oppos.yaml : « raga » renvoie à la fois vers Ragavan et Kess"]


def test_le_vrai_fichier_accepte_une_variante(tmp_path):
    """data/oppos.yaml du dépôt, copié : une variante s'insère sous une référence ajoutée par meta."""
    source = Path(__file__).resolve().parents[3] / "data" / "oppos.yaml"
    path = tmp_path / "oppos.yaml"
    path.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    before, _ = load_oppos(path)
    reference = next(iter(before))
    assert add_oppo(path, "Variante de test", variant_of=reference).ok
    after, errors = load_oppos(path)
    assert errors == [] and after[reference] == before[reference] + ["Variante de test"]
    assert {name: variants for name, variants in after.items() if name != reference} == {
        name: variants for name, variants in before.items() if name != reference
    }
