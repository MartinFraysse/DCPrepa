from pathlib import Path

import yaml


def load_oppos(path: Path) -> tuple[dict[str, list[str]], list[str]]:
    """Lit data/oppos.yaml : nom de référence → liste de ses variantes.

    Un fichier sans entrée (seulement des commentaires) est valide et donne {}.
    Une référence sans variante est acceptée (seul son nom est reconnu).

    Renvoie (oppos, errors), jamais les deux remplis,
    ex. ({"Ragavan": ["Ragavan, Nimble Pilferer", "raga"]}, []).
    """
    if not path.is_file():
        return {}, [f"fichier introuvable : {path}"]

    try:
        content = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as error:
        return {}, [f"{path.name} : YAML illisible : {error}"]

    if content is None:
        return {}, []
    if not isinstance(content, dict):
        return {}, [f"{path.name} : attendu « Nom de référence: » suivi de ses variantes"]

    oppos = {}
    errors = []
    for reference, variants in content.items():
        name = str(reference).strip()
        if variants is None:
            variants = []
        if not isinstance(variants, list):
            errors.append(f"{path.name} : {name} : variantes attendues sous forme de liste (« - variante »)")
            continue
        oppos[name] = [str(variant).strip() for variant in variants if variant is not None]

    if errors:
        return {}, errors
    return oppos, errors
