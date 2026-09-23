SELF_PLAY_MARK = "@"


def _key(name: str) -> str:
    """Forme de comparaison souple : minuscules, espaces en trop retirés."""
    return " ".join(str(name).lower().split())


def build_oppo_index(oppos: dict[str, list[str]]) -> tuple[dict[str, str], list[str]]:
    """Construit la table de correspondance « forme souple → nom de référence ».

    Chaque nom de référence et chacune de ses variantes y figurent.
    Une même forme rattachée à deux références différentes est une erreur (oppos.yaml ambigu).

    Renvoie (index, errors), jamais les deux remplis, ex. ({"raga": "Ragavan", "ragavan": "Ragavan"}, []).
    """
    index = {}
    errors = []
    for reference, variants in oppos.items():
        for name in [reference, *variants]:
            key = _key(name)
            if not key:
                continue
            known = index.get(key)
            if known is not None and known != reference:
                errors.append(f"oppos.yaml : « {name} » renvoie à la fois vers {known} et {reference}")
                continue
            index[key] = reference

    if errors:
        return {}, errors
    return index, errors


def normalize_oppo(oppo: str, index: dict[str, str]) -> tuple[str, str | None]:
    """Ramène l'oppo saisi à son nom de référence.

    - trouvé (sans tenir compte des majuscules ni des espaces en trop) : (référence, None) ;
    - self-play « deck@version » : gardé tel quel, sans avertissement ;
    - inconnu : gardé tel que saisi (espaces retirés) avec un avertissement.
    """
    name = " ".join(str(oppo).split())
    if SELF_PLAY_MARK in name:
        return name, None
    reference = index.get(_key(name))
    if reference is not None:
        return reference, None
    return name, f"oppo inconnu : {name} → à ajouter dans data/oppos.yaml"
