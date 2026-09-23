import pytest

from dcprepa.domain.oppos import build_oppo_index, normalize_oppo

OPPOS = {
    "Ragavan": ["Ragavan, Nimble Pilferer", "raga"],
    "Tymna/Thrasios": ["Tymna Thrasios", "Thrasios/Tymna"],
    "Kess": [],
}


@pytest.fixture
def index():
    index, errors = build_oppo_index(OPPOS)
    assert errors == []
    return index


def test_index_contient_references_et_variantes(index):
    assert index == {
        "ragavan": "Ragavan",
        "ragavan, nimble pilferer": "Ragavan",
        "raga": "Ragavan",
        "tymna/thrasios": "Tymna/Thrasios",
        "tymna thrasios": "Tymna/Thrasios",
        "thrasios/tymna": "Tymna/Thrasios",
        "kess": "Kess",
    }


def test_index_vide():
    assert build_oppo_index({}) == ({}, [])


def test_variante_egale_a_sa_reference_acceptee():
    assert build_oppo_index({"Ragavan": ["ragavan", "RAGAVAN"]}) == ({"ragavan": "Ragavan"}, [])


def test_variante_vide_ignoree():
    assert build_oppo_index({"Ragavan": ["", "   "]}) == ({"ragavan": "Ragavan"}, [])


@pytest.mark.parametrize(
    "oppos, message",
    [
        (
            {"Ragavan": ["raga"], "Kess": ["raga"]},
            "oppos.yaml : « raga » renvoie à la fois vers Ragavan et Kess",
        ),
        (
            {"Ragavan": [], "Kess": ["RAGAVAN"]},
            "oppos.yaml : « RAGAVAN » renvoie à la fois vers Ragavan et Kess",
        ),
    ],
)
def test_index_ambigu(oppos, message):
    assert build_oppo_index(oppos) == ({}, [message])


@pytest.mark.parametrize(
    "oppo, expected",
    [
        ("Ragavan", "Ragavan"),
        ("raga", "Ragavan"),
        ("RAGA", "Ragavan"),
        ("  Raga  ", "Ragavan"),
        ("ragavan,   nimble pilferer", "Ragavan"),
        ("tymna thrasios", "Tymna/Thrasios"),
        ("Thrasios/Tymna", "Tymna/Thrasios"),
        ("kess", "Kess"),
    ],
)
def test_oppo_connu(index, oppo, expected):
    assert normalize_oppo(oppo, index) == (expected, None)


@pytest.mark.parametrize(
    "oppo, expected",
    [
        ("Atraxa", "Atraxa"),
        ("  Atraxa   Grand  Unifier ", "Atraxa Grand Unifier"),
        ("ragav", "ragav"),
    ],
)
def test_oppo_inconnu_garde_avec_avertissement(index, oppo, expected):
    assert normalize_oppo(oppo, index) == (
        expected,
        f"oppo inconnu : {expected} → à ajouter dans data/oppos.yaml",
    )


@pytest.mark.parametrize("oppo", ["terra-midrange@v1", " terra-midrange@v2 "])
def test_self_play_garde_tel_quel(index, oppo):
    assert normalize_oppo(oppo, index) == (oppo.strip(), None)


def test_index_vide_tout_est_inconnu():
    assert normalize_oppo("Ragavan", {}) == (
        "Ragavan",
        "oppo inconnu : Ragavan → à ajouter dans data/oppos.yaml",
    )
