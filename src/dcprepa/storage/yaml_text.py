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
