from datetime import date
from pathlib import Path

import pytest

from dcprepa.domain.report import MATCHUPS_SORT_META, MATCHUPS_SORT_NO_META, _gap, render_deck_report
from dcprepa.domain.stats import compute_deck_stats

TEMPLATE = Path(__file__).resolve().parents[3] / "data" / "templates" / "tournament" / "stats" / "_modele-deck.md"
GENERATED = date(2026, 9, 24)


def game(match_id, resultat, *, version="v1", oppo="Ragavan", source="paper", position="OTP"):
    return {
        "date": "01/11/2026", "match_id": match_id, "partie": "1", "source": source, "deck": "terra",
        "version": version, "oppo": oppo, "position": position, "resultat": resultat, "note/ressenti": "",
    }


def match(match_id, results, **fields):
    return [game(match_id, r, position=("OTP", "OTD")[n % 2], **fields) for n, r in enumerate(results)]


@pytest.fixture
def sheet():
    return {"name": "Terra Midrange", "commandant": "Terra, Magical Adept", "statut": "envisage", "versions": ["v1", "v2"]}


def section(text, title):
    """Lignes d'une section « ## title », sans le titre ni les lignes vides."""
    block = text.split(f"## {title}\n", 1)[1].split("\n## ", 1)[0]
    return [line for line in block.splitlines() if line]


def test_deck_vide_suit_le_modele():
    sheet = {"name": "", "commandant": "", "statut": "", "versions": []}
    stats = compute_deck_stats([], "<deck>", [])
    expected = (
        TEMPLATE.read_text(encoding="utf-8")
        .replace("# <nom du deck>", "# <deck>")
        .replace("Généré le —", "Généré le 24/09/2026")
        .replace("Triés par poids dans le méta", MATCHUPS_SORT_NO_META)
    )
    assert render_deck_report("<deck>", sheet, stats, GENERATED) == expected


def test_en_tete(sheet):
    text = render_deck_report("terra", sheet, compute_deck_stats([], "terra", sheet["versions"]), GENERATED)
    assert text.startswith(
        "# Terra Midrange\n\n"
        "> Généré le 24/09/2026 à partir de `games.csv`, `decks/terra.yaml` et `meta/—.csv`. Ne pas modifier à la main.\n"
        "> Conventions : voir `README.md`.\n\n"
        "- **Commandant :** Terra, Magical Adept\n"
        "- **Statut :** envisage\n"
        "- **Dernière version :** v2\n"
    )
    assert text.endswith(" |\n")


def test_nom_absent_remplace_par_le_fichier(sheet):
    sheet["name"] = ""
    text = render_deck_report("terra", sheet, compute_deck_stats([], "terra", []), GENERATED)
    assert text.startswith("# terra\n")


def test_sections_remplies(sheet):
    games = (
        match("a", "WLW", version="v1") + match("b", "WW", version="v1", source="mtgo")
        + match("c", "L", version="v2", oppo="Kess")
        + match("d", "WW", version="v2", oppo="terra@v1", source="cockatrice")
    )
    text = render_deck_report("terra", sheet, compute_deck_stats(games, "terra", sheet["versions"]), GENERATED)

    assert section(text, "Général")[2:] == [
        "| Par partie | ⚠️ 66.7 % (4/6) |",
        "| Par match (BO3) | ⚠️ 100 % (2/2) |",
        "| Winrate attendu au tournoi | — |",
    ]
    assert section(text, "Versions")[3:] == [
        "| v1 | 5 | +80 | 2 | — |",
        "| v2 | 1 | -80 | — | — |",
    ]
    assert section(text, "Position")[3:] == ["| ⚠️ 75 % (3/4) | ⚠️ 50 % (1/2) |"]
    assert section(text, "Source")[2:] == [
        "| Paper | ⚠️ 50 % (2/4) | ⚠️ 100 % (1/1) |",
        "| Cockatrice | — | — |",
        "| MTGO | ⚠️ 100 % (2/2) | ⚠️ 100 % (1/1) |",
    ]
    assert section(text, "Matchups")[3:] == [
        "| Ragavan | — | ⚠️ 80 % (4/5) | ⚠️ 100 % (2/2) | — | — |",
        "| Kess | — | ⚠️ 0 % (0/1) | — | — | — |",
    ]
    assert section(text, "Self-play")[3:] == ["| terra@v1 | ⚠️ 100 % (2/2) | ⚠️ 100 % (1/1) | — | — |"]


def test_otp_otd_du_matchup_des_10_parties(sheet):
    games = [game(f"m{n}", "W", position=("OTP", "OTD")[n % 2]) for n in range(10)]
    text = render_deck_report("terra", sheet, compute_deck_stats(games, "terra", sheet["versions"]), GENERATED)
    assert section(text, "Matchups")[3:] == ["| Ragavan | — | 100 % (10/10) | — | ⚠️ 100 % (5/5) | ⚠️ 100 % (5/5) |"]


def test_avec_meta(sheet):
    games = match("a", "WW") + match("b", "L", oppo="Kess")
    stats = compute_deck_stats(games, "terra", sheet["versions"], {"Ragavan": 12.5, "Atraxa": 30.0})
    text = render_deck_report("terra", sheet, stats, GENERATED, "2026-10-01.csv")
    assert "`decks/terra.yaml` et `meta/2026-10-01.csv`." in text
    matchups = section(text, "Matchups")
    assert matchups[0].startswith(f"{MATCHUPS_SORT_META}, self-play exclu.")
    assert matchups[3:] == [
        "| Ragavan | 12.5 % | ⚠️ 100 % (2/2) | ⚠️ 100 % (1/1) | — | — |",
        "| Kess | — | ⚠️ 0 % (0/1) | — | — | — |",
    ]


def test_sans_meta(sheet):
    text = render_deck_report("terra", sheet, compute_deck_stats(match("a", "WW"), "terra", ["v1"]), GENERATED)
    assert "`meta/—.csv`" in text
    assert section(text, "Matchups")[0].startswith(f"{MATCHUPS_SORT_NO_META}, self-play exclu.")
    assert section(text, "Matchups")[3:] == ["| Ragavan | — | ⚠️ 100 % (2/2) | ⚠️ 100 % (1/1) | — | — |"]


@pytest.mark.parametrize(
    "gap, expected",
    [(None, "—"), (3.24, "+3.2"), (-30.0, "-30"), (0.0, "0"), (0.04, "0"), (-0.04, "0")],
)
def test_format_ecart(gap, expected):
    assert _gap(gap) == expected
