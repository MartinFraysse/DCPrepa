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


def check_new_oppo(name: str, variant_of: str | None, index: dict[str, str]) -> tuple[str | None, list[str]]:
    """Vérifie un nom d'oppo à ajouter à data/oppos.yaml, comme nouvelle référence ou comme variante d'une référence.

    name : nom saisi (espaces en trop retirés) ; variant_of : None pour un nouvel oppo, sinon une forme connue de la référence
    (nom ou variante, ex. « raga » → Ragavan) ; index : build_oppo_index.
    Refusé : nom vide, « @ » (réservé au self-play deck@version), nom déjà connu, référence inconnue.
    Renvoie (référence, errors) : la référence de rattachement (None pour un nouvel oppo).
    """
    name = " ".join(str(name).split())
    errors = []
    if not name:
        errors.append("nom d'oppo vide")
    elif SELF_PLAY_MARK in name:
        errors.append(f"« {SELF_PLAY_MARK} » est réservé au self-play (deck@version) : {name}")
    elif name_key(name) in index:
        errors.append(f"oppo déjà connu : {name} → {index[name_key(name)]}")

    reference = None
    if variant_of is not None:
        reference = index.get(name_key(variant_of))
        if reference is None:
            errors.append(f"oppo de référence inconnu : {' '.join(str(variant_of).split())}")
    return (None if errors else reference), errors
