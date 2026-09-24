import csv
from pathlib import Path

COLUMNS = ["date", "match_id", "game", "source", "deck", "version", "oppo", "position", "resultat", "note/ressenti"]


def read_match_ids(path: Path) -> tuple[set[str], list[str]]:
    """Lit games.csv et renvoie les match_id déjà utilisés.

    Vérifie que le fichier existe et que son en-tête est exactement COLUMNS.
    Renvoie (match_ids, errors), jamais les deux remplis.
    """
    if not path.is_file():
        return set(), [f"fichier introuvable : {path}"]

    with path.open(encoding="utf-8-sig", newline="") as file:
        rows = list(csv.reader(file))

    if not rows or rows[0] != COLUMNS:
        found = ",".join(rows[0]) if rows else "(fichier vide)"
        return set(), [f"{path.name} : en-tête inattendu : {found} (attendu : {','.join(COLUMNS)})"]

    match_ids = {row[1] for row in rows[1:] if len(row) > 1 and row[1]}
    return match_ids, []


POSITIONS = ("OTP", "OTD")
RESULTS = ("W", "L")


def read_games(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    """Lit toutes les lignes de games.csv (une par game), pour les stats.

    Vérifie l'en-tête (exactement COLUMNS), puis chaque ligne : nombre de colonnes,
    position (OTP / OTD) et résultat (W / L). Les erreurs donnent le numéro de ligne du fichier.
    Renvoie (games, errors), jamais les deux remplis ; chaque game est un dict colonne → valeur.
    """
    if not path.is_file():
        return [], [f"fichier introuvable : {path}"]

    with path.open(encoding="utf-8-sig", newline="") as file:
        rows = list(csv.reader(file))

    if not rows or rows[0] != COLUMNS:
        found = ",".join(rows[0]) if rows else "(fichier vide)"
        return [], [f"{path.name} : en-tête inattendu : {found} (attendu : {','.join(COLUMNS)})"]

    games = []
    errors = []
    for line, row in enumerate(rows[1:], start=2):
        if not any(value.strip() for value in row):
            continue
        prefix = f"{path.name} : ligne {line}"
        if len(row) != len(COLUMNS):
            errors.append(f"{prefix} : {len(row)} colonnes au lieu de {len(COLUMNS)}")
            continue
        game = dict(zip(COLUMNS, row))
        if game["position"] not in POSITIONS:
            errors.append(f"{prefix} : position inconnue (OTP ou OTD) : {game['position']}")
        if game["resultat"] not in RESULTS:
            errors.append(f"{prefix} : résultat inconnu (W ou L) : {game['resultat']}")
        games.append(game)

    if errors:
        return [], errors
    return games, errors


def append_rows(path: Path, rows: list[dict[str, str]]) -> None:
    """Ajoute des lignes à la fin de games.csv (une ligne par game, colonnes COLUMNS).

    Le module csv met entre guillemets les valeurs qui contiennent une virgule.
    Les fins de ligne du fichier (LF ou CRLF) sont conservées. L'écriture passe par un
    fichier temporaire remplacé d'un coup : games.csv n'est jamais écrit à moitié.
    """
    with path.open(encoding="utf-8", newline="") as file:
        content = file.read()

    newline = "\r\n" if "\r\n" in content else "\n"
    if content and not content.endswith(("\n", "\r")):
        content += newline

    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as file:
        file.write(content)
        writer = csv.DictWriter(file, fieldnames=COLUMNS, lineterminator=newline)
        writer.writerows(rows)
    temporary.replace(path)
