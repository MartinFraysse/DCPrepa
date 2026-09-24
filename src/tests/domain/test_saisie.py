import pytest

from dcprepa.domain.saisie import check_tournament_fields, slugify


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
