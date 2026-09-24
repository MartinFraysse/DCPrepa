from pathlib import Path

import yaml

from dcprepa.storage.yaml_text import append_list_item, set_fields, top_level_key, yaml_scalar


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
            if (decks_dir / f"{deck}.yaml").is_file():
                continue  # fiche présente mais en erreur : load_decks la signale déjà
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


def version_lines(version: str, cards_in: list[str], cards_out: list[str], card_list: list[str], notes: str) -> list[str]:
    """Lignes YAML d'une version, au format des fiches : « -   version: » puis in, out, liste (bloc « | »), notes."""
    lines = [f"    -   version: {yaml_scalar(version)}"]
    for key, cards in (("in", cards_in), ("out", cards_out)):
        if cards:
            lines.append(f"        {key}:")
            lines += [f"            - {yaml_scalar(card)}" for card in cards]
    if card_list:
        lines.append("        liste: |")
        lines += [f"                {line}" for line in card_list]
    lines.append(f"        notes: {yaml_scalar(notes)}" if notes else "        notes:")
    return lines


def create_deck_file(path: Path, header: str, fields: dict[str, str], card_list: list[str], notes: str) -> list[str]:
    """Écrit une nouvelle fiche deck : commentaire d'en-tête, name, commandant, statut, puis la version v1.

    Le texte est relu avant l'écriture (fiche lisible par load_decks avec la seule version v1) ; fichier déjà présent : erreur.
    Écriture via un fichier .tmp renommé. Renvoie les erreurs ; rien n'est écrit en cas d'erreur.
    """
    if path.exists():
        return [f"fiche déjà existante : {path.name}"]
    lines = [f"# {header}", ""]
    lines += [f"{field}: {yaml_scalar(value)}" if value else f"{field}:" for field, value in fields.items()]
    lines += ["versions:", *version_lines("v1", [], [], card_list, notes), ""]
    text = "\n".join(lines)
    if not _readable_versions(text, ["v1"]):
        return [f"{path.name} : fiche générée illisible (valeurs à vérifier)"]
    _write(path, text)
    return []


def append_version(path: Path, lines: list[str], version: str) -> list[str]:
    """Ajoute une version (version_lines) à la fin de la liste « versions » d'une fiche, sans toucher au reste.

    Placée après la dernière ligne non commentée du bloc (un exemple commenté en fin de fichier reste en dessous),
    précédée d'une ligne vide. Le texte est relu : versions = anciennes + la nouvelle, autres champs inchangés.
    """
    content = path.read_text(encoding="utf-8")
    rows = content.split("\n")
    start = next((index for index, line in enumerate(rows) if top_level_key(line) == "versions"), None)
    if start is None:
        return [f"{path.name} : champ « versions » introuvable"]
    end = start + 1
    last = start
    while end < len(rows) and (not rows[end].strip() or rows[end][:1] in (" ", "\t")):
        if rows[end].strip() and not rows[end].lstrip().startswith("#"):
            last = end
        end += 1
    updated = "\n".join(rows[: last + 1] + ["", *lines] + rows[last + 1:])

    before = _parse(content)
    old_versions, _ = _versions_of(before)
    after = _parse(updated)
    if after is None or _versions_of(after)[0] != old_versions + [version] or _without_versions(after) != _without_versions(before):
        return [f"{path.name} : impossible d'ajouter la version {version} (fiche à vérifier à la main)"]
    _write(path, updated)
    return []


def update_deck_fields(path: Path, fields: dict[str, str]) -> list[str]:
    """Modifie des champs d'une fiche (statut, name, commandant) en gardant le reste, commentaires compris (set_fields)."""
    updated = set_fields(path.read_text(encoding="utf-8"), fields)
    if updated is None:
        return [f"{path.name} : impossible d'écrire {', '.join(fields)} (fiche à vérifier à la main)"]
    _write(path, updated)
    return []


def add_alias(decks_dir: Path, deck: str, alias: str) -> list[str]:
    """Ajoute une appellation d'un deck dans decks/_alias.yaml (créé s'il manque), sous le nom du fichier du deck."""
    path = decks_dir / ALIAS_FILE
    content = path.read_text(encoding="utf-8") if path.is_file() else "# Appellations acceptées pour chaque deck de ce tournoi.\n"
    updated = append_list_item(content, deck, alias)
    if updated is None:
        return [f"{ALIAS_FILE} : impossible d'ajouter {alias} sous {deck} (fichier à vérifier à la main)"]
    _write(path, updated)
    return []


def _parse(text: str):
    try:
        return yaml.safe_load(text)
    except yaml.YAMLError:
        return None


def _versions_of(content) -> tuple[list[str], list]:
    entries = content.get("versions") if isinstance(content, dict) else None
    entries = entries if isinstance(entries, list) else []
    return [str(entry.get("version")).strip() for entry in entries if isinstance(entry, dict)], entries


def _without_versions(content) -> dict:
    return {key: value for key, value in content.items() if key != "versions"} if isinstance(content, dict) else {}


def _readable_versions(text: str, expected: list[str]) -> bool:
    return _versions_of(_parse(text))[0] == expected


def _write(path: Path, text: str) -> None:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)
