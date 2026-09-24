from dataclasses import dataclass

from dcprepa.domain.oppos import SELF_PLAY_MARK
from dcprepa.domain.winrate import MIN_RELIABLE, Winrate

POSITIONS = ("OTP", "OTD")
SOURCES = ("paper", "cockatrice", "mtgo")
MIN_BO3_GAMES = 2
WINS_TO_WIN_BO3 = 2


@dataclass(frozen=True)
class Record:
    """Les deux winrates, toujours distincts : par game (toutes les games) et par BO3 (2 ou 3 games)."""

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
class BestVersion:
    """La version au meilleur winrate contre un oppo ; gap = son winrate − celui du matchup, en points."""

    version: str
    winrate: Winrate
    gap: float


@dataclass(frozen=True)
class MatchupStats:
    """Un oppo : games et BO3 ; OTP / OTD seulement à partir de 10 games contre lui (sinon None).

    weight_paper / weight_general : son poids dans le méta papier / général, en % (None sans méta ou si l'oppo n'y figure pas).
    best_games / best_bo3 : meilleure version contre l'oppo, par game et par BO3
    (None si moins de deux versions l'ont joué).
    """

    oppo: str
    record: Record
    otp: Winrate | None
    otd: Winrate | None
    weight_paper: float | None = None
    weight_general: float | None = None
    best_games: BestVersion | None = None
    best_bo3: BestVersion | None = None


@dataclass(frozen=True)
class DeckStats:
    """Toutes les stats d'un deck ; le self-play est à part et exclu de tout le reste."""

    overall: Record
    versions: list[VersionStats]
    positions: dict[str, Winrate]
    sources: dict[str, Record]
    matchups: list[MatchupStats]
    self_play: list[MatchupStats]


def compute_deck_stats(
    games: list[dict[str, str]], deck: str, versions: list[str], metas: dict[str, dict[str, float]] | None = None
) -> DeckStats:
    """Calcule les stats d'un deck à partir des lignes de games.csv (read_games).

    games : toutes les games du fichier, celles des autres decks sont ignorées ;
    versions : versions de la fiche, de la plus ancienne à la plus récente. Une version jouée
    mais absente de la fiche est ajoutée à la fin (le service le signale) ;
    metas : poids par oppo de chaque méta, {"paper": {…}, "general": {…}} (load_latest_meta), None ou vide sans méta.
    """
    own = [game for game in games if game["deck"] == deck]
    self_play = [game for game in own if SELF_PLAY_MARK in game["oppo"]]
    played = [game for game in own if SELF_PLAY_MARK not in game["oppo"]]

    return DeckStats(
        overall=record(played),
        versions=_versions(played, versions),
        positions=_positions(played),
        sources=_sources(played),
        matchups=_matchups(played, metas or {}, versions),
        self_play=_matchups(self_play, {}, versions),
    )


def record(games: list[dict[str, str]]) -> Record:
    """Winrate par game et winrate BO3 d'un ensemble de games."""
    matches = bo3_matches(games)
    return Record(
        games=_game_winrate(games),
        bo3=Winrate(sum(_bo3_won(match) for match in matches), len(matches)),
    )


def bo3_matches(games: list[dict[str, str]]) -> list[list[dict[str, str]]]:
    """Regroupe les games par match_id et garde les BO3 (2 ou 3 games) ; un BO d'une seule game est un BO1."""
    matches = {}
    for game in games:
        matches.setdefault(game["match_id"], []).append(game)
    return [match for match in matches.values() if len(match) >= MIN_BO3_GAMES]


def version_gaps(rates: dict[str, float | None]) -> dict[str, float | None]:
    """Écart de chaque version : son winrate − moyenne simple des winrates des autres versions.

    Les versions sans game (None) ne comptent pas dans la moyenne ; écart None si la version
    n'a pas de game ou si aucune autre version n'en a.
    """
    gaps = {}
    for version, rate in rates.items():
        others = [other for name, other in rates.items() if name != version and other is not None]
        gaps[version] = None if rate is None or not others else rate - sum(others) / len(others)
    return gaps


def _game_winrate(games: list[dict[str, str]]) -> Winrate:
    return Winrate(sum(game["resultat"] == "W" for game in games), len(games))


def _bo3_won(match: list[dict[str, str]]) -> bool:
    """Gagné = 2 victoires ; un 1-1 est un BO3 non gagné."""
    return sum(game["resultat"] == "W" for game in match) >= WINS_TO_WIN_BO3


def best_version(winrates: dict[str, Winrate], overall: Winrate) -> BestVersion | None:
    """Version au meilleur winrate parmi celles qui ont joué (total > 0), comparée au winrate d'ensemble.

    winrates : winrate de chaque version, dans l'ordre de la fiche. À égalité : le plus grand total,
    puis la version la plus récente. None si moins de deux versions ont joué.
    """
    played = [(index, version, winrate) for index, (version, winrate) in enumerate(winrates.items()) if winrate.total]
    if len(played) < 2:
        return None
    _, version, winrate = max(played, key=lambda item: (item[2].rate, item[2].total, item[0]))
    return BestVersion(version, winrate, winrate.rate - overall.rate)


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


def _matchups(games: list[dict[str, str]], metas: dict[str, dict[str, float]], versions: list[str]) -> list[MatchupStats]:
    """Un MatchupStats par oppo, avec la meilleure version contre lui (par game et par BO3).

    Tri : par poids dans le méta papier (décroissant) ; puis les oppos absents du papier, par poids général ;
    puis ceux absents des deux ; à égalité, et toujours sans méta, par nombre de games (décroissant) puis par nom.
    """
    by_oppo = {}
    for game in games:
        by_oppo.setdefault(game["oppo"], []).append(game)

    matchups = []
    for oppo, oppo_games in by_oppo.items():
        positions = _positions(oppo_games) if len(oppo_games) >= MIN_RELIABLE else {}
        overall = record(oppo_games)
        names = list(versions) + [v for v in dict.fromkeys(game["version"] for game in oppo_games) if v not in versions]
        by_version = {name: record([game for game in oppo_games if game["version"] == name]) for name in names}
        matchups.append(
            MatchupStats(
                oppo, overall, positions.get("OTP"), positions.get("OTD"),
                weight_paper=metas.get("paper", {}).get(oppo),
                weight_general=metas.get("general", {}).get(oppo),
                best_games=best_version({name: rec.games for name, rec in by_version.items()}, overall.games),
                best_bo3=best_version({name: rec.bo3 for name, rec in by_version.items()}, overall.bo3),
            )
        )
    return sorted(
        matchups,
        key=lambda m: (
            m.weight_paper is None, -(m.weight_paper or 0),
            m.weight_general is None, -(m.weight_general or 0),
            -m.record.games.total, m.oppo.lower(),
        ),
    )
