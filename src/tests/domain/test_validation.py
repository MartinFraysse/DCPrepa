import pytest
import yaml

from dcprepa.domain.validation import validate_block

DECKS = {"terra-midrange": ["v1", "v2"]}

VALID_BLOCK = {
    "date": "02/10/2026",
    "source": "paper",
    "deck": "terra-midrange",
    "version": "v1",
    "oppo": "Ragavan",
    "parties": "OTP W, OTD L, OTP W / OTD W",
    "note/ressenti": "Matchup jouable",
}

MISSING = object()


def make_block(**changes):
    """Copie du bloc valide avec des champs modifiés ; MISSING retire le champ."""
    block = dict(VALID_BLOCK)
    for field, value in changes.items():
        if value is MISSING:
            block.pop(field)
        else:
            block[field] = value
    return block


def test_bloc_valide():
    assert validate_block(make_block(), DECKS) == []


@pytest.mark.parametrize(
    "changes",
    [
        {"source": " Paper "},
        {"source": "MTGO"},
        {"source": "cockatrice"},
        {"deck": " terra-midrange "},
        {"version": "v2"},
        {"date": "29/02/2028"},
        {"note/ressenti": MISSING},
        {"note/ressenti": None},
    ],
)
def test_variantes_acceptees(changes):
    assert validate_block(make_block(**changes), DECKS) == []


@pytest.mark.parametrize("field", ["date", "source", "deck", "version", "oppo", "parties"])
@pytest.mark.parametrize("value", [MISSING, None, "", "   "])
def test_champ_obligatoire_manquant(field, value):
    assert validate_block(make_block(**{field: value}), DECKS) == [f"champ manquant : {field}"]


def test_plusieurs_champs_manquants():
    block = make_block(oppo=MISSING, parties="")
    assert validate_block(block, DECKS) == ["champ manquant : oppo", "champ manquant : parties"]


@pytest.mark.parametrize(
    "changes, expected",
    [
        ({"date": "2026-10-02"}, ["date invalide (attendu : JJ/MM/AAAA) : 2026-10-02"]),
        ({"date": "31/02/2026"}, ["date invalide (attendu : JJ/MM/AAAA) : 31/02/2026"]),
        ({"date": "29/02/2026"}, ["date invalide (attendu : JJ/MM/AAAA) : 29/02/2026"]),
        ({"date": "demain"}, ["date invalide (attendu : JJ/MM/AAAA) : demain"]),
        ({"source": "arena"}, ["source inconnue (paper, mtgo ou cockatrice) : arena"]),
        ({"deck": "terra"}, ["deck inconnu : terra (decks disponibles : terra-midrange)"]),
        ({"version": "v9"}, ["version inconnue pour terra-midrange : v9"]),
        ({"version": 3}, ["version inconnue pour terra-midrange : 3"]),
        ({"deck": "terra", "version": "v9"}, ["deck inconnu : terra (decks disponibles : terra-midrange)"]),
        (
            {"parties": "OTP W / OPP L"},
            ["parties : BO 2 : game 1 : position inconnue (OTP ou OTD) : OPP"],
        ),
    ],
)
def test_champ_invalide(changes, expected):
    assert validate_block(make_block(**changes), DECKS) == expected


def test_toutes_les_erreurs_sont_remontees():
    block = make_block(date="x", source="arena", deck="terra", parties="OTP")
    assert validate_block(block, DECKS) == [
        "date invalide (attendu : JJ/MM/AAAA) : x",
        "source inconnue (paper, mtgo ou cockatrice) : arena",
        "deck inconnu : terra (decks disponibles : terra-midrange)",
        "parties : BO 1 : game 1 : mal formée (attendu : OTP W) : OTP",
    ]


@pytest.mark.parametrize("block", ["date 02/10/2026", ["date", "source"], None])
def test_bloc_mal_forme(block):
    errors = validate_block(block, DECKS)
    assert len(errors) == 1
    assert errors[0].startswith("bloc mal formé")


def test_bloc_lu_par_yaml():
    text = (
        "date: 02/10/2026\n"
        "source: paper\n"
        "deck: terra-midrange\n"
        "version: v1\n"
        "oppo: Ragavan\n"
        "parties: OTP W, OTD L, OTP W / OTD W\n"
        "note/ressenti: Matchup jouable, le mull agressif paie.\n"
    )
    assert validate_block(yaml.safe_load(text), DECKS) == []


def test_pieges_yaml():
    text = (
        "date: 2026-10-02\n"
        "source: paper\n"
        "deck: terra-midrange\n"
        "version: 1.10\n"
        "oppo: Ragavan\n"
        "parties: OTP W\n"
    )
    decks = {"terra-midrange": ["1.10"]}
    assert validate_block(yaml.safe_load(text), decks) == [
        "date invalide (attendu : JJ/MM/AAAA) : 2026-10-02",
        "version inconnue pour terra-midrange : 1.1",
    ]
