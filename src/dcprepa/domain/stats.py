from dataclasses import dataclass

from dcprepa.domain.oppos import SELF_PLAY_MARK
from dcprepa.domain.winrate import MIN_RELIABLE, Winrate

POSITIONS = ("OTP", "OTD")
SOURCES = ("paper", "cockatrice", "mtgo")
MIN_BO3_GAMES = 2
WINS_TO_WIN_BO3 = 2


@dataclass(frozen=True)
class Record:
    """Les deux winrates, toujours distincts : par partie (toutes les games) et par match BO3 (2 ou 3 games)."""

    games: Winrate
    bo3: Winrate


@dataclass(frozen=True)
class VersionStats:
    """Une version du deck : ses compteurs et son écart aux autres versions, en points (None si incalculable)."""

    version: str
    record: Record
    gap_games: float | None
    gap_bo3: float | None


@dataclass(frozen=True)
class MatchupStats:
    """Un oppo : parties et BO3 ; OTP / OTD seulement à partir de 10 parties contre lui (sinon None)."""

    oppo: str
    record: Record
    otp: Winrate | None
    otd: Winrate | None


@dataclass(frozen=True)
class DeckStats:
    """Toutes les stats d'un deck ; le self-play est à part et exclu de tout le reste."""

    overall: Record
    versions: list[VersionStats]
    positions: dict[str, Winrate]
    sources: dict[str, Record]
    matchups: list[MatchupStats]
    self_play: list[MatchupStats]


def compute_deck_stats(games: list[dict[str, str]], deck: str, versions: list[str]) -> DeckStats:
    """Calcule les stats d'un deck à partir des lignes de games.csv (read_games).

    games : toutes les games du fichier, celles des autres decks sont ignorées ;
    versions : versions de la fiche, de la plus ancienne à la plus récente. Une version jouée
    mais absente de la fiche est ajoutée à la fin (le service le signale).
    """
    own = [game for game in games if game["deck"] == deck]
    self_play = [game for game in own if SELF_PLAY_MARK in game["oppo"]]
    played = [game for game in own if SELF_PLAY_MARK not in game["oppo"]]

    return DeckStats(
        overall=record(played),
        versions=_versions(played, versions),
        positions=_positions(played),
        sources=_sources(played),
        matchups=_matchups(played),
        self_play=_matchups(self_play),
    )


def record(games: list[dict[str, str]]) -> Record:
    """Winrate par partie et winrate BO3 d'un ensemble de games."""
    matches = bo3_matches(games)
    return Record(
        games=_game_winrate(games),
        bo3=Winrate(sum(_bo3_won(match) for match in matches), len(matches)),
    )


def bo3_matches(games: list[dict[str, str]]) -> list[list[dict[str, str]]]:
    """Regroupe les games par match_id et garde les BO3 (2 ou 3 games) ; un match d'une game est un BO1."""
    matches = {}
    for game in games:
        matches.setdefault(game["match_id"], []).append(game)
    return [match for match in matches.values() if len(match) >= MIN_BO3_GAMES]


def version_gaps(rates: dict[str, float | None]) -> dict[str, float | None]:
    """Écart de chaque version : son winrate − moyenne simple des winrates des autres versions.

    Les versions sans partie (None) ne comptent pas dans la moyenne ; écart None si la version
    n'a pas de partie ou si aucune autre version n'en a.
    """
    gaps = {}
    for version, rate in rates.items():
        others = [other for name, other in rates.items() if name != version and other is not None]
        gaps[version] = None if rate is None or not others else rate - sum(others) / len(others)
    return gaps


def _game_winrate(games: list[dict[str, str]]) -> Winrate:
    return Winrate(sum(game["resultat"] == "W" for game in games), len(games))


def _bo3_won(match: list[dict[str, str]]) -> bool:
    """Gagné = 2 victoires ; un 1-1 est un match non gagné."""
    return sum(game["resultat"] == "W" for game in match) >= WINS_TO_WIN_BO3


def _versions(games: list[dict[str, str]], versions: list[str]) -> list[VersionStats]:
    names = list(versions) + [v for v in dict.fromkeys(game["version"] for game in games) if v not in versions]
    records = {name: record([game for game in games if game["version"] == name]) for name in names}
    gaps_games = version_gaps({name: rec.games.rate for name, rec in records.items()})
    gaps_bo3 = version_gaps({name: rec.bo3.rate for name, rec in records.items()})
    return [VersionStats(name, records[name], gaps_games[name], gaps_bo3[name]) for name in names]


def _positions(games: list[dict[str, str]]) -> dict[str, Winrate]:
    return {position: _game_winrate([game for game in games if game["position"] == position]) for position in POSITIONS}


def _sources(games: list[dict[str, str]]) -> dict[str, Record]:
    extra = sorted({game["source"] for game in games} - set(SOURCES))
    return {source: record([game for game in games if game["source"] == source]) for source in (*SOURCES, *extra)}


def _matchups(games: list[dict[str, str]]) -> list[MatchupStats]:
    """Un MatchupStats par oppo, triés par nombre de parties (décroissant) puis par nom."""
    by_oppo = {}
    for game in games:
        by_oppo.setdefault(game["oppo"], []).append(game)

    matchups = []
    for oppo, oppo_games in by_oppo.items():
        positions = _positions(oppo_games) if len(oppo_games) >= MIN_RELIABLE else {}
        matchups.append(MatchupStats(oppo, record(oppo_games), positions.get("OTP"), positions.get("OTD")))
    return sorted(matchups, key=lambda matchup: (-matchup.record.games.total, matchup.oppo.lower()))
