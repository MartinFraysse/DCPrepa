import pytest

from dcprepa.domain.stats import bo3_matches, compute_deck_stats, record, version_gaps
from dcprepa.domain.winrate import Winrate


def game(match_id, resultat, *, deck="terra", version="v1", oppo="Ragavan", source="paper", position="OTP"):
    return {
        "date": "01/11/2026", "match_id": match_id, "partie": "1", "source": source, "deck": deck,
        "version": version, "oppo": oppo, "position": position, "resultat": resultat, "note/ressenti": "",
    }


def match(match_id, results, **fields):
    """Un match écrit comme « WLW » : une game par lettre, positions alternées à partir d'OTP."""
    return [
        game(match_id, result, position=("OTP", "OTD")[number % 2], **fields)
        for number, result in enumerate(results)
    ]


@pytest.fixture
def exemple():
    """L'exemple des conventions : 4 BO3 (WLW, WW, LWL, LWL) + 4 BO1 gagnés = 15 parties."""
    games = []
    for number, results in enumerate(["WLW", "WW", "LWL", "LWL", "W", "W", "W", "W"], start=1):
        games += match(f"m{number}", results)
    return games


def test_exemple_des_conventions(exemple):
    rec = record(exemple)
    assert rec.games == Winrate(10, 15)
    assert rec.bo3 == Winrate(2, 4)
    assert str(rec.games) == "66.7 % (10/15)"
    assert str(rec.bo3) == "⚠️ 50 % (2/4)"


def test_bo3_2_ou_3_games_bo1_exclu():
    games = match("a", "W") + match("b", "WW") + match("c", "LWL")
    assert [len(m) for m in bo3_matches(games)] == [2, 3]


def test_bo3_nul_non_gagne():
    rec = record(match("a", "WL"))
    assert rec.bo3 == Winrate(0, 1)
    assert rec.games == Winrate(1, 2)


def test_aucune_partie():
    stats = compute_deck_stats([], "terra", ["v1"])
    assert str(stats.overall.games) == "—"
    assert str(stats.overall.bo3) == "—"
    assert [(v.version, v.gap_games, v.gap_bo3) for v in stats.versions] == [("v1", None, None)]
    assert all(w.total == 0 for w in stats.positions.values())
    assert list(stats.sources) == ["paper", "cockatrice", "mtgo"]
    assert stats.matchups == []
    assert stats.self_play == []


def test_autres_decks_ignores():
    games = match("a", "WW") + match("b", "LL", deck="autre")
    assert compute_deck_stats(games, "terra", ["v1"]).overall.games == Winrate(2, 2)


def test_self_play_exclu_de_tout():
    games = match("a", "WW") + match("b", "LLL", oppo="terra@v1", version="v2")
    stats = compute_deck_stats(games, "terra", ["v1", "v2"])
    assert stats.overall == record(match("a", "WW"))
    assert stats.positions["OTD"] == Winrate(1, 1)
    assert [m.oppo for m in stats.matchups] == ["Ragavan"]
    assert stats.versions[1].record.games.total == 0
    assert [(m.oppo, m.record.games, m.record.bo3) for m in stats.self_play] == [
        ("terra@v1", Winrate(0, 3), Winrate(0, 1))
    ]


def test_positions_par_partie():
    stats = compute_deck_stats(match("a", "WLW") + match("b", "LW"), "terra", ["v1"])
    # OTP : W, W, L ; OTD : L, W
    assert stats.positions == {"OTP": Winrate(2, 3), "OTD": Winrate(1, 2)}


def test_sources_parties_et_bo3():
    games = match("a", "WW", source="mtgo") + match("b", "W", source="mtgo") + match("c", "LL")
    sources = compute_deck_stats(games, "terra", ["v1"]).sources
    assert sources["mtgo"] == record(match("a", "WW") + match("b", "W"))
    assert sources["mtgo"].games == Winrate(3, 3)
    assert sources["mtgo"].bo3 == Winrate(1, 1)
    assert sources["paper"].bo3 == Winrate(0, 1)
    assert sources["cockatrice"].games.total == 0


def test_versions_ordre_fiche_puis_inconnues():
    games = match("a", "W", version="v9") + match("b", "W", version="v2")
    stats = compute_deck_stats(games, "terra", ["v1", "v2"])
    assert [v.version for v in stats.versions] == ["v1", "v2", "v9"]


def test_ecarts_parties_et_bo3_distincts():
    games = (
        match("a", "WW", version="v1") + match("b", "LL", version="v1")  # parties 50 %, BO3 50 %
        + match("c", "WW", version="v2") + match("d", "W", version="v2")  # parties 100 %, BO3 100 %
        + match("e", "L", version="v3")  # parties 0 %, pas de BO3
    )
    versions = {v.version: v for v in compute_deck_stats(games, "terra", ["v1", "v2", "v3"]).versions}
    assert versions["v1"].gap_games == pytest.approx(50 - (100 + 0) / 2)
    assert versions["v2"].gap_games == pytest.approx(100 - (50 + 0) / 2)
    assert versions["v3"].gap_games == pytest.approx(0 - (50 + 100) / 2)
    assert versions["v1"].gap_bo3 == pytest.approx(50 - 100)
    assert versions["v2"].gap_bo3 == pytest.approx(100 - 50)
    assert versions["v3"].gap_bo3 is None


@pytest.mark.parametrize(
    "rates, expected",
    [
        ({"v1": 60.0}, {"v1": None}),
        ({"v1": 60.0, "v2": None}, {"v1": None, "v2": None}),
        ({"v1": 60.0, "v2": 50.0, "v3": 40.0}, {"v1": 15.0, "v2": 0.0, "v3": -15.0}),
    ],
)
def test_version_gaps(rates, expected):
    assert version_gaps(rates) == expected


def test_matchups_tri_et_otp_otd_des_10_parties():
    games = (
        match("a", "WL", oppo="Kess") + match("b", "WLW", oppo="Kess")  # 5 parties
        + [game(f"r{n}", "W", oppo="Ragavan", position=("OTP", "OTD")[n % 2]) for n in range(10)]  # 10 BO1
        + match("c", "WW", oppo="Atraxa") + match("d", "LWL", oppo="abzan")  # 2 et 3 parties
    )
    matchups = compute_deck_stats(games, "terra", ["v1"]).matchups
    assert [m.oppo for m in matchups] == ["Ragavan", "Kess", "abzan", "Atraxa"]
    ragavan, kess = matchups[0], matchups[1]
    assert (ragavan.otp, ragavan.otd) == (Winrate(5, 5), Winrate(5, 5))
    assert ragavan.record.bo3 == Winrate(0, 0)
    assert (kess.otp, kess.otd) == (None, None)
    assert kess.record == record(match("a", "WL") + match("b", "WLW"))
    assert kess.record.bo3 == Winrate(1, 2)


def test_egalite_de_parties_triee_par_nom():
    games = match("a", "WW", oppo="kess") + match("b", "WW", oppo="Atraxa")
    assert [m.oppo for m in compute_deck_stats(games, "terra", ["v1"]).matchups] == ["Atraxa", "kess"]


def test_matchups_tries_par_poids_du_meta():
    games = (
        match("a", "WWW", oppo="Kess") + match("b", "WW", oppo="Ragavan")
        + match("c", "L", oppo="Atraxa") + match("d", "WLW", oppo="Tymna")
    )
    weights = {"Ragavan": 20.0, "Atraxa": 12.5, "Absent": 30.0}
    matchups = compute_deck_stats(games, "terra", ["v1"], weights).matchups
    # méta d'abord (poids ↓), puis les oppos hors méta (parties ↓, puis nom)
    assert [(m.oppo, m.weight) for m in matchups] == [
        ("Ragavan", 20.0), ("Atraxa", 12.5), ("Kess", None), ("Tymna", None)
    ]


def test_self_play_sans_poids():
    games = match("a", "WW", oppo="terra@v1")
    stats = compute_deck_stats(games, "terra", ["v1"], {"terra@v1": 10.0})
    assert stats.self_play[0].weight is None
