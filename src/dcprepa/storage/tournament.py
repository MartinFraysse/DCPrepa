from pathlib import Path

import yaml

TOURNAMENT_FILE = "tournament.yaml"


def load_tournament_name(tournament_dir: Path) -> tuple[str, list[str]]:
    """Nom affiché du tournoi : champ « name » de tournament.yaml, sinon le nom du dossier.

    Fichier absent ou sans nom : nom du dossier, sans avertissement ; fichier illisible : nom du dossier et un avertissement.
    Renvoie (name, warnings), ex. ("RelicFest 2026", []).
    """
    path = tournament_dir / TOURNAMENT_FILE
    if not path.is_file():
        return tournament_dir.name, []
    try:
        content = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError:
        return tournament_dir.name, [f"{TOURNAMENT_FILE} : YAML illisible → nom du dossier utilisé ({tournament_dir.name})"]
    name = content.get("name") if isinstance(content, dict) else None
    return (str(name).strip() if name is not None and str(name).strip() else tournament_dir.name), []
