import pytest

from dcprepa.domain.winrate import Winrate, format_percent


def test_aucune_partie():
    winrate = Winrate(0, 0)
    assert str(winrate) == "—"
    assert winrate.rate is None
    assert not winrate.reliable


@pytest.mark.parametrize(
    "wins, total, expected",
    [
        (66, 120, "55 % (66/120)"),
        (5, 10, "50 % (5/10)"),
        (10, 10, "100 % (10/10)"),
        (0, 12, "0 % (0/12)"),
        (10, 15, "66.7 % (10/15)"),
        (11, 90, "12.2 % (11/90)"),
    ],
)
def test_affichage_fiable(wins, total, expected):
    assert str(Winrate(wins, total)) == expected


@pytest.mark.parametrize(
    "wins, total, expected",
    [
        (1, 3, "⚠️ 33.3 % (1/3)"),
        (2, 4, "⚠️ 50 % (2/4)"),
        (9, 9, "⚠️ 100 % (9/9)"),
        (0, 1, "⚠️ 0 % (0/1)"),
    ],
)
def test_affichage_moins_de_10(wins, total, expected):
    assert str(Winrate(wins, total)) == expected


def test_seuil_10():
    assert not Winrate(5, 9).reliable
    assert Winrate(5, 10).reliable


def test_rate_exact():
    assert Winrate(1, 8).rate == 12.5
    assert Winrate(10, 15).rate == pytest.approx(66.6667, abs=1e-4)


@pytest.mark.parametrize(
    "value, expected",
    [
        (55.0, "55"),
        (12.2, "12.2"),
        (12.25, "12.3"),  # 0,05 arrondi au-dessus
        (12.24, "12.2"),
        (66.666, "66.7"),
        (99.96, "100"),
        (0.04, "0"),
        (3.2, "3.2"),
        (-3.2, "-3.2"),
        (-0.04, "0"),
    ],
)
def test_format_percent(value, expected):
    assert format_percent(value) == expected


@pytest.mark.parametrize("wins, total", [(-1, 5), (6, 5), (1, 0), (0, -1)])
def test_winrate_impossible(wins, total):
    with pytest.raises(ValueError, match="winrate impossible"):
        Winrate(wins, total)
