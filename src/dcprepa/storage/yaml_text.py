import re

import yaml


def yaml_scalar(text: str) -> str:
    """Texte YAML d'une valeur : tel quel si possible (« Phelia, Exuberant Shepherd »), sinon entre guillemets."""
    dumped = yaml.safe_dump(text, allow_unicode=True, width=10**6, default_style=None)
    return dumped.split("\n", 1)[0]


def set_fields(text: str, fields: dict[str, str]) -> str | None:
    """Remplace la valeur de champs « champ: valeur » non indentés d'un texte YAML, en gardant le reste (commentaires compris).

    Le commentaire de fin de ligne d'un champ (« name:   # nom affiché ») reste à sa place ; un champ absent est ajouté à la fin ;
    une valeur vide écrit « champ: ». Le texte obtenu est relu : None si un champ n'y a pas la valeur voulue (fichier inattendu).
    """
    lines = text.split("\n")
    for field, value in fields.items():
        value = " ".join(str(value).split()) if value is not None else ""
        written = f"{field}: {yaml_scalar(value)}" if value else f"{field}:"
        pattern = re.compile(rf"^{re.escape(field)}:(?P<value>.*?)(?P<comment>\s+#.*)?$")
        index = next((i for i, line in enumerate(lines) if pattern.match(line)), None)
        if index is None:
            position = len(lines) - 1 if lines and lines[-1] == "" else len(lines)
            lines.insert(position, written)
            continue
        comment = pattern.match(lines[index]).group("comment")
        if comment:
            column = lines[index].index(comment.lstrip())
            written = written + " " * max(1, column - len(written)) + comment.lstrip()
        lines[index] = written

    updated = "\n".join(lines)
    try:
        parsed = yaml.safe_load(updated)
    except yaml.YAMLError:
        return None
    if not isinstance(parsed, dict):
        return None
    for field, value in fields.items():
        expected = " ".join(str(value).split()) if value is not None else ""
        found = parsed.get(field)
        if (str(found) if found is not None else "") != expected:
            return None
    return updated


def append_list_item(text: str, key: str, item: str) -> str | None:
    """Ajoute « - item » à la liste d'une clé non indentée « key: » d'un texte YAML, sans toucher au reste.

    La ligne (indentée de 4 espaces) est placée après les éléments existants de la clé ; clé absente : « key: » et l'élément
    sont ajoutés à la fin, précédés d'une ligne vide. Le texte obtenu est relu : None si l'élément n'y est pas rattaché à la clé (fichier inattendu).
    """
    lines = text.split("\n")
    start = next((index for index, line in enumerate(lines) if top_level_key(line) == key), None)
    entry = f"    - {yaml_scalar(item)}"
    if start is None:
        position = len(lines) - 1 if lines and lines[-1] == "" else len(lines)
        spacer = [""] if position and lines[position - 1].strip() else []
        lines[position:position] = [*spacer, f"{yaml_scalar(key)}:", entry]
    else:
        end = start + 1
        while end < len(lines) and lines[end][:1] in (" ", "\t"):
            end += 1
        lines.insert(end, entry)
    updated = "\n".join(lines)

    try:
        parsed = yaml.safe_load(updated)
    except yaml.YAMLError:
        return None
    if not isinstance(parsed, dict) or item not in [str(value).strip() for value in parsed.get(key) or []]:
        return None
    return updated


def top_level_key(line: str) -> str | None:
    """Clé d'une ligne « clé: » non indentée (guillemets compris), None pour toute autre ligne."""
    if not line or line[0] in " \t#" or not line.rstrip().endswith(":"):
        return None
    try:
        parsed = yaml.safe_load(line)
    except yaml.YAMLError:
        return None
    if isinstance(parsed, dict) and len(parsed) == 1:
        return str(next(iter(parsed))).strip()
    return None
