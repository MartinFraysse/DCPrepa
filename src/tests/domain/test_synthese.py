import pytest

from dcprepa.domain.stats import MatchupStats, Record
from dcprepa.domain.synthese import ExpectedWinrate, UntestedMatchup, expected_winrate, untested_matchups
from dcprepa.domain.winrate import Winrate


def matchup(oppo, games, bo3=(0, 0), *, paper=None, general=None):
    """Un matchup : games et BO3 écrits (victoires, total), poids papier / général en %."""
    return MatchupStats(
        oppo, Record(Winrate(*games), Winrate(*bo3)), None, None, weight_paper=paper, weight_general=general
    )


@pytest.fixture
def exemple():
    """L'exemple du plan : Cloud 6 % (69.2 %), Phelia 5.2 % (35 %), Aragorn 5 % (41.9 %)."""
    return [
        matchup("Cloud", (9, 13), paper=6, general=4),
        matchup("Phelia", (7, 20), paper=5.2),
        matchup("Aragorn", (13, 31), paper=5, general=3),
    ]


def test_exemple_du_plan(exemple):
    expected = expected_winrate(exemple, "paper", "games")
    assert expected.rate == pytest.approx((6 * 900 / 13 + 5.2 * 35 + 5 * 1300 / 31) / 16.2)
    assert expected.coverage == pytest.approx(16.2)
    assert str(expected) == "⚠️ 49.8 % (16.2 % du méta)"


def test_meta_general(exemple):
    expected = expected_winrate(exemple, "general", "games")
    assert expected.coverage == pytest.approx(7)
    assert expected.rate == pytest.approx((4 * 900 / 13 + 3 * 1300 / 31) / 7)


def test_oppo_hors_meta_ignore(exemple):
    hors_meta = exemple + [matchup("Kinnan", (0, 40))]
    assert expected_winrate(hors_meta, "paper", "games") == expected_winrate(exemple, "paper", "games")


def test_oppo_sans_game_ignore(exemple):
    sans_game = exemple + [matchup("Kraum", (0, 0), paper=8)]
    assert expected_winrate(sans_game, "paper", "games") == expected_winrate(exemple, "paper", "games")


def test_bo3_oppo_sans_bo3_ignore():
    matchups = [
        matchup("Cloud", (5, 8), (2, 3), paper=20),
        matchup("Phelia", (1, 1), (0, 0), paper=15),  # un BO1 seulement
    ]
    expected = expected_winrate(matchups, "paper", "bo3")
    assert expected.rate == pytest.approx(200 / 3)
    assert expected.coverage == pytest.approx(20)


def test_aucun_oppo_joue():
    expected = expected_winrate([matchup("Kinnan", (3, 5))], "paper", "games")
    assert expected == ExpectedWinrate(None, 0.0)
    assert str(expected) == "—"
    assert str(expected_winrate([], "general", "bo3")) == "—"


@pytest.mark.parametrize(
    "paper, text",
    [
        (29.9, "⚠️ 50 % (29.9 % du méta)"),
        (30, "50 % (30 % du méta)"),
    ],
)
def test_avertissement_sous_30_pourcent(paper, text):
    assert str(expected_winrate([matchup("Cloud", (1, 2), paper=paper)], "paper", "games")) == text


@pytest.mark.parametrize("meta, base", [("papier", "games"), ("paper", "game")])
def test_meta_ou_base_inconnu(meta, base):
    with pytest.raises(ValueError):
        expected_winrate([], meta, base)


def paper_meta(count=12):
    """Méta papier de test : Oppo1 (poids 30) … Oppo12 (poids 8), rang = numéro."""
    return {f"Oppo{number}": 32 - 2 * number for number in range(1, count + 1)}


def oppos_of(untested, deck="cloud"):
    return [row.oppo for row in untested if row.deck == deck]


def test_non_testes_deck_sans_game_top_10_seulement():
    untested = untested_matchups({"cloud": ("retenu", [])}, paper_meta())
    assert oppos_of(untested) == [f"Oppo{number}" for number in range(1, 11)]
    assert untested[0] == UntestedMatchup("cloud", "Oppo1", 1, 30, 0, 0)


@pytest.mark.parametrize(
    "games, bo3, tested",
    [
        ((0, 29), (0, 9), False),
        ((0, 30), (0, 9), True),
        ((0, 29), (0, 10), True),
        ((0, 40), (0, 12), True),
    ],
)
def test_seuils_exacts(games, bo3, tested):
    matchups = [matchup("Oppo1", games, bo3, paper=30)]
    untested = untested_matchups({"cloud": ("envisage", matchups)}, paper_meta())
    assert ("Oppo1" not in oppos_of(untested)) is tested


def test_compteurs_du_matchup_partiellement_joue():
    matchups = [matchup("Oppo3", (10, 17), (3, 6), paper=26)]
    untested = untested_matchups({"cloud": ("retenu", matchups)}, paper_meta())
    assert UntestedMatchup("cloud", "Oppo3", 3, 26, 6, 17) in untested


@pytest.mark.parametrize("status", ["ecarte", "", "Retenu"])
def test_deck_ni_retenu_ni_envisage_ignore(status):
    assert untested_matchups({"cloud": (status, [])}, paper_meta()) == []


def test_ordre_decks_puis_rang_et_egalite_par_nom():
    paper = {"b": 10, "A": 10, "c": 20}
    untested = untested_matchups({"terra": ("envisage", []), "cloud": ("retenu", [])}, paper)
    assert [(row.deck, row.oppo, row.rank) for row in untested] == [
        ("terra", "c", 1), ("terra", "A", 2), ("terra", "b", 3),
        ("cloud", "c", 1), ("cloud", "A", 2), ("cloud", "b", 3),
    ]


def test_sans_meta_papier():
    assert untested_matchups({"cloud": ("retenu", [])}, {}) == []
