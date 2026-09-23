import pytest

from dcprepa.domain.rows import build_rows, next_match_id

BLOCK = {
    "date": "02/10/2026",
    "source": " Paper ",
    "deck": "terra-midrange",
    "version": "v1",
    "oppo": "raga",
    "parties": "OTP W, OTD W / OTD L",
    "note/ressenti": "Matchup  jouable",
}
BOS = [[["OTP", "W"], ["OTD", "W"]], [["OTD", "L"]]]


@pytest.mark.parametrize(
    "used_ids, expected",
    [
        (set(), "2026-10-02-01"),
        ({"2026-10-02-01"}, "2026-10-02-02"),
        ({"2026-10-02-01", "2026-10-02-03"}, "2026-10-02-04"),
        ({"2026-10-01-05", "2026-10-03-07"}, "2026-10-02-01"),
        ({"2026-10-02-09"}, "2026-10-02-10"),
        ({"2026-10-02-99"}, "2026-10-02-100"),
        ({"2026-10-02-xx", "autre"}, "2026-10-02-01"),
    ],
)
def test_next_match_id(used_ids, expected):
    assert next_match_id("02/10/2026", used_ids) == expected


def test_next_match_id_ne_modifie_pas_used_ids():
    used_ids = {"2026-10-02-01"}
    next_match_id("02/10/2026", used_ids)
    assert used_ids == {"2026-10-02-01"}


def test_build_rows():
    used_ids = {"2026-10-02-01"}
    rows = build_rows(BLOCK, BOS, "Ragavan", used_ids)
    common = {
        "date": "02/10/2026",
        "source": "paper",
        "deck": "terra-midrange",
        "version": "v1",
        "oppo": "Ragavan",
        "note/ressenti": "Matchup jouable",
    }
    assert rows == [
        {**common, "match_id": "2026-10-02-02", "partie": "1", "position": "OTP", "resultat": "W"},
        {**common, "match_id": "2026-10-02-02", "partie": "2", "position": "OTD", "resultat": "W"},
        {**common, "match_id": "2026-10-02-03", "partie": "1", "position": "OTD", "resultat": "L"},
    ]
    assert used_ids == {"2026-10-02-01", "2026-10-02-02", "2026-10-02-03"}


def test_deux_blocs_du_meme_jour_se_suivent():
    used_ids = set()
    first = build_rows(BLOCK, BOS, "Ragavan", used_ids)
    second = build_rows(BLOCK, [[["OTP", "L"]]], "Kess", used_ids)
    assert [row["match_id"] for row in first] == ["2026-10-02-01", "2026-10-02-01", "2026-10-02-02"]
    assert [row["match_id"] for row in second] == ["2026-10-02-03"]


def test_note_absente_ou_vide():
    block = {key: value for key, value in BLOCK.items() if key != "note/ressenti"}
    rows = build_rows(block, [[["OTP", "W"]]], "Ragavan", set())
    assert rows[0]["note/ressenti"] == ""
    rows = build_rows({**BLOCK, "note/ressenti": None}, [[["OTP", "W"]]], "Ragavan", set())
    assert rows[0]["note/ressenti"] == ""


def test_version_numerique_en_texte():
    rows = build_rows({**BLOCK, "version": 3}, [[["OTP", "W"]]], "Ragavan", set())
    assert rows[0]["version"] == "3"


def test_toutes_les_colonnes_presentes():
    from dcprepa.storage.games import COLUMNS

    rows = build_rows(BLOCK, BOS, "Ragavan", set())
    assert all(sorted(row) == sorted(COLUMNS) for row in rows)
