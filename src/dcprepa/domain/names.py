def name_key(name: str) -> str:
    """Forme de comparaison souple : minuscules, espaces en trop retirés."""
    return " ".join(str(name).lower().split())


def build_name_index(references: dict[str, list[str]], source: str) -> tuple[dict[str, str], list[str]]:
    """Construit la table « forme souple → nom de référence » (oppos, decks…).

    Chaque nom de référence et chacune de ses variantes y figurent.
    Une même forme rattachée à deux références différentes est une erreur ; source (ex. « oppos.yaml »)
    préfixe le message pour dire quel fichier corriger.

    Renvoie (index, errors), jamais les deux remplis, ex. ({"raga": "Ragavan", "ragavan": "Ragavan"}, []).
    """
    index = {}
    errors = []
    for reference, variants in references.items():
        for name in [reference, *variants]:
            key = name_key(name)
            if not key:
                continue
            known = index.get(key)
            if known is not None and known != reference:
                errors.append(f"{source} : « {name} » renvoie à la fois vers {known} et {reference}")
                continue
            index[key] = reference

    if errors:
        return {}, errors
    return index, errors
