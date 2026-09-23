from pathlib import Path

import yaml


def load_decks(tournament_dir: Path) -> tuple[dict[str, list[str]], list[str]]:
    """Lit les fiches deck d'un tournoi (decks/*.yaml) et renvoie leurs versions.

    Nom du deck = nom du fichier sans extension ; les fichiers commençant par « _ » (modèles) sont ignorés.
    Une fiche illisible ou sans version valide est écartée et signalée, les autres sont chargées.

    Renvoie (decks, errors), ex. ({"terra-midrange": ["v1", "v2"]}, []).
    """
    decks_dir = tournament_dir / "decks"
    if not decks_dir.is_dir():
        return {}, [f"dossier introuvable : {decks_dir}"]

    decks = {}
    errors = []
    for path in sorted(decks_dir.glob("*.yaml")):
        if path.name.startswith("_"):
            continue
        versions, file_errors = _read_versions(path)
        if file_errors:
            for message in file_errors:
                errors.append(f"{path.name} : {message}")
            continue
        decks[path.stem] = versions
    return decks, errors


def _read_versions(path: Path) -> tuple[list[str], list[str]]:
    """Lit une fiche deck et renvoie (identifiants de version, erreurs)."""
    try:
        content = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as error:
        return [], [f"YAML illisible : {error}"]

    entries = content.get("versions") if isinstance(content, dict) else None
    if not isinstance(entries, list) or not entries:
        return [], ["aucune version (champ « versions » manquant ou vide)"]

    versions = []
    errors = []
    for number, entry in enumerate(entries, start=1):
        value = entry.get("version") if isinstance(entry, dict) else None
        if value is None or not str(value).strip():
            errors.append(f"version n°{number} sans identifiant (champ « version »)")
            continue
        version = str(value).strip()
        if version in versions:
            errors.append(f"version en double : {version}")
            continue
        versions.append(version)

    if errors:
        return [], errors
    return versions, errors
