from dataclasses import dataclass, field
from pathlib import Path

from dcprepa.domain.games import parse_bos
from dcprepa.domain.oppos import build_oppo_index, normalize_oppo
from dcprepa.domain.rows import build_rows
from dcprepa.domain.validation import validate_block
from dcprepa.storage.decks import load_decks
from dcprepa.storage.games import append_rows, read_match_ids
from dcprepa.storage.inbox import clear_inbox, read_inbox
from dcprepa.storage.oppos import load_oppos


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

    Un oppo inconnu est un avertissement, pas une erreur. Une inbox sans bloc ne modifie rien.
    """
    report = ImportReport()
    inbox_path = tournament_dir / "inbox.yaml"
    games_path = tournament_dir / "games.csv"

    blocks, errors = read_inbox(inbox_path)
    report.errors += errors
    decks, errors = load_decks(tournament_dir)
    report.errors += errors
    oppos, errors = load_oppos(oppos_path)
    report.errors += errors
    index, errors = build_oppo_index(oppos)
    report.errors += errors
    used_ids, errors = read_match_ids(games_path)
    report.errors += errors
    if report.errors or not blocks:
        return report

    rows = []
    for number, block in enumerate(blocks, start=1):
        block_errors = validate_block(block, decks)
        if block_errors:
            report.errors += [f"bloc {number} : {message}" for message in block_errors]
            continue
        oppo, warning = normalize_oppo(block["oppo"], index)
        if warning:
            report.warnings.append(f"bloc {number} : {warning}")
        bos, _ = parse_bos(str(block["parties"]))
        rows += build_rows(block, bos, oppo, used_ids)
        report.blocks += 1
        report.matches += len(bos)

    if report.errors:
        report.blocks = report.matches = 0
        return report

    append_rows(games_path, rows)
    clear_inbox(inbox_path)
    report.games = len(rows)
    return report
