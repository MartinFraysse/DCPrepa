from datetime import date

from dcprepa.domain.report import _table, _weight
from dcprepa.domain.stats import DeckStats
from dcprepa.domain.synthese import ACTIVE_STATUSES, expected_winrate, untested_matchups
from dcprepa.domain.validation import DATE_FORMAT
from dcprepa.domain.winrate import NO_DATA

STATUS_ORDER = ("retenu", "envisage", "ecarte")


def render_synthese(
    tournament: str,
    decks: dict[str, tuple[dict, DeckStats]],
    metas: dict[str, dict[str, float]],
    generated: date,
    meta_dir: str | None = None,
) -> str:
    """Texte Markdown de stats/synthese.md, dans la structure de data/templates/tournament/stats/synthese.md.

    tournament : nom affiché du tournoi ; decks : {deck: (fiche de load_deck_sheets, stats de compute_deck_stats)} ;
    metas : poids par oppo, {"paper": {…}, "general": {…}} (load_latest_meta), vide sans méta ;
    meta_dir : dossier méta utilisé (ex. « 2026-09-24 »), None sans méta.
    Decks : triés par statut (retenu, envisage, ecarte, puis inconnu), puis winrate attendu papier par game (décroissant), puis nom.
    Méta et Matchups non testés : decks retenus ou envisagés seulement, dans l'ordre du tableau Decks.
    """
    ordered = sorted(decks.items(), key=lambda item: _deck_order(item[0], *item[1]))
    active = [(deck, sheet, stats) for deck, (sheet, stats) in ordered if sheet.get("statut") in ACTIVE_STATUSES]
    names = {deck: _name(deck, sheet) for deck, (sheet, _) in decks.items()}
    paper, general = metas.get("paper", {}), metas.get("general", {})
    meta_path = f"meta/{meta_dir}/" if meta_dir else f"meta/{NO_DATA}"

    lines = [
        f"# Synthèse — {tournament}",
        "",
        f"> Généré le {generated.strftime(DATE_FORMAT)} à partir de `games.csv`, `decks/` et `{meta_path}`."
        " Ne pas modifier à la main.",
        "> Conventions : voir `README.md`.",
        "",
        "## Decks",
        "",
        "Triés par statut (retenu, envisage, ecarte), puis par winrate attendu papier par game.",
        "",
        *_table(
            ["Deck", "Statut", "Dernière version", "Winrate (games)", "Winrate BO3", "Attendu papier (games)", "Attendu papier (BO3)"],
            [
                [
                    f"[{names[deck]}]({deck}.md)", sheet.get("statut") or NO_DATA,
                    sheet["versions"][-1] if sheet.get("versions") else NO_DATA,
                    stats.overall.games, stats.overall.bo3,
                    expected_winrate(stats.matchups, "paper", "games"), expected_winrate(stats.matchups, "paper", "bo3"),
                ]
                for deck, (sheet, stats) in ordered
            ],
        ),
        "",
        "## Méta",
        "",
        "Oppos du top 20 papier et général, triés par poids papier, et winrate par game de chaque deck retenu ou envisagé contre eux.",
        "",
        *_table(
            ["Oppo", "Poids papier", "Poids général", *(names[deck] for deck, _, _ in active)],
            [
                [
                    oppo, _weight(paper.get(oppo)), _weight(general.get(oppo)),
                    *(_winrate_against(stats, oppo) for _, _, stats in active),
                ]
                for oppo in _meta_oppos(paper, general)
            ],
        ),
        "",
        "## Matchups non testés",
        "",
        "Oppos du top 10 du méta papier pas encore assez testés par les decks retenus ou envisagés :"
        " moins de 10 BO3 **et** moins de 30 games",
        "(un seul des deux seuils atteint suffit pour considérer le matchup testé).",
        "",
        *_table(
            ["Deck", "Oppo", "Rang papier", "Poids papier", "BO3 joués", "Games jouées"],
            [
                [names[row.deck], row.oppo, row.rank, _weight(row.weight), row.bo3, row.games]
                for row in untested_matchups(
                    {deck: (sheet["statut"], stats.matchups) for deck, sheet, stats in active}, paper
                )
            ],
        ),
    ]
    return "\n".join(lines) + "\n"


def _name(deck: str, sheet: dict) -> str:
    return sheet.get("name") or deck


def _deck_order(deck: str, sheet: dict, stats: DeckStats) -> tuple:
    status = sheet.get("statut")
    rank = STATUS_ORDER.index(status) if status in STATUS_ORDER else len(STATUS_ORDER)
    expected = expected_winrate(stats.matchups, "paper", "games")
    return rank, expected.rate is None, -(expected.rate or 0), _name(deck, sheet).lower()


def _meta_oppos(paper: dict[str, float], general: dict[str, float]) -> list[str]:
    """Union des deux métas : par poids papier ↓, puis les absents du papier par poids général ↓, puis par nom."""
    return sorted(
        set(paper) | set(general),
        key=lambda oppo: (oppo not in paper, -paper.get(oppo, 0), -general.get(oppo, 0), oppo.lower()),
    )


def _winrate_against(stats: DeckStats, oppo: str):
    """Winrate par game du deck contre l'oppo, « — » s'il ne l'a jamais joué."""
    return next((matchup.record.games for matchup in stats.matchups if matchup.oppo == oppo), NO_DATA)
