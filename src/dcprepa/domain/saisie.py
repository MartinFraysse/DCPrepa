import re
import unicodedata
from datetime import datetime

from dcprepa.domain.names import name_key
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


STATUSES = ("retenu", "envisage", "ecarte")
DECK_FIELDS = ("name", "commandant")
RESERVED_DECKS = ("synthese", "readme")
DECK_SIZE = 100
CARD_LINE = re.compile(r"^(\d+)\s+(\S.*)$")
VERSION_PATTERN = re.compile(r"^v(\d+)$")


def check_status(statut: str) -> list[str]:
    """Statut d'un deck : retenu, envisage ou ecarte (sans accents)."""
    if str(statut).strip() in STATUSES:
        return []
    return [f"statut inconnu : {statut} (retenu, envisage ou ecarte)"]


def check_new_deck(name: str, deck_index: dict[str, str]) -> tuple[str, list[str]]:
    """Nom de fichier d'un nouveau deck (slugify du nom, ex. « Terra Midrange » → terra-midrange) et ses problèmes.

    deck_index : appellations des decks existants (build_name_index) ; le nom et le fichier ne doivent désigner aucun deck existant.
    Refusé : nom vide ou sans lettre ni chiffre, nom réservé (synthese, README : fichiers de stats/), appellation déjà prise.
    """
    name = " ".join(str(name).split())
    deck = slugify(name)
    if not name:
        return deck, ["nom du deck vide"]
    if not deck:
        return deck, [f"nom du deck sans lettre ni chiffre : {name}"]
    if deck in RESERVED_DECKS:
        return deck, [f"nom réservé : {deck} (stats/{deck}.md est un fichier du tournoi)"]
    for form in (name, deck):
        known = deck_index.get(name_key(form))
        if known is not None:
            return deck, [f"appellation déjà prise : {form} → {known}"]
    return deck, []


def parse_card_list(text: str) -> tuple[list[str], list[str], list[str]]:
    """Liste d'un deck collée depuis un export MTGO / Moxfield : une ligne « 1 Nom de carte » par carte.

    Renvoie (lignes, errors, warnings) : lignes nettoyées (espaces en trop retirés, lignes vides ignorées) ;
    erreur par ligne mal formée ; avertissement si le total n'est pas de 100 cartes.
    """
    lines, errors = [], []
    for number, raw in enumerate(str(text or "").splitlines(), start=1):
        line = " ".join(raw.split())
        if not line:
            continue
        if not CARD_LINE.match(line):
            errors.append(f"liste : ligne {number} : attendu « 1 Nom de carte » : {line}")
            continue
        lines.append(line)
    warnings = []
    total = sum(int(CARD_LINE.match(line).group(1)) for line in lines)
    if lines and not errors and total != DECK_SIZE:
        warnings.append(f"liste de {total} cartes ({DECK_SIZE} attendues, commandant compris)")
    return lines, errors, warnings


def next_version(versions: list[str]) -> str:
    """Version suivante : « v » + (plus grand numéro vN + 1), ex. [v1, v2, v3] → v4 ; v1 si aucune version numérotée."""
    numbers = [int(match.group(1)) for match in map(VERSION_PATTERN.match, versions) if match]
    return f"v{max(numbers, default=0) + 1}"


def check_new_version(version: str, versions: list[str], cards_in: list[str], cards_out: list[str], card_list: list[str]) -> list[str]:
    """Nouvelle version d'un deck : identifiant libre, sans espace, et au moins un changement (in, out ou liste)."""
    errors = []
    if not version or any(char.isspace() for char in version):
        errors.append(f"identifiant de version invalide : « {version} » (ex. v4, sans espace)")
    elif version in versions:
        errors.append(f"version déjà présente : {version}")
    if not (cards_in or cards_out or card_list):
        errors.append("version sans changement : in, out ou liste attendus")
    return errors
