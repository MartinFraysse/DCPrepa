from datetime import date

from dcprepa.domain.stats import BestVersion, DeckStats, MatchupStats
from dcprepa.domain.validation import DATE_FORMAT
from dcprepa.domain.winrate import NO_DATA, WARNING, Winrate, format_percent

SOURCE_LABELS = {"paper": "Paper", "cockatrice": "Cockatrice", "mtgo": "MTGO"}
MATCHUPS_SORT_META = "Triés par poids dans le méta papier"
MATCHUPS_SORT_NO_META = "Triés par nombre de games (pas encore de méta)"


def render_deck_report(deck: str, sheet: dict, stats: DeckStats, generated: date, meta_dir: str | None = None) -> str:
    """Texte Markdown de stats/<deck>.md, dans la structure de data/templates/tournament/stats/_modele-deck.md.

    deck : nom du fichier de la fiche ; sheet : fiche de load_deck_sheets (name, commandant, statut, versions) ;
    meta_dir : dossier méta utilisé par compute_deck_stats (ex. « 2026-09-24 »), None sans méta.
    Avec méta : l'en-tête le cite, matchups triés par poids papier, colonnes « Poids papier » et « Poids général » remplies.
    Sans méta : « meta/— », matchups triés par games. « Winrate attendu au tournoi » reste à « — ».
    """
    versions = sheet.get("versions") or []
    meta_path = f"meta/{meta_dir}/" if meta_dir else f"meta/{NO_DATA}"
    lines = [
        f"# {sheet.get('name') or deck}",
        "",
        f"> Généré le {generated.strftime(DATE_FORMAT)} à partir de `games.csv`, `decks/{deck}.yaml` et `{meta_path}`."
        " Ne pas modifier à la main.",
        "> Conventions : voir `README.md`.",
        "",
        f"- **Commandant :** {sheet.get('commandant') or NO_DATA}",
        f"- **Statut :** {sheet.get('statut') or NO_DATA}",
        f"- **Dernière version :** {versions[-1] if versions else NO_DATA}",
        "",
        "## Général",
        "",
        *_table(
            ["", "Winrate"],
            [
                ["Par game", stats.overall.games],
                ["Par BO3", stats.overall.bo3],
                ["Winrate attendu au tournoi", NO_DATA],
            ],
        ),
        "",
        "## Versions",
        "",
        "Écart : winrate de la version − moyenne simple des winrates des autres versions, en points.",
        "",
        *_table(
            ["Version", "Games", "Winrate (games)", "Écart (games)", "BO3", "Winrate BO3", "Écart BO3"],
            [
                [
                    v.version,
                    _count(v.record.games), v.record.games, _gap(v.gap_games),
                    _count(v.record.bo3), v.record.bo3, _gap(v.gap_bo3),
                ]
                for v in stats.versions
            ],
        ),
        "",
        "## Position",
        "",
        "Par game seulement : la position change d'une game à l'autre dans un BO3.",
        "",
        *_table(["OTP", "OTD"], [[stats.positions["OTP"], stats.positions["OTD"]]]),
        "",
        "## Source",
        "",
        *_table(
            ["Source", "Winrate (games)", "Winrate BO3"],
            [[SOURCE_LABELS.get(source, source), rec.games, rec.bo3] for source, rec in stats.sources.items()],
        ),
        "",
        "## Matchups",
        "",
        f"{MATCHUPS_SORT_META if meta_dir else MATCHUPS_SORT_NO_META}, self-play exclu. OTP / OTD affichés seulement à partir de 10 games contre l'oppo.",
        "",
        "Meilleure version : la version au meilleur winrate contre l'oppo et son écart au winrate du matchup, en points"
        " (« — » si une seule version l'a joué).",
        "",
        *_table(
            ["Oppo", "Poids papier", "Poids général", "Winrate (games)", "Meilleure version (games)", "Winrate BO3", "Meilleure version BO3", "OTP", "OTD"],
            [
                [
                    m.oppo, _weight(m.weight_paper), _weight(m.weight_general),
                    m.record.games, _best(m.best_games), m.record.bo3, _best(m.best_bo3),
                    m.otp or NO_DATA, m.otd or NO_DATA,
                ]
                for m in stats.matchups
            ],
        ),
        "",
        "## Self-play",
        "",
        "Games contre ses propres decks (oppo = `deck@version`), hors winrate général.",
        "",
        *_table(
            ["Oppo", "Winrate (games)", "Winrate BO3", "OTP", "OTD"],
            [[m.oppo, *_matchup_cells(m)] for m in stats.self_play],
        ),
    ]
    return "\n".join(lines) + "\n"


def _table(header: list[str], rows: list[list]) -> list[str]:
    """Tableau Markdown ; sans ligne de données, une ligne de « — »."""
    rows = rows or [[NO_DATA] * len(header)]
    return [
        _row(header),
        "|" + "---|" * len(header),
        *(_row(row) for row in rows),
    ]


def _row(cells: list) -> str:
    """Ligne de tableau ; une cellule vide donne « | | » comme dans le modèle."""
    return "|" + "".join(f" {cell} |" if str(cell) else " |" for cell in cells)


def _matchup_cells(matchup: MatchupStats) -> list:
    return [matchup.record.games, matchup.record.bo3, matchup.otp or NO_DATA, matchup.otd or NO_DATA]


def _best(best: BestVersion | None) -> str:
    """Meilleure version : « v2 (+12) », « ⚠️ v2 (+12) » si elle a moins de 10 games (ou BO3) contre l'oppo, « — » sinon."""
    if best is None:
        return NO_DATA
    text = f"{best.version} ({_gap(best.gap)})"
    return text if best.winrate.reliable else f"{WARNING} {text}"


def _count(winrate: Winrate) -> str:
    return str(winrate.total) if winrate.total else NO_DATA


def _weight(weight: float | None) -> str:
    """Poids dans le méta : « 12.5 % » ; « — » sans méta ou oppo absent du méta."""
    return NO_DATA if weight is None else f"{format_percent(weight)} %"


def _gap(gap: float | None) -> str:
    """Écart en points : « +3.2 », « -30 », « 0 » ; « — » si incalculable."""
    if gap is None:
        return NO_DATA
    text = format_percent(gap)
    return f"+{text}" if gap > 0 and text != "0" else text
