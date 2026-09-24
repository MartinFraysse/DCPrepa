import pytest

from dcprepa.domain.saisie import (
    check_new_deck,
    check_new_version,
    check_status,
    check_tournament_fields,
    next_version,
    parse_card_list,
    slugify,
)


@pytest.mark.parametrize(
    "name, slug",
    [
        ("RelicFest 2026", "relicfest-2026"),
        ("Été Duel #3", "ete-duel-3"),
        ("  --Grand   Prix!!  ", "grand-prix"),
        ("Ça_va  / Là", "ca-va-la"),
        ("!!!", ""),
    ],
)
def test_slugify(name, slug):
    assert slugify(name) == slug


@pytest.mark.parametrize(
    "fields, creating, errors",
    [
        ({"name": "RelicFest 2026", "date": "31/10/2026"}, True, []),
        ({"name": "  "}, True, ["nom du tournoi vide"]),
        ({"date": "31/10/2026"}, True, ["nom du tournoi vide"]),
        ({"name": "!!!"}, True, ["nom du tournoi sans lettre ni chiffre : !!!"]),
        ({"name": "X", "date": "31/02/2026"}, True, ["date invalide (attendu : JJ/MM/AAAA) : 31/02/2026"]),
        ({"banlist": "01/09/2026"}, False, []),
        ({"date": ""}, False, []),
        ({}, False, ["rien à modifier"]),
        ({"slug": "autre"}, False, ["champ non modifiable ici : slug (possibles : name, format, date, location, banlist, notes)"]),
        ({"name": ""}, False, ["nom du tournoi vide"]),
    ],
)
def test_check_tournament_fields(fields, creating, errors):
    assert check_tournament_fields(fields, creating) == errors


DECK_INDEX = {"terra-midrange": "terra-midrange", "terra midrange": "terra-midrange", "terra": "terra-midrange"}


@pytest.mark.parametrize(
    "name, expected",
    [
        ("Kinnan Combo", ("kinnan-combo", [])),
        ("", ("", ["nom du deck vide"])),
        ("???", ("", ["nom du deck sans lettre ni chiffre : ???"])),
        ("Synthèse", ("synthese", ["nom réservé : synthese (stats/synthese.md est un fichier du tournoi)"])),
        ("README", ("readme", ["nom réservé : readme (stats/readme.md est un fichier du tournoi)"])),
        ("Terra", ("terra", ["appellation déjà prise : Terra → terra-midrange"])),
        ("Terra  Midrange", ("terra-midrange", ["appellation déjà prise : Terra Midrange → terra-midrange"])),
        ("Terra-Midrange!", ("terra-midrange", ["appellation déjà prise : terra-midrange → terra-midrange"])),
    ],
)
def test_check_new_deck(name, expected):
    assert check_new_deck(name, DECK_INDEX) == expected


def test_check_status():
    assert check_status("retenu") == [] and check_status(" ecarte ") == []
    assert check_status("écarté") == ["statut inconnu : écarté (retenu, envisage ou ecarte)"]


def test_parse_card_list():
    assert parse_card_list("1 Kinnan\n  99   Island  \n\n") == (["1 Kinnan", "99 Island"], [], [])
    assert parse_card_list("") == ([], [], [])
    assert parse_card_list("1 Kinnan\n2 Island") == (["1 Kinnan", "2 Island"], [], ["liste de 3 cartes (100 attendues, commandant compris)"])
    assert parse_card_list("Kinnan\n99 Island")[1] == ["liste : ligne 1 : attendu « 1 Nom de carte » : Kinnan"]


@pytest.mark.parametrize(
    "versions, expected",
    [(["v1", "v2", "v3"], "v4"), (["v1", "v10", "v2"], "v11"), (["beta"], "v1"), ([], "v1")],
)
def test_next_version(versions, expected):
    assert next_version(versions) == expected


@pytest.mark.parametrize(
    "version, cards_in, card_list, errors",
    [
        ("v3", ["Force of Will"], [], []),
        ("v3", [], ["1 X"], []),
        ("v2", ["Force of Will"], [], ["version déjà présente : v2"]),
        ("v 3", ["Force of Will"], [], ["identifiant de version invalide : « v 3 » (ex. v4, sans espace)"]),
        ("v3", [], [], ["version sans changement : in, out ou liste attendus"]),
    ],
)
def test_check_new_version(version, cards_in, card_list, errors):
    assert check_new_version(version, ["v1", "v2"], cards_in, [], card_list) == errors
