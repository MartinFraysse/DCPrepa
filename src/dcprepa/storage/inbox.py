from pathlib import Path

import yaml

SEPARATOR = "---"


def read_inbox(path: Path) -> tuple[list, list[str]]:
    """Lit inbox.yaml et renvoie ses blocs, lus un par un.

    Les blocs sont séparés par une ligne « --- » ; les parties sans contenu (en-tête commenté,
    lignes vides, « --- » en trop) sont ignorées. Chaque bloc est lu séparément : un bloc
    illisible n'empêche pas de signaler les erreurs des suivants.

    Renvoie (blocks, errors), jamais les deux remplis :
    - tout est lisible : ([bloc 1, bloc 2, ...], []), chaque bloc tel que lu par YAML
      (en principe un dictionnaire ; sa validation se fait dans domain/validation.py) ;
    - sinon : ([], ["bloc 2 : YAML illisible ligne 40 : ...", ...]).
    """
    if not path.is_file():
        return [], [f"fichier introuvable : {path}"]

    blocks = []
    errors = []
    chunks = _split_blocks(path.read_text(encoding="utf-8"))
    for number, (start_line, text) in enumerate(chunks, start=1):
        try:
            blocks.append(yaml.safe_load(text))
        except yaml.YAMLError as error:
            errors.append(f"bloc {number} : YAML illisible {_describe(error, start_line)}")

    if errors:
        return [], errors
    return blocks, errors


def clear_inbox(path: Path) -> None:
    """Vide inbox.yaml en ne gardant que son en-tête (lignes vides et commentaires du début).

    À appeler seulement après un import réussi. L'écriture passe par un fichier temporaire
    remplacé d'un coup : en cas de coupure, l'inbox reste soit intacte, soit vidée, jamais à moitié.
    Les fins de ligne du fichier (LF ou CRLF) sont conservées.
    """
    with path.open(encoding="utf-8", newline="") as file:
        lines = file.readlines()

    header = []
    for line in lines:
        if _has_content(line) or line.strip() == SEPARATOR:
            break
        header.append(line)

    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as file:
        file.writelines(header)
    temporary.replace(path)


def _split_blocks(text: str) -> list[tuple[int, str]]:
    """Découpe le texte sur les lignes « --- ».

    Renvoie, pour chaque bloc qui contient au moins une ligne utile (ni vide ni commentaire),
    le numéro dans le fichier de sa première ligne et son texte.
    """
    blocks = []
    lines = []
    start_line = 1
    for number, line in enumerate(text.splitlines(), start=1):
        if line.strip() == SEPARATOR:
            if any(_has_content(kept) for kept in lines):
                blocks.append((start_line, "\n".join(lines)))
            lines = []
            start_line = number + 1
            continue
        lines.append(line)
    if any(_has_content(kept) for kept in lines):
        blocks.append((start_line, "\n".join(lines)))
    return blocks


def _has_content(line: str) -> bool:
    """Vrai si la ligne n'est ni vide ni un commentaire."""
    stripped = line.strip()
    return bool(stripped) and not stripped.startswith("#")


def _describe(error: yaml.YAMLError, start_line: int) -> str:
    """Localise et résume une erreur YAML : « ligne 40 : <problème> »."""
    mark = getattr(error, "problem_mark", None)
    problem = getattr(error, "problem", None) or str(error).splitlines()[0]
    if mark is None:
        return f": {problem}"
    return f"ligne {start_line + mark.line} : {problem}"
