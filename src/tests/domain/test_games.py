import pytest

from dcprepa.domain.games import _parse_games, parse_bos


def test_bo1_valide():
    assert _parse_games("OTP W") == ([["OTP", "W"]], [])


@pytest.mark.parametrize(
    "text, expected",
    [
        ("OTP W", [["OTP", "W"]]),
        ("OTD L", [["OTD", "L"]]),
        ("  otp w ,otd l ", [["OTP", "W"], ["OTD", "L"]]),
        ("OTP\tW", [["OTP", "W"]]),
        ("OTP W, OTD L", [["OTP", "W"], ["OTD", "L"]]),
        ("OTP W, OTD W", [["OTP", "W"], ["OTD", "W"]]),
        ("OTP W, OTD L, OTP W", [["OTP", "W"], ["OTD", "L"], ["OTP", "W"]]),
        ("OTP W, OTD L, OTP L", [["OTP", "W"], ["OTD", "L"], ["OTP", "L"]]),
    ],
)
def test_bo_valide(text, expected):
    assert _parse_games(text) == (expected, [])


@pytest.mark.parametrize(
    "text, expected",
    [
        ("", ["BO vide"]),
        ("   ", ["BO vide"]),
        ("OTP W, OTD W, OTP L, OTD W", ["4 games dans un BO (3 maximum)"]),
        ("OTP W,", ["game 2 : vide (virgule en trop ?)"]),
        (", OTP W", ["game 1 : vide (virgule en trop ?)"]),
        ("OTP W,, OTD L", ["game 2 : vide (virgule en trop ?)"]),
        ("OTP", ["game 1 : mal formée (attendu : OTP W) : OTP"]),
        ("OTP W X", ["game 1 : mal formée (attendu : OTP W) : OTP W X"]),
        ("MID W", ["game 1 : position inconnue (OTP ou OTD) : MID"]),
        ("OTP X", ["game 1 : résultat inconnu (W ou L) : X"]),
        (
            "OPP U",
            [
                "game 1 : position inconnue (OTP ou OTD) : OPP",
                "game 1 : résultat inconnu (W ou L) : U",
            ],
        ),
        ("OTP W, OTD W, OTP L", ["game 3 : en trop, BO déjà terminé (2-0)"]),
        ("OTP L, OTD L, OTP W", ["game 3 : en trop, BO déjà terminé (0-2)"]),
    ],
)
def test_bo_invalide(text, expected):
    assert _parse_games(text) == ([], expected)


@pytest.mark.parametrize(
    "text, expected",
    [
        ("OTP W", [[["OTP", "W"]]]),
        (
            "OTP W, OTD W / OTD L",
            [[["OTP", "W"], ["OTD", "W"]], [["OTD", "L"]]],
        ),
        (
            "otp w,otd l/ otp l ",
            [[["OTP", "W"], ["OTD", "L"]], [["OTP", "L"]]],
        ),
    ],
)
def test_parse_bos_valide(text, expected):
    assert parse_bos(text) == (expected, [])


@pytest.mark.parametrize(
    "text, expected",
    [
        ("", ["BO 1 : BO vide"]),
        ("OTP W / ", ["BO 2 : BO vide"]),
        ("OTP W / OPP L", ["BO 2 : game 1 : position inconnue (OTP ou OTD) : OPP"]),
        (
            "OTP X / OTD Y",
            [
                "BO 1 : game 1 : résultat inconnu (W ou L) : X",
                "BO 2 : game 1 : résultat inconnu (W ou L) : Y",
            ],
        ),
        (
            "OTP W, OTD W, OTP L / OTD L",
            ["BO 1 : game 3 : en trop, BO déjà terminé (2-0)"],
        ),
    ],
)
def test_parse_bos_invalide(text, expected):
    assert parse_bos(text) == ([], expected)
