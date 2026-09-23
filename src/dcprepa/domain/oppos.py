from dcprepa.domain.names import build_name_index, name_key

SELF_PLAY_MARK = "@"


def build_oppo_index(oppos: dict[str, list[str]]) -> tuple[dict[str, str], list[str]]:
    """Construit la table de correspondance « forme souple → nom de référence » des oppos.

    Chaque nom de référence et chacune de ses variantes y figurent.
    Une même forme rattachée à deux références différentes est une erreur (oppos.yaml ambigu).

    Renvoie (index, errors), jamais les deux remplis, ex. ({"raga": "Ragavan", "ragavan": "Ragavan"}, []).
    """
    return build_name_index(oppos, "oppos.yaml")


def normalize_oppo(oppo: str, index: dict[str, str]) -> tuple[str, str | None]:
    """Ramène l'oppo saisi à son nom de référence.

    - trouvé (sans tenir compte des majuscules ni des espaces en trop) : (référence, None) ;
    - self-play « deck@version » : gardé tel quel, sans avertissement (voir domain/decks.py::resolve_self_play) ;
    - inconnu : gardé tel que saisi (espaces retirés) avec un avertissement.
    """
    name = " ".join(str(oppo).split())
    if SELF_PLAY_MARK in name:
        return name, None
    reference = index.get(name_key(name))
    if reference is not None:
        return reference, None
    return name, f"oppo inconnu : {name} → à ajouter dans data/oppos.yaml"
