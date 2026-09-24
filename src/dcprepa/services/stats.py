from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from dcprepa.domain.report import render_deck_report
from dcprepa.domain.stats import compute_deck_stats
from dcprepa.storage.decks import load_deck_sheets
from dcprepa.storage.games import read_games
from dcprepa.storage.meta import load_latest_meta
from dcprepa.storage.stats import write_report


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
    """Génère stats/<deck>.md pour chaque fiche deck du tournoi, en tout ou rien.

    1. lit games.csv, les fiches deck et le méta le plus récent (s'il y en a un) ;
    2. à la moindre erreur : rien n'est écrit, le bilan liste les erreurs ;
    3. sinon : calcule et rend tous les rapports, PUIS les écrit (un par fiche, même sans partie).

    Avertissements : deck de games.csv sans fiche (pas de rapport), version jouée absente de la fiche.
    generated : date affichée dans les rapports (aujourd'hui par défaut).
    """
    report = StatsReport()
    generated = generated or date.today()

    games, errors = read_games(tournament_dir / "games.csv")
    report.errors += errors
    sheets, errors = load_deck_sheets(tournament_dir)
    report.errors += errors
    meta_file, weights, errors = load_latest_meta(tournament_dir)
    report.errors += errors
    if report.errors:
        return report

    for deck in sorted({game["deck"] for game in games} - set(sheets)):
        count = sum(game["deck"] == deck for game in games)
        report.warnings.append(f"games.csv : deck sans fiche : {deck} ({count} game(s)) → pas de rapport")

    texts = {}
    for deck, sheet in sheets.items():
        played = dict.fromkeys(game["version"] for game in games if game["deck"] == deck)
        for version in played:
            if version not in sheet["versions"]:
                report.warnings.append(f"{deck} : version jouée absente de la fiche : {version}")
        stats = compute_deck_stats(games, deck, sheet["versions"], weights)
        texts[deck] = render_deck_report(deck, sheet, stats, generated, meta_file)

    for deck, text in texts.items():
        write_report(tournament_dir / "stats" / f"{deck}.md", text)
    report.decks = list(texts)
    report.games = len(games)
    report.meta = meta_file
    return report
