from datetime import datetime

from dcprepa.domain.games import parse_bos

SOURCES = {"paper", "mtgo", "cockatrice"}
REQUIRED_FIELDS = ["date", "source", "deck", "version", "oppo", "games"]
DATE_FORMAT = "%d/%m/%Y"


def validate_block(block: dict, decks: dict[str, list[str]]) -> list[str]:
    """Vérifie un bloc de l'inbox et renvoie la liste de tous ses problèmes.

    decks : decks connus et leurs versions, ex. {"terra-midrange": ["v1", "v2"]}
    (fourni par l'appelant : domain ne lit aucun fichier).

    Contrôles : champs obligatoires présents et non vides, date JJ/MM/AAAA valide,
    source connue, deck connu, version existante pour ce deck, champ « games » valide.
    Renvoie [] si le bloc est valide.
    """
    if not isinstance(block, dict):
        return [f"bloc mal formé (attendu : une ligne « champ: valeur » par champ) : {block}"]

    errors = []
    for field in REQUIRED_FIELDS:
        value = block.get(field)
        if value is None or not str(value).strip():
            errors.append(f"champ manquant : {field}")
    if errors:
        return errors

    date = str(block["date"]).strip()
    try:
        datetime.strptime(date, DATE_FORMAT)
    except ValueError:
        errors.append(f"date invalide (attendu : JJ/MM/AAAA) : {date}")

    source = str(block["source"]).strip().lower()
    if source not in SOURCES:
        errors.append(f"source inconnue (paper, mtgo ou cockatrice) : {source}")

    deck = str(block["deck"]).strip()
    version = str(block["version"]).strip()
    if deck not in decks:
        available = ", ".join(sorted(decks)) or "aucun"
        errors.append(f"deck inconnu : {deck} (decks disponibles : {available})")
    elif version not in decks[deck]:
        errors.append(f"version inconnue pour {deck} : {version}")

    _, games_errors = parse_bos(str(block["games"]))
    for message in games_errors:
        errors.append(f"games : {message}")

    return errors
