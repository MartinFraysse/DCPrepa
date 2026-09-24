import csv
import math
from datetime import datetime
from pathlib import Path

META_COLUMNS = ["oppo", "decks", "poids"]
META_NAME_FORMAT = "%Y-%m-%d"
META_FILES = {"general": "general.csv", "paper": "paper.csv"}


def load_latest_meta(tournament_dir: Path) -> tuple[str | None, dict[str, dict[str, float]], list[str]]:
    """Lit le méta le plus récent du tournoi : le dossier meta/AAAA-MM-JJ/ à la date la plus récente.

    Un import = un dossier daté avec general.csv et paper.csv (META_FILES) ; les imports précédents
    restent à côté. Tout ce qui n'est pas un dossier daté (README.md, ancien meta/AAAA-MM-JJ.csv) est ignoré.
    Pas de méta (dossier absent ou aucun dossier daté) : (None, {}, []), ce n'est pas une erreur.
    Un fichier manquant ou invalide dans le dossier le plus récent en est une (contrôles de read_meta).

    Renvoie (nom du dossier, {type: {oppo: poids}}, errors),
    ex. ("2026-09-24", {"general": {"Phelia": 5.81}, "paper": {"Cloud": 6.04}}, []) ; en cas d'erreur, poids vides.
    """
    meta_dir = tournament_dir / "meta"
    dated = [path for path in meta_dir.iterdir() if path.is_dir() and _date_of(path)] if meta_dir.is_dir() else []
    if not dated:
        return None, {}, []
    folder = max(dated, key=_date_of)

    metas = {}
    errors = []
    for kind, file_name in META_FILES.items():
        path = folder / file_name
        label = f"meta/{folder.name}/{file_name}"
        if not path.is_file():
            errors.append(f"{label} : fichier manquant")
            continue
        metas[kind], file_errors = read_meta(path, label)
        errors += file_errors

    if errors:
        return folder.name, {}, errors
    return folder.name, metas, errors


def read_meta(path: Path, label: str) -> tuple[dict[str, float], list[str]]:
    """Lit un fichier méta (colonnes META_COLUMNS) et renvoie le poids de chaque oppo.

    label : nom affiché dans les messages (ex. « meta/2026-10-01/paper.csv »).
    Vérifie l'en-tête (exactement META_COLUMNS), puis chaque ligne : colonnes, oppo non vide
    et non répété, decks entier ≥ 0, poids nombre ≥ 0 (en %, point décimal).
    Renvoie (poids par oppo, errors), jamais les deux remplis, ex. ({"Ragavan": 12.5}, []).
    """
    with path.open(encoding="utf-8-sig", newline="") as file:
        rows = list(csv.reader(file))

    if not rows or rows[0] != META_COLUMNS:
        found = ",".join(rows[0]) if rows else "(fichier vide)"
        return {}, [f"{label} : en-tête inattendu : {found} (attendu : {','.join(META_COLUMNS)})"]

    weights = {}
    errors = []
    for line, row in enumerate(rows[1:], start=2):
        if not any(value.strip() for value in row):
            continue
        prefix = f"{label} : ligne {line}"
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
        return {}, errors
    return weights, errors


def write_meta(path: Path, rows: list[tuple[str, int, float]]) -> None:
    """Écrit un fichier méta : en-tête META_COLUMNS, puis une ligne (oppo, decks, poids) par oppo, dans l'ordre reçu.

    Le dossier (ex. meta/2026-09-24/) est créé s'il manque ; un fichier existant est remplacé.
    Poids écrit sans zéro inutile (5.81, 60, 0.07). Le module csv met entre guillemets les noms qui contiennent
    une virgule. Écriture via un fichier .tmp remplacé d'un coup : jamais de fichier à moitié écrit.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file, lineterminator="\n")
        writer.writerow(META_COLUMNS)
        for oppo, decks, weight in rows:
            writer.writerow([oppo, decks, f"{round(weight, 2):g}"])
    temporary.replace(path)


def _date_of(path: Path) -> datetime | None:
    try:
        return datetime.strptime(path.name, META_NAME_FORMAT)
    except ValueError:
        return None


def _number(text: str) -> float | None:
    try:
        value = float(text)
    except ValueError:
        return None
    return value if math.isfinite(value) and value >= 0 else None
