from datetime import date
from pathlib import Path

from dcprepa.domain.stats import compute_deck_stats
from dcprepa.domain.synthese_report import render_synthese

TEMPLATE = Path(__file__).resolve().parents[3] / "data" / "templates" / "tournament" / "stats" / "synthese.md"
GENERATED = date(2026, 9, 24)


def game(match_id, resultat, *, deck, oppo, version="v1"):
    return {
        "date": "01/11/2026", "match_id": match_id, "game": "1", "source": "paper", "deck": deck,
        "version": version, "oppo": oppo, "position": "OTP", "resultat": resultat, "note/ressenti": "",
    }


def match(match_id, results, **fields):
    return [game(match_id, result, **fields) for result in results]


def sheet(name, statut, versions=("v1",)):
    return {"name": name, "commandant": "", "statut": statut, "versions": list(versions)}


def section(text, title):
    """Lignes d'une section « ## title », sans le titre ni les lignes vides."""
    block = text.split(f"## {title}\n", 1)[1].split("\n## ", 1)[0]
    return [line for line in block.splitlines() if line]


def render(games, sheets, metas=None, meta_dir=None):
    metas = metas or {}
    decks = {deck: (sh, compute_deck_stats(games, deck, sh["versions"], metas)) for deck, sh in sheets.items()}
    return render_synthese("RelicFest 2026", decks, metas, GENERATED, meta_dir)


def test_deck_vide_suit_le_modele():
    stats = compute_deck_stats([], "<deck>", [])
    text = render_synthese("<nom du tournoi>", {"<deck>": (sheet("", "envisage", []), stats)}, {}, GENERATED)
    expected = (
        TEMPLATE.read_text(encoding="utf-8")
        .replace("Généré le —", "Généré le 24/09/2026")
        .replace("| [<deck>](<deck>.md) | — |", "| [<deck>](<deck>.md) | envisage |")
    )
    assert text == expected


def test_en_tete_avec_meta():
    text = render([], {}, {"paper": {}, "general": {}}, "2026-09-24")
    assert text.startswith(
        "# Synthèse — RelicFest 2026\n\n"
        "> Généré le 24/09/2026 à partir de `games.csv`, `decks/` et `meta/2026-09-24/`. Ne pas modifier à la main.\n"
    )


def test_decks_tries_par_statut_puis_attendu():
    metas = {"paper": {"Kess": 40, "Ragavan": 30}, "general": {}}
    games = (
        match("a", "WL", deck="terra", oppo="Kess")          # attendu 50 %
        + match("b", "WW", deck="cloud", oppo="Kess")        # attendu 100 %
        + match("c", "WW", deck="aragorn", oppo="Ragavan")   # retenu
        + match("d", "WW", deck="winota", oppo="Kess")       # ecarte
    )
    sheets = {
        "winota": sheet("Winota", "ecarte"), "terra": sheet("Terra", "envisage", ["v1", "v2"]),
        "cloud": sheet("Cloud", "envisage"), "aragorn": sheet("Aragorn", "retenu"), "sans": sheet("", ""),
    }
    rows = section(render(games, sheets, metas, "2026-09-24"), "Decks")[3:]
    assert [row.split(" | ")[0] for row in rows] == [
        "| [Aragorn](aragorn.md)", "| [Cloud](cloud.md)", "| [Terra](terra.md)", "| [Winota](winota.md)", "| [sans](sans.md)",
    ]
    assert rows[2] == (
        "| [Terra](terra.md) | envisage | v2 | ⚠️ 50 % (1/2) | ⚠️ 0 % (0/1) | 50 % (40 % du méta) | 0 % (40 % du méta) |"
    )
    assert rows[4] == "| [sans](sans.md) | — | v1 | — | — | — | — |"


def test_meta_union_et_decks_actifs_seulement():
    metas = {"paper": {"Kess": 12.5, "Ragavan": 20}, "general": {"Ragavan": 18, "Tymna": 9, "Atraxa": 11}}
    games = match("a", "WLW", deck="terra", oppo="Ragavan") + match("b", "W", deck="winota", oppo="Kess")
    sheets = {"terra": sheet("Terra", "retenu"), "winota": sheet("Winota", "ecarte")}
    rows = section(render(games, sheets, metas, "2026-09-24"), "Méta")[1:]
    assert rows == [
        "| Oppo | Poids papier | Poids général | Terra |",
        "|---|---|---|---|",
        "| Ragavan | 20 % | 18 % | ⚠️ 66.7 % (2/3) |",
        "| Kess | 12.5 % | — | — |",
        "| Atraxa | — | 11 % | — |",
        "| Tymna | — | 9 % | — |",
    ]


def test_matchups_non_testes():
    metas = {"paper": {"Kess": 40, "Ragavan": 30}, "general": {}}
    games = match("a", "WL", deck="terra", oppo="Kess") + [
        game(f"r{number}", "W", deck="terra", oppo="Ragavan") for number in range(30)
    ]
    sheets = {"terra": sheet("Terra", "retenu"), "winota": sheet("Winota", "ecarte")}
    rows = section(render(games, sheets, metas, "2026-09-24"), "Matchups non testés")[4:]
    assert rows == ["| Terra | Kess | 1 | 40 % | 1 | 2 |"]
