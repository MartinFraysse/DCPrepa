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


SHEET_FIELDS = ("name", "commandant", "statut")


def load_deck_sheets(tournament_dir: Path) -> tuple[dict[str, dict], list[str]]:
    """Lit les fiches deck complètes d'un tournoi, pour les rapports de stats.

    Versions et erreurs viennent de load_decks (mêmes règles que l'import) ; s'y ajoutent
    les champs name, commandant et statut, en texte ("" si absent ou vide).

    Renvoie (sheets, errors), ex. ({"terra-midrange": {"name": "Terra Midrange", "commandant": "Terra, Magical Adept",
    "statut": "envisage", "versions": ["v1", "v2"]}}, []). Versions de la plus ancienne à la plus récente.
    """
    decks, errors = load_decks(tournament_dir)

    sheets = {}
    for deck, versions in decks.items():
        content = yaml.safe_load((tournament_dir / "decks" / f"{deck}.yaml").read_text(encoding="utf-8"))
        sheet = {}
        for field in SHEET_FIELDS:
            value = content.get(field)
            sheet[field] = str(value).strip() if value is not None else ""
        sheet["versions"] = versions
        sheets[deck] = sheet
    return sheets, errors


ALIAS_FILE = "_alias.yaml"


def load_deck_aliases(tournament_dir: Path, decks: dict[str, list[str]]) -> tuple[dict[str, list[str]], list[str]]:
    """Rassemble les appellations acceptées de chaque deck chargé par load_decks.

    Pour chaque deck : le nom de son fichier, le champ « name » de sa fiche, et ses variantes
    dans decks/_alias.yaml (facultatif, même format que data/oppos.yaml : nom du fichier → liste).

    Renvoie (aliases, errors), jamais les deux remplis,
    ex. ({"terra-5c": ["terra-5c", "Terra 5C", "Terra", "Terra mid"]}, []).
    """
    decks_dir = tournament_dir / "decks"
    aliases = {}
    for deck in decks:
        aliases[deck] = [deck]
        content = yaml.safe_load((decks_dir / f"{deck}.yaml").read_text(encoding="utf-8"))
        name = content.get("name") if isinstance(content, dict) else None
        if name is not None and str(name).strip():
            aliases[deck].append(str(name).strip())

    alias_path = decks_dir / ALIAS_FILE
    if not alias_path.is_file():
        return aliases, []

    try:
        content = yaml.safe_load(alias_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as error:
        return {}, [f"{ALIAS_FILE} : YAML illisible : {error}"]
    if content is None:
        return aliases, []
    if not isinstance(content, dict):
        return {}, [f"{ALIAS_FILE} : attendu « nom-du-fichier-deck: » suivi de ses variantes"]

    errors = []
    available = ", ".join(sorted(decks)) or "aucun"
    for deck, variants in content.items():
        deck = str(deck).strip()
        if deck not in aliases:
            errors.append(f"{ALIAS_FILE} : deck inconnu : {deck} (decks disponibles : {available})")
            continue
        if variants is None:
            continue
        if not isinstance(variants, list):
            errors.append(f"{ALIAS_FILE} : {deck} : variantes attendues sous forme de liste (« - variante »)")
            continue
        aliases[deck] += [str(variant).strip() for variant in variants if variant is not None]

    if errors:
        return {}, errors
    return aliases, errors


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
