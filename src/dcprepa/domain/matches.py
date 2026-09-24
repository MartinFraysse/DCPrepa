from dataclasses import dataclass

from dcprepa.domain.stats import MIN_BO3_GAMES, WINS_TO_WIN_BO3

NOTE = "note/ressenti"


@dataclass(frozen=True)
class GameLine:
    """Une game d'un BO, telle qu'affichée : numéro, position, résultat, note."""

    game: str
    position: str
    resultat: str
    note: str


@dataclass(frozen=True)
class MatchSummary:
    """Un BO de games.csv résumé pour l'affichage : ses champs communs, ses games et son score (victoires-défaites).

    outcome : « W » (BO3 gagné), « L » (BO3 perdu), « nul » (BO3 à 1-1) ; pour un BO1, le résultat de sa game.
    """

    match_id: str
    date: str
    source: str
    deck: str
    version: str
    oppo: str
    games: list[GameLine]
    wins: int
    losses: int

    @property
    def is_bo3(self) -> bool:
        return len(self.games) >= MIN_BO3_GAMES

    @property
    def score(self) -> str:
        return f"{self.wins}-{self.losses}"

    @property
    def outcome(self) -> str:
        if not self.is_bo3:
            return self.games[0].resultat if self.games else ""
        if self.wins >= WINS_TO_WIN_BO3:
            return "W"
        if self.losses >= WINS_TO_WIN_BO3:
            return "L"
        return "nul"


def group_matches(games: list[dict[str, str]]) -> list[MatchSummary]:
    """Regroupe les lignes de games.csv (read_games) en BO, du plus récent au plus ancien.

    Ordre : date décroissante (JJ/MM/AAAA), puis numéro du BO décroissant ; games d'un BO triées par numéro.
    """
    by_match: dict[str, list[dict[str, str]]] = {}
    for game in games:
        by_match.setdefault(game["match_id"], []).append(game)

    matches = []
    for match_id, rows in by_match.items():
        rows = sorted(rows, key=lambda row: int(row["game"]) if row["game"].isdigit() else 0)
        first = rows[0]
        lines = [GameLine(row["game"], row["position"], row["resultat"], row[NOTE]) for row in rows]
        wins = sum(row["resultat"] == "W" for row in rows)
        matches.append(
            MatchSummary(match_id, first["date"], first["source"], first["deck"], first["version"], first["oppo"], lines, wins, len(rows) - wins)
        )
    return sorted(matches, key=lambda match: (date_key(match.date), _number(match.match_id)), reverse=True)


def date_key(date: str, unreadable: tuple[int, int, int] = (0, 0, 0)) -> tuple[int, int, int]:
    """JJ/MM/AAAA → (AAAA, MM, JJ) pour trier par date ; unreadable si la date est absente ou illisible."""
    parts = str(date).split("/")
    if len(parts) == 3 and all(part.isdigit() for part in parts):
        return int(parts[2]), int(parts[1]), int(parts[0])
    return unreadable


def _number(match_id: str) -> int:
    """NN d'un match_id « JJ/MM/AAAA-NN » ; 0 s'il est illisible."""
    number = match_id.rsplit("-", 1)[-1]
    return int(number) if number.isdigit() else 0
