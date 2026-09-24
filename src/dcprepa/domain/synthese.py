from dataclasses import dataclass

from dcprepa.domain.stats import MatchupStats
from dcprepa.domain.winrate import NO_DATA, WARNING, format_percent

METAS = ("paper", "general")
BASES = ("games", "bo3")
MIN_COVERAGE = 30
ACTIVE_STATUSES = ("retenu", "envisage")
UNTESTED_TOP = 10
MIN_TESTED_BO3 = 10
MIN_TESTED_GAMES = 30


@dataclass(frozen=True)
class ExpectedWinrate:
    """Winrate attendu au tournoi et part du méta (en %) sur laquelle il repose.

    Affichage (str) : « 49.8 % (32.4 % du méta) », « ⚠️ 49.8 % (16.2 % du méta) » sous 30 % du méta,
    « — » si aucun oppo du méta n'a été joué.
    """

    rate: float | None
    coverage: float

    @property
    def reliable(self) -> bool:
        """Vrai à partir de 30 % du méta couvert."""
        return self.coverage >= MIN_COVERAGE

    def __str__(self) -> str:
        if self.rate is None:
            return NO_DATA
        text = f"{format_percent(self.rate)} % ({format_percent(self.coverage)} % du méta)"
        return text if self.reliable else f"{WARNING} {text}"


def expected_winrate(matchups: list[MatchupStats], meta: str, base: str) -> ExpectedWinrate:
    """Winrate attendu d'un deck : moyenne de ses winrates contre les oppos du méta, pondérée par leur poids.

    matchups : ceux du deck (compute_deck_stats), self-play déjà exclu ;
    meta : « paper » ou « general » ; base : « games » ou « bo3 ».
    Seuls comptent les oppos du méta (poids connu) joués au moins une fois dans la base choisie :
    le reste du méta est ignoré et les poids retenus sont ramenés à 100 %. Winrates exacts, sans arrondi.
    """
    if meta not in METAS or base not in BASES:
        raise ValueError(f"méta ou base inconnu : {meta!r}, {base!r}")

    coverage = weighted = 0.0
    for matchup in matchups:
        weight = getattr(matchup, f"weight_{meta}")
        rate = getattr(matchup.record, base).rate
        if weight is None or rate is None:
            continue
        coverage += weight
        weighted += weight * rate
    return ExpectedWinrate(weighted / coverage if coverage else None, coverage)


@dataclass(frozen=True)
class UntestedMatchup:
    """Un oppo du top 10 papier pas encore assez testé par un deck ; rank : son rang dans le méta papier (1 = le plus joué)."""

    deck: str
    oppo: str
    rank: int
    weight: float
    bo3: int
    games: int


def untested_matchups(
    decks: dict[str, tuple[str, list[MatchupStats]]], paper: dict[str, float], top: int = UNTESTED_TOP
) -> list[UntestedMatchup]:
    """Les matchups à tester avant le tournoi : pour chaque deck retenu ou envisagé, les oppos du top 10 papier pas assez joués.

    decks : {deck: (statut, matchups)}, les autres statuts (ecarte, vide…) sont ignorés ;
    paper : poids du méta papier par oppo (load_latest_meta), top 10 par poids décroissant puis par nom.
    Testé = au moins 10 BO3 OU au moins 30 games contre l'oppo ; un oppo jamais joué est non testé (0 / 0).
    Tri : decks dans l'ordre reçu, puis par rang.
    """
    ranking = sorted(paper.items(), key=lambda item: (-item[1], item[0].lower()))[:top]
    untested = []
    for deck, (status, matchups) in decks.items():
        if status not in ACTIVE_STATUSES:
            continue
        records = {matchup.oppo: matchup.record for matchup in matchups}
        for rank, (oppo, weight) in enumerate(ranking, start=1):
            record = records.get(oppo)
            bo3, games = (record.bo3.total, record.games.total) if record else (0, 0)
            if bo3 < MIN_TESTED_BO3 and games < MIN_TESTED_GAMES:
                untested.append(UntestedMatchup(deck, oppo, rank, weight, bo3, games))
    return untested
