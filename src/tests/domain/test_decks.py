import pytest

from dcprepa.domain.decks import resolve_deck, resolve_self_play
from dcprepa.domain.names import build_name_index


@pytest.fixture
def index():
    index, errors = build_name_index(
        {
            "terra-5c": ["terra-5c", "Terra 5C", "Terra", "Terra mid"],
            "tymna-thrasios": ["tymna-thrasios", "Tymna Thrasios", "TnT"],
        },
        "decks",
    )
    assert errors == []
    return index


@pytest.mark.parametrize(
    "name, expected",
    [
        ("terra-5c", "terra-5c"),
        ("Terra 5C", "terra-5c"),
        ("terra", "terra-5c"),
        ("  TERRA   Mid ", "terra-5c"),
        ("tnt", "tymna-thrasios"),
        ("Tymna thrasios", "tymna-thrasios"),
    ],
)
def test_deck_reconnu(index, name, expected):
    assert resolve_deck(name, index) == expected


@pytest.mark.parametrize("name", ["terra_5c", "Atraxa", ""])
def test_deck_inconnu(index, name):
    assert resolve_deck(name, index) is None


@pytest.mark.parametrize(
    "oppo, expected",
    [
        ("terra-5c@v1", "terra-5c@v1"),
        ("Terra mid@v2", "terra-5c@v2"),
        ("  terra  @ v1 ", "terra-5c@v1"),
        ("TnT@v3", "tymna-thrasios@v3"),
    ],
)
def test_self_play_reconnu(index, oppo, expected):
    assert resolve_self_play(oppo, index) == (expected, None)


def test_self_play_deck_inconnu(index):
    assert resolve_self_play("atraxa@v1", index) == ("atraxa@v1", "self-play : deck inconnu : atraxa")
