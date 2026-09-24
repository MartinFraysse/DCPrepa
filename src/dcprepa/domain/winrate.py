from dataclasses import dataclass

MIN_RELIABLE = 10
NO_DATA = "—"
WARNING = "⚠️"


def format_percent(value: float) -> str:
    """Pourcentage au dixième, 0,05 arrondi au-dessus : 12.25 → « 12.3 », 55.0 → « 55 » (décimale nulle omise)."""
    tenths = int(abs(value) * 10 + 0.5 + 1e-9)
    sign = "-" if value < 0 and tenths else ""
    units, decimal = divmod(tenths, 10)
    return f"{sign}{units}" if decimal == 0 else f"{sign}{units}.{decimal}"


@dataclass(frozen=True)
class Winrate:
    """Victoires sur un total de parties (ou de matchs pour le BO3).

    Affichage (str) : « 55 % (66/120) », « 12.2 % (… ) », « ⚠️ 33.3 % (1/3) » sous 10, « — » si le total est nul.
    """

    wins: int
    total: int

    def __post_init__(self):
        if self.total < 0 or not 0 <= self.wins <= self.total:
            raise ValueError(f"winrate impossible : {self.wins}/{self.total}")

    @property
    def rate(self) -> float | None:
        """Winrate exact en pourcentage (ex. 66.666…), None si aucune partie."""
        if self.total == 0:
            return None
        return 100 * self.wins / self.total

    @property
    def reliable(self) -> bool:
        """Vrai à partir de 10 (parties, ou matchs pour le BO3)."""
        return self.total >= MIN_RELIABLE

    def __str__(self) -> str:
        if self.total == 0:
            return NO_DATA
        text = f"{format_percent(self.rate)} % ({self.wins}/{self.total})"
        return text if self.reliable else f"{WARNING} {text}"
