import pytest

from dcprepa.domain.stats import MatchupStats, Record
from dcprepa.domain.synthese import ExpectedWinrate, expected_winrate
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
