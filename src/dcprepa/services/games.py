from dataclasses import dataclass, field
from pathlib import Path

from dcprepa.domain.blocks import prepare_block
from dcprepa.domain.names import build_name_index
from dcprepa.domain.oppos import build_oppo_index
from dcprepa.storage.decks import load_deck_aliases, load_decks
from dcprepa.storage.games import append_rows, read_match_ids
from dcprepa.storage.oppos import load_oppos


@dataclass(frozen=True)
class GameReferences:
    """Ce qu'il faut pour vérifier un bloc de games : decks et versions, appellations des decks et des oppos, match_id pris."""

    decks: dict[str, list[str]]
    deck_index: dict[str, str]
    oppo_index: dict[str, str]
    used_ids: set[str]


@dataclass
class GamesReport:
    """Bilan d'une saisie de games : BO et games écrits, leurs match_id, erreurs (bloquantes) et avertissements."""

    matches: int = 0
    games: int = 0
    match_ids: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def load_game_references(tournament_dir: Path, oppos_path: Path) -> tuple[GameReferences, list[str]]:
    """Lit les fiches deck, decks/_alias.yaml, data/oppos.yaml et les match_id de games.csv.

    Toutes les erreurs sont rassemblées (lecture et appellations ambiguës) ; avec une erreur, les références ne sont pas fiables.
    """
    errors = []
    decks, found = load_decks(tournament_dir)
    errors += found
    aliases, found = load_deck_aliases(tournament_dir, decks)
    errors += found
    deck_index, found = build_name_index(aliases, "decks")
    errors += found
    oppos, found = load_oppos(oppos_path)
    errors += found
    oppo_index, found = build_oppo_index(oppos)
    errors += found
    used_ids, found = read_match_ids(tournament_dir / "games.csv")
    errors += found
    return GameReferences(decks, deck_index, oppo_index, used_ids), errors


def add_games(tournament_dir: Path, block: dict, oppos_path: Path) -> GamesReport:
    """Ajoute à games.csv les games d'une session saisie, en tout ou rien.

    block : mêmes champs qu'un bloc de l'inbox (date, source, deck, version, oppo, games, note/ressenti facultative),
    ex. {"date": "02/10/2026", "source": "paper", "deck": "terra", "version": "v2", "oppo": "Ragavan",
    "games": "OTP W, OTD L, OTP W / OTP W"}. Mêmes contrôles que l'import (prepare_block).
    À la moindre erreur : rien n'est écrit. Un oppo inconnu est un avertissement.
    """
    report = GamesReport()
    references, errors = load_game_references(tournament_dir, oppos_path)
    report.errors += errors
    if report.errors:
        return report

    prepared = prepare_block(block, references.decks, references.deck_index, references.oppo_index, references.used_ids)
    report.errors += prepared.errors
    report.warnings += prepared.warnings
    if report.errors:
        return report

    append_rows(tournament_dir / "games.csv", prepared.rows)
    report.matches = prepared.matches
    report.games = len(prepared.rows)
    report.match_ids = list(dict.fromkeys(row["match_id"] for row in prepared.rows))
    return report
