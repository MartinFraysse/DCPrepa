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


def append_oppos(path: Path, entries: dict[str, list[str]], comment: str) -> None:
    """Ajoute des oppos à la fin de data/oppos.yaml, sans toucher au reste (commentaires compris).

    entries : nom de référence → variantes (propose_oppos), écrites au format du fichier :
    « Référence: » puis « - variante » indentées de 4 espaces ; comment : ligne de commentaire placée avant le bloc.
    Les noms sont mis entre guillemets seulement si YAML l'exige. Écriture via un fichier .tmp remplacé d'un coup.
    """
    if not entries:
        return
    content = path.read_text(encoding="utf-8")
    if content and not content.endswith("\n"):
        content += "\n"

    lines = ["", f"# {comment}"]
    for reference, variants in entries.items():
        lines.append(f"{_yaml_scalar(reference)}:")
        lines += [f"    - {_yaml_scalar(variant)}" for variant in variants]

    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(content + "\n".join(lines) + "\n", encoding="utf-8")
    temporary.replace(path)


def _yaml_scalar(text: str) -> str:
    """Texte YAML d'un nom : tel quel si possible (« Phelia, Exuberant Shepherd »), sinon entre guillemets."""
    dumped = yaml.safe_dump(text, allow_unicode=True, width=10**6, default_style=None)
    return dumped.split("\n", 1)[0]
