from datetime import datetime

from dcprepa.domain.validation import DATE_FORMAT


def normalize_date(date: str) -> str:
    """Réécrit une date JJ/MM/AAAA déjà validée avec ses zéros, ex. « 2/10/2026 » → « 02/10/2026 »."""
    return datetime.strptime(str(date).strip(), DATE_FORMAT).strftime(DATE_FORMAT)


def next_match_id(date: str, used_ids: set[str]) -> str:
    """Prochain match_id libre pour une date JJ/MM/AAAA : « JJ/MM/AAAA-NN », ex. « 02/10/2026-01 ».

    NN repart de 01 pour chaque date et suit le plus grand numéro déjà utilisé ce jour-là
    (pas de trou comblé : l'ordre des match_id reste l'ordre de saisie).
    """
    prefix = normalize_date(date)
    numbers = [
        int(match_id[len(prefix) + 1:])
        for match_id in used_ids
        if match_id.startswith(prefix + "-") and match_id[len(prefix) + 1:].isdigit()
    ]
    return f"{prefix}-{max(numbers, default=0) + 1:02d}"


def build_rows(block: dict, bos: list[list[list[str]]], oppo: str, used_ids: set[str]) -> list[dict[str, str]]:
    """Transforme un bloc validé en lignes de games.csv : une ligne par game, un match_id par BO.

    block : bloc de l'inbox déjà validé (validate_block sans erreur) ;
    bos : résultat de parse_bos ; oppo : nom déjà normalisé (normalize_oppo).
    used_ids est complété avec les match_id attribués, pour que les blocs suivants continuent la numérotation.
    La note du bloc est recopiée sur chaque ligne.
    """
    note = block.get("note/ressenti")
    common = {
        "date": normalize_date(block["date"]),
        "source": str(block["source"]).strip().lower(),
        "deck": str(block["deck"]).strip(),
        "version": str(block["version"]).strip(),
        "oppo": oppo,
        "note/ressenti": "" if note is None else " ".join(str(note).split()),
    }

    rows = []
    for games in bos:
        match_id = next_match_id(common["date"], used_ids)
        used_ids.add(match_id)
        for number, (position, result) in enumerate(games, start=1):
            rows.append({**common, "match_id": match_id, "partie": str(number), "position": position, "resultat": result})
    return rows
