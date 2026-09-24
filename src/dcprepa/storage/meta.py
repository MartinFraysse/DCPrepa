import csv
import math
from datetime import datetime
from pathlib import Path

META_COLUMNS = ["oppo", "decks", "poids"]
META_NAME_FORMAT = "%Y-%m-%d"


def load_latest_meta(tournament_dir: Path) -> tuple[str | None, dict[str, float], list[str]]:
    """Lit le méta le plus récent du tournoi : meta/AAAA-MM-JJ.csv, choisi d'après la date du nom.

    Les autres fichiers de meta/ (README.md, CSV mal nommé) sont ignorés. Pas de méta
    (dossier absent ou aucun fichier daté) : (None, {}, []), ce n'est pas une erreur.
    Vérifie l'en-tête (exactement META_COLUMNS), puis chaque ligne : colonnes, oppo non vide
    et non répété, decks entier ≥ 0, poids nombre ≥ 0 (en %, point décimal).

    Renvoie (nom du fichier, poids par oppo, errors), ex. ("2026-10-01.csv", {"Ragavan": 12.5}, []) ;
    en cas d'erreur, poids vides.
    """
    meta_dir = tournament_dir / "meta"
    dated = [path for path in meta_dir.glob("*.csv") if _date_of(path)] if meta_dir.is_dir() else []
    if not dated:
        return None, {}, []
    path = max(dated, key=_date_of)

    with path.open(encoding="utf-8-sig", newline="") as file:
        rows = list(csv.reader(file))

    if not rows or rows[0] != META_COLUMNS:
        found = ",".join(rows[0]) if rows else "(fichier vide)"
        return path.name, {}, [f"meta/{path.name} : en-tête inattendu : {found} (attendu : {','.join(META_COLUMNS)})"]

    weights = {}
    errors = []
    for line, row in enumerate(rows[1:], start=2):
        if not any(value.strip() for value in row):
            continue
        prefix = f"meta/{path.name} : ligne {line}"
        if len(row) != len(META_COLUMNS):
            errors.append(f"{prefix} : {len(row)} colonnes au lieu de {len(META_COLUMNS)}")
            continue
        oppo, decks, weight = (value.strip() for value in row)
        if not oppo:
            errors.append(f"{prefix} : oppo vide")
        elif oppo in weights:
            errors.append(f"{prefix} : oppo en double : {oppo}")
        if not decks.isdigit():
            errors.append(f"{prefix} : decks attendu en nombre entier : {decks}")
        value = _number(weight)
        if value is None:
            errors.append(f"{prefix} : poids attendu en nombre positif (ex. 12.5) : {weight}")
        if oppo and value is not None:
            weights.setdefault(oppo, value)

    if errors:
        return path.name, {}, errors
    return path.name, weights, errors


def _date_of(path: Path) -> datetime | None:
    try:
        return datetime.strptime(path.stem, META_NAME_FORMAT)
    except ValueError:
        return None


def _number(text: str) -> float | None:
    try:
        value = float(text)
    except ValueError:
        return None
    return value if math.isfinite(value) and value >= 0 else None
