"""Services de lecture pour l'interface : des données prêtes à afficher, pour que l'interface ne lise jamais un fichier elle-même.

Chaque fonction renvoie (données, erreurs) ; avec une erreur, les données sont vides ou partielles et l'interface l'affiche.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path

from dcprepa.domain.matches import MatchSummary, date_key, group_matches
from dcprepa.storage.decks import load_deck_sheets
from dcprepa.storage.games import read_games
from dcprepa.storage.meta import load_latest_meta
from dcprepa.storage.oppos import load_oppos
from dcprepa.storage.tournament import load_tournament_sheet

TOURNAMENTS = "tournaments"
STATS = "stats"
SYNTHESE = "synthese"
REPORT_NAME = re.compile(r"^[a-z0-9][a-z0-9-]*$")


@dataclass(frozen=True)
class TournamentSummary:
    """Un tournoi pour le menu de choix : slug (dossier), nom, date de l'événement, nombre de games (None si games.csv invalide)."""

    slug: str
    name: str
    date: str
    games: int | None


@dataclass(frozen=True)
class TournamentOverview:
    """Tout ce qu'il faut pour afficher un tournoi : fiche, decks (fiches avec statut et versions), méta utilisé, rapports présents."""

    sheet: dict[str, str]
    decks: dict[str, dict]
    meta: str | None
    reports: list[str] = field(default_factory=list)


def list_tournaments(data_dir: Path) -> tuple[list[TournamentSummary], list[str]]:
    """Les tournois de data/tournaments/, triés par date de l'événement (la plus proche d'abord), puis par nom.

    Un dossier sans games.csv lisible reste listé (games = None) avec une erreur : on doit pouvoir l'ouvrir pour le réparer.
    """
    root = data_dir / TOURNAMENTS
    if not root.is_dir():
        return [], []
    summaries, errors = [], []
    for folder in sorted(path for path in root.iterdir() if path.is_dir() and not path.name.startswith((".", "_"))):
        sheet, found = load_tournament_sheet(folder)
        errors += [f"{folder.name} : {message}" for message in found]
        games, found = read_games(folder / "games.csv")
        errors += [f"{folder.name} : {message}" for message in found]
        summaries.append(TournamentSummary(folder.name, sheet["name"], sheet["date"], None if found else len(games)))
    return sorted(summaries, key=lambda item: (date_key(item.date, unreadable=(9999, 99, 99)), item.name.lower())), errors


def tournament_overview(tournament_dir: Path) -> tuple[TournamentOverview, list[str]]:
    """Fiche, decks, méta le plus récent et rapports de stats/ d'un tournoi ; les erreurs de lecture sont rassemblées."""
    sheet, errors = load_tournament_sheet(tournament_dir)
    decks, found = load_deck_sheets(tournament_dir)
    errors += found
    meta, _, found = load_latest_meta(tournament_dir)
    errors += found
    return TournamentOverview(sheet, decks, meta, list_reports(tournament_dir)), errors


def list_matches(tournament_dir: Path) -> tuple[list[MatchSummary], list[str]]:
    """Les BO de games.csv, du plus récent au plus ancien (group_matches) ; games.csv invalide : [] et ses erreurs."""
    games, errors = read_games(tournament_dir / "games.csv")
    return group_matches(games), errors


def list_oppos(oppos_path: Path) -> tuple[dict[str, list[str]], list[str]]:
    """Les oppos de data/oppos.yaml (nom de référence → variantes), triés par nom de référence."""
    oppos, errors = load_oppos(oppos_path)
    return dict(sorted(oppos.items(), key=lambda item: item[0].lower())), errors


def list_reports(tournament_dir: Path) -> list[str]:
    """Rapports présents dans stats/ (sans .md) : la synthèse d'abord, puis les decks par nom ; README et modèles exclus."""
    folder = tournament_dir / STATS
    if not folder.is_dir():
        return []
    names = [path.stem for path in folder.glob("*.md") if REPORT_NAME.match(path.stem) and path.stem != "readme"]
    return sorted(names, key=lambda name: (name != SYNTHESE, name))


def read_report(tournament_dir: Path, name: str) -> tuple[str, list[str]]:
    """Texte Markdown d'un rapport de stats/ (« synthese » ou le nom d'un deck).

    Seuls les rapports listés par list_reports se lisent : un nom avec « / », « .. » ou inconnu est refusé.
    """
    if name not in list_reports(tournament_dir):
        return "", [f"rapport introuvable : {name} (lancer les stats d'abord ?)"]
    return (tournament_dir / STATS / f"{name}.md").read_text(encoding="utf-8"), []

