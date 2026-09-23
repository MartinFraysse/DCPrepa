import csv
from pathlib import Path

COLUMNS = ["date", "match_id", "partie", "source", "deck", "version", "oppo", "position", "resultat", "note/ressenti"]


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
