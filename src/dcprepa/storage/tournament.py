import shutil
from pathlib import Path

import yaml

from dcprepa.storage.yaml_text import set_fields

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


TEMPLATE_REMOVED = ("README.md", "stats/_modele-deck.md")
STATS_README_LINE = "- `_modele-deck.md`"


def create_tournament_dir(template_dir: Path, target_dir: Path, fields: dict[str, str]) -> list[str]:
    """Crée un dossier de tournoi à partir du modèle, en tout ou rien.

    Copie template_dir dans un dossier temporaire, retire README.md et stats/_modele-deck.md (et sa ligne dans stats/README.md),
    remplit tournament.yaml (set_fields, commentaires gardés), puis renomme le dossier en target_dir.
    Renvoie les erreurs (dossier déjà présent, tournament.yaml du modèle inattendu) ; rien n'est créé en cas d'erreur.
    """
    if target_dir.exists():
        return [f"dossier déjà existant : {target_dir}"]
    yaml_path = template_dir / TOURNAMENT_FILE
    updated = set_fields(yaml_path.read_text(encoding="utf-8"), fields)
    if updated is None:
        return [f"modèle {TOURNAMENT_FILE} inattendu : impossible d'y écrire {', '.join(fields)}"]

    temporary = target_dir.with_name(target_dir.name + ".tmp")
    if temporary.exists():
        shutil.rmtree(temporary)
    try:
        shutil.copytree(template_dir, temporary)
        for relative in TEMPLATE_REMOVED:
            (temporary / relative).unlink(missing_ok=True)
        readme = temporary / "stats" / "README.md"
        if readme.is_file():
            lines = readme.read_text(encoding="utf-8").split("\n")
            readme.write_text("\n".join(line for line in lines if not line.startswith(STATS_README_LINE)), encoding="utf-8")
        (temporary / TOURNAMENT_FILE).write_text(updated, encoding="utf-8")
        temporary.rename(target_dir)
    except BaseException:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    return []


def update_tournament_file(tournament_dir: Path, fields: dict[str, str]) -> list[str]:
    """Modifie des champs de tournament.yaml (set_fields, commentaires gardés), écriture via un fichier .tmp.

    Renvoie les erreurs (fichier absent ou inattendu) ; rien n'est écrit en cas d'erreur.
    """
    path = tournament_dir / TOURNAMENT_FILE
    if not path.is_file():
        return [f"fichier introuvable : {path}"]
    updated = set_fields(path.read_text(encoding="utf-8"), fields)
    if updated is None:
        return [f"{TOURNAMENT_FILE} inattendu : impossible d'y écrire {', '.join(fields)}"]
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(updated, encoding="utf-8")
    temporary.replace(path)
    return []


SHEET_FIELDS = ("name", "slug", "format", "date", "location", "banlist", "notes")


def load_tournament_sheet(tournament_dir: Path) -> tuple[dict[str, str], list[str]]:
    """Fiche du tournoi (tournament.yaml), champs en texte (« » si absent ou vide) ; name vaut le nom du dossier s'il est vide.

    Fichier absent : fiche vide avec le nom du dossier, sans erreur ; YAML illisible ou inattendu : même fiche et une erreur.
    """
    sheet = {field: "" for field in SHEET_FIELDS}
    sheet["name"] = tournament_dir.name
    path = tournament_dir / TOURNAMENT_FILE
    if not path.is_file():
        return sheet, []
    try:
        content = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError:
        return sheet, [f"{TOURNAMENT_FILE} : YAML illisible"]
    if content is None:
        return sheet, []
    if not isinstance(content, dict):
        return sheet, [f"{TOURNAMENT_FILE} : attendu une ligne « champ: valeur » par champ"]
    for field in SHEET_FIELDS:
        value = content.get(field)
        if value is not None and str(value).strip():
            sheet[field] = " ".join(str(value).split())
    return sheet, []
