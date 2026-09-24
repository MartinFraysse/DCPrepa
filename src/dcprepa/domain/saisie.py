import re
import unicodedata
from datetime import datetime

from dcprepa.domain.validation import DATE_FORMAT

TOURNAMENT_FIELDS = ("name", "format", "date", "location", "banlist", "notes")


def slugify(name: str) -> str:
    """Slug d'un nom : minuscules, accents retirés, tout autre caractère que lettre ou chiffre → « - ».

    Ex. « RelicFest 2026 » → « relicfest-2026 », « Été Duel #3 » → « ete-duel-3 » ; « » si rien d'utilisable.
    """
    text = unicodedata.normalize("NFKD", str(name))
    text = "".join(char for char in text if not unicodedata.combining(char)).lower()
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


def check_tournament_fields(fields: dict[str, str], creating: bool) -> list[str]:
    """Vérifie les champs d'une fiche de tournoi à écrire (tournament.yaml).

    Champs possibles : name, format, date, location, banlist, notes (le slug se déduit du nom, il ne se modifie pas).
    creating : le nom est obligatoire. Date au format JJ/MM/AAAA si elle est remplie.
    """
    errors = [f"champ non modifiable ici : {name} (possibles : {', '.join(TOURNAMENT_FIELDS)})" for name in fields if name not in TOURNAMENT_FIELDS]
    if not creating and not fields:
        errors.append("rien à modifier")
    name = fields.get("name")
    if (creating or name is not None) and not str(name or "").strip():
        errors.append("nom du tournoi vide")
    elif name is not None and not slugify(name):
        errors.append(f"nom du tournoi sans lettre ni chiffre : {name}")
    date = str(fields.get("date") or "").strip()
    if date:
        try:
            datetime.strptime(date, DATE_FORMAT)
        except ValueError:
            errors.append(f"date invalide (attendu : JJ/MM/AAAA) : {date}")
    return errors
