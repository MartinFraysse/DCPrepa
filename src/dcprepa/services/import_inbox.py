from dataclasses import dataclass, field
from pathlib import Path

from dcprepa.domain.blocks import prepare_block
from dcprepa.services.games import load_game_references
from dcprepa.storage.games import append_rows
from dcprepa.storage.inbox import clear_inbox, read_inbox


@dataclass
class ImportReport:
    """Bilan d'un import : ce qui a été importé, les erreurs (bloquantes) et les avertissements."""

    blocks: int = 0
    matches: int = 0
    games: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def import_inbox(tournament_dir: Path, oppos_path: Path) -> ImportReport:
    """Importe inbox.yaml dans games.csv pour un tournoi, en tout ou rien.

    1. lit l'inbox, les fiches deck, oppos.yaml et les match_id de games.csv ;
    2. valide TOUS les blocs et rassemble TOUTES les erreurs ;
    3. à la moindre erreur : rien n'est écrit, le bilan liste les erreurs ;
    4. sinon : ajoute les lignes à games.csv, PUIS vide l'inbox (en-tête gardé).

    Le deck saisi est ramené au nom de son fichier (nom du fichier, name: ou variante de decks/_alias.yaml),
    y compris le deck d'un oppo self-play « deck@version ».
    Un oppo inconnu est un avertissement, pas une erreur. Une inbox sans bloc ne modifie rien.
    """
    report = ImportReport()
    inbox_path = tournament_dir / "inbox.yaml"
    games_path = tournament_dir / "games.csv"

    blocks, errors = read_inbox(inbox_path)
    report.errors += errors
    references, errors = load_game_references(tournament_dir, oppos_path)
    report.errors += errors
    if report.errors or not blocks:
        return report

    rows = []
    for number, block in enumerate(blocks, start=1):
        prepared = prepare_block(block, references.decks, references.deck_index, references.oppo_index, references.used_ids)
        report.errors += [f"bloc {number} : {message}" for message in prepared.errors]
        report.warnings += [f"bloc {number} : {message}" for message in prepared.warnings]
        if prepared.errors:
            continue
        rows += prepared.rows
        report.blocks += 1
        report.matches += prepared.matches

    if report.errors:
        report.blocks = report.matches = 0
        return report

    append_rows(games_path, rows)
    clear_inbox(inbox_path)
    report.games = len(rows)
    return report
