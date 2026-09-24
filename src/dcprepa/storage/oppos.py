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


def insert_variant(path: Path, reference: str, variant: str) -> bool:
    """Ajoute une variante sous un nom de référence de data/oppos.yaml, sans toucher au reste (commentaires compris).

    La ligne « - variante » (indentée de 4 espaces) est placée après les variantes existantes de la référence.
    Le texte obtenu est relu avant l'écriture : si la variante n'y est pas rattachée à la référence (référence introuvable,
    fichier inattendu), rien n'est écrit et la fonction renvoie False. Écriture via un fichier .tmp remplacé d'un coup.
    """
    content = path.read_text(encoding="utf-8")
    lines = content.split("\n")
    start = next((index for index, line in enumerate(lines) if _reference_of(line) == reference), None)
    if start is None:
        return False
    end = start + 1
    while end < len(lines) and lines[end][:1] in (" ", "\t"):
        end += 1
    lines.insert(end, f"    - {_yaml_scalar(variant)}")
    updated = "\n".join(lines)

    try:
        parsed = yaml.safe_load(updated)
    except yaml.YAMLError:
        return False
    if not isinstance(parsed, dict) or variant not in [str(v).strip() for v in parsed.get(reference) or []]:
        return False

    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(updated, encoding="utf-8")
    temporary.replace(path)
    return True


def _reference_of(line: str) -> str | None:
    """Nom de référence d'une ligne « Référence: » non indentée (guillemets compris), None pour toute autre ligne."""
    if not line or line[0] in " \t#" or not line.rstrip().endswith(":"):
        return None
    try:
        parsed = yaml.safe_load(line)
    except yaml.YAMLError:
        return None
    if isinstance(parsed, dict) and len(parsed) == 1:
        return str(next(iter(parsed))).strip()
    return None


def _yaml_scalar(text: str) -> str:
    """Texte YAML d'un nom : tel quel si possible (« Phelia, Exuberant Shepherd »), sinon entre guillemets."""
    dumped = yaml.safe_dump(text, allow_unicode=True, width=10**6, default_style=None)
    return dumped.split("\n", 1)[0]
