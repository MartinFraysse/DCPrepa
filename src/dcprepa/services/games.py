from dataclasses import dataclass, field
from pathlib import Path

from dcprepa.domain import edits
from dcprepa.domain.blocks import prepare_block
from dcprepa.domain.edits import References
from dcprepa.domain.names import build_name_index
from dcprepa.domain.oppos import build_oppo_index
from dcprepa.storage.decks import load_deck_aliases, load_decks
from dcprepa.storage.games import append_rows, read_games, write_games
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
    """Bilan d'une saisie ou d'une correction de games : BO et games écrits, leurs match_id, erreurs (bloquantes) et avertissements.

    Correction : matches = 1 et games = nombre de games du BO après correction (0 et [] si le BO a été supprimé).
    """

    matches: int = 0
    games: int = 0
    match_ids: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def load_game_references(tournament_dir: Path, oppos_path: Path) -> tuple[GameReferences, list[str]]:
    """Lit les fiches deck, decks/_alias.yaml, data/oppos.yaml et games.csv (pour ses match_id).

    games.csv est entièrement vérifié (read_games) : on n'ajoute jamais de games à un fichier déjà invalide, que les stats refuseraient.
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
    games, found = read_games(tournament_dir / "games.csv")
    errors += found
    used_ids = {game["match_id"] for game in games if game["match_id"]}
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


def edit_game(tournament_dir: Path, match_id: str, number: str, changes: dict[str, str], oppos_path: Path) -> GamesReport:
    """Corrige une game : position, résultat et / ou note, ex. edit_game(t, "02/10/2026-01", "2", {"resultat": "W"}, oppos).

    Le BO est revérifié comme à l'import ; à la moindre erreur, games.csv n'est pas modifié.
    """
    return _correct(tournament_dir, oppos_path, lambda games, refs: edits.edit_game(games, match_id, number, changes, refs))


def edit_match(tournament_dir: Path, match_id: str, changes: dict[str, str], oppos_path: Path) -> GamesReport:
    """Corrige toutes les games d'un BO : date, source, deck, version et / ou oppo, ex. {"oppo": "Kess"}.

    Mêmes contrôles que l'import ; date changée → nouveau match_id (dans report.match_ids).
    """
    return _correct(tournament_dir, oppos_path, lambda games, refs: edits.edit_match(games, match_id, changes, refs))


def delete_game(tournament_dir: Path, match_id: str, number: str) -> GamesReport:
    """Supprime une game d'un BO ; les suivantes sont renumérotées, un BO réduit à une game devient un BO1 (avertissement)."""
    return _correct(tournament_dir, None, lambda games, _: edits.delete_game(games, match_id, number))


def delete_match(tournament_dir: Path, match_id: str) -> GamesReport:
    """Supprime toutes les games d'un BO."""
    return _correct(tournament_dir, None, lambda games, _: edits.delete_match(games, match_id))


def _correct(tournament_dir: Path, oppos_path: Path | None, operation) -> GamesReport:
    """Lit games.csv (et les références si oppos_path, pour revérifier un BO), applique la correction, réécrit games.csv.

    games.csv invalide, références invalides ou correction refusée : rien n'est écrit.
    """
    report = GamesReport()
    games_path = tournament_dir / "games.csv"
    games, errors = read_games(games_path)
    report.errors += errors
    refs = None
    if oppos_path is not None and not report.errors:
        references, errors = load_game_references(tournament_dir, oppos_path)
        report.errors += errors
        refs = References(references.decks, references.deck_index, references.oppo_index)
    if report.errors:
        return report

    result = operation(games, refs)
    report.errors += result.errors
    report.warnings += result.warnings
    if report.errors:
        return report

    write_games(games_path, result.games)
    report.matches = 1 if result.match_id else 0
    report.games = result.changed
    report.match_ids = [result.match_id] if result.match_id else []
    return report
