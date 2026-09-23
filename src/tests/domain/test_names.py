import pytest

from dcprepa.domain.names import build_name_index, name_key


@pytest.mark.parametrize(
    "name, expected",
    [
        ("Terra", "terra"),
        ("  TERRA   mid  ", "terra mid"),
        ("Terra\t5C", "terra 5c"),
        ("", ""),
        (42, "42"),
    ],
)
def test_name_key(name, expected):
    assert name_key(name) == expected


def test_index_references_et_variantes():
    index, errors = build_name_index({"terra-5c": ["Terra 5C", "Terra", "Terra mid"]}, "decks")
    assert errors == []
    assert index == {"terra-5c": "terra-5c", "terra 5c": "terra-5c", "terra": "terra-5c", "terra mid": "terra-5c"}


def test_source_dans_le_message_d_ambiguite():
    assert build_name_index({"terra-5c": ["Terra"], "terra-mono": ["terra"]}, "decks") == (
        {},
        ["decks : « terra » renvoie à la fois vers terra-5c et terra-mono"],
    )
