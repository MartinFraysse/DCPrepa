from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from dcprepa.domain.report import render_deck_report
from dcprepa.domain.stats import compute_deck_stats
from dcprepa.domain.synthese_report import STATUS_ORDER, render_synthese
from dcprepa.storage.decks import load_deck_sheets
from dcprepa.storage.games import read_games
from dcprepa.storage.meta import load_latest_meta
from dcprepa.storage.stats import write_report
from dcprepa.storage.tournament import load_tournament_name

SYNTHESE_FILE = "synthese.md"


@dataclass
class StatsReport:
    """Bilan d'une génération : rapports écrits, games lues, méta utilisé, erreurs (bloquantes) et avertissements."""

    decks: list[str] = field(default_factory=list)
    games: int = 0
    meta: str | None = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def generate_stats(tournament_dir: Path, generated: date | None = None) -> StatsReport:
    """Génère stats/<deck>.md pour chaque fiche deck du tournoi et stats/synthese.md, en tout ou rien.

    1. lit games.csv, les fiches deck, le méta le plus récent (s'il y en a un) et le nom du tournoi (tournament.yaml) ;
    2. à la moindre erreur : rien n'est écrit, le bilan liste les erreurs ;
    3. sinon : calcule et rend tous les rapports et la synthèse, PUIS les écrit (un rapport par fiche, même sans game).

    Avertissements : deck de games.csv sans fiche (pas de rapport), version jouée absente de la fiche,
    statut vide ou inconnu (deck absent du tableau Méta et des matchups non testés), tournament.yaml illisible.
    generated : date affichée dans les rapports (aujourd'hui par défaut).
    """
    report = StatsReport()
    generated = generated or date.today()

    games, errors = read_games(tournament_dir / "games.csv")
    report.errors += errors
    sheets, errors = load_deck_sheets(tournament_dir)
    report.errors += errors
    meta_dir, metas, errors = load_latest_meta(tournament_dir)
    report.errors += errors
    if report.errors:
        return report

    for deck in sorted({game["deck"] for game in games} - set(sheets)):
        count = sum(game["deck"] == deck for game in games)
        report.warnings.append(f"games.csv : deck sans fiche : {deck} ({count} game(s)) → pas de rapport")

    tournament, warnings = load_tournament_name(tournament_dir)
    report.warnings += warnings

    texts = {}
    all_stats = {}
    for deck, sheet in sheets.items():
        if sheet["statut"] not in STATUS_ORDER:
            status = f"inconnu « {sheet['statut']} »" if sheet["statut"] else "vide"
            report.warnings.append(
                f"{deck} : statut {status} (retenu, envisage ou ecarte) → absent du tableau Méta et des matchups non testés"
            )
        played = dict.fromkeys(game["version"] for game in games if game["deck"] == deck)
        for version in played:
            if version not in sheet["versions"]:
                report.warnings.append(f"{deck} : version jouée absente de la fiche : {version}")
        stats = compute_deck_stats(games, deck, sheet["versions"], metas)
        texts[deck] = render_deck_report(deck, sheet, stats, generated, meta_dir)
        all_stats[deck] = (sheet, stats)
    synthese = render_synthese(tournament, all_stats, metas, generated, meta_dir)

    for deck, text in texts.items():
        write_report(tournament_dir / "stats" / f"{deck}.md", text)
    write_report(tournament_dir / "stats" / SYNTHESE_FILE, synthese)
    report.decks = list(texts)
    report.games = len(games)
    report.meta = meta_dir
    return report
