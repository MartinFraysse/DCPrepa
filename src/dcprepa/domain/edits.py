from dataclasses import dataclass, field

from dcprepa.domain.blocks import prepare_block
from dcprepa.domain.rows import normalize_date

NOTE = "note/ressenti"
MATCH_FIELDS = ("date", "source", "deck", "version", "oppo")
GAME_FIELDS = ("position", "resultat", NOTE)


@dataclass(frozen=True)
class EditResult:
    """Games de games.csv après une correction (toutes, dans l'ordre du fichier), ou les erreurs (games vide).

    match_id : le BO corrigé après la correction (nouveau si sa date a changé, None s'il a été supprimé) ;
    changed : nombre de games du BO après la correction.
    """

    games: list[dict[str, str]]
    match_id: str | None = None
    changed: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class References:
    """Decks et versions, appellations des decks et des oppos : ce qu'il faut pour revérifier un BO (voir prepare_block)."""

    decks: dict[str, list[str]]
    deck_index: dict[str, str]
    oppo_index: dict[str, str]


def edit_game(games: list[dict[str, str]], match_id: str, number: str, changes: dict[str, str], refs: References) -> EditResult:
    """Corrige une game d'un BO : position, résultat et / ou note (ex. {"resultat": "W"}).

    Le BO entier est revérifié comme à l'import ; les autres games et les autres BO ne changent pas.
    """
    errors = _unknown_fields(changes, GAME_FIELDS)
    rows, found = _match(games, match_id)
    errors += found
    if not errors and not any(row["game"] == str(number) for row in rows):
        errors.append(f"game inconnue : {match_id} game {number} (le BO a {len(rows)} game(s))")
    if errors:
        return EditResult([], errors=errors)

    edited = [{**row, **changes} if row["game"] == str(number) else row for row in rows]
    return _rebuild(games, match_id, edited, {}, refs)


def edit_match(games: list[dict[str, str]], match_id: str, changes: dict[str, str], refs: References) -> EditResult:
    """Corrige un BO entier : date, source, deck, version et / ou oppo, appliqués à toutes ses games.

    Mêmes contrôles que l'import ; date changée → nouveau match_id (prochain numéro libre de la nouvelle date).
    """
    errors = _unknown_fields(changes, MATCH_FIELDS)
    rows, found = _match(games, match_id)
    errors += found
    if errors:
        return EditResult([], errors=errors)
    return _rebuild(games, match_id, rows, changes, refs)


def delete_game(games: list[dict[str, str]], match_id: str, number: str) -> EditResult:
    """Supprime une game d'un BO ; les games suivantes sont renumérotées (3 → 2).

    Un BO réduit à une seule game devient un BO1 (avertissement) ; sa dernière game supprimée, le BO disparaît.
    """
    rows, errors = _match(games, match_id)
    if not errors and not any(row["game"] == str(number) for row in rows):
        errors.append(f"game inconnue : {match_id} game {number} (le BO a {len(rows)} game(s))")
    if errors:
        return EditResult([], errors=errors)

    kept = [row for row in rows if row["game"] != str(number)]
    renumbered = [{**row, "game": str(index)} for index, row in enumerate(kept, start=1)]
    warnings = []
    if len(rows) >= 2 and len(renumbered) == 1:
        warnings.append(f"{match_id} : une seule game restante, le BO devient un BO1 (hors winrate BO3)")
    return EditResult(
        _replace(games, match_id, renumbered), match_id if renumbered else None, len(renumbered), [], warnings
    )


def delete_match(games: list[dict[str, str]], match_id: str) -> EditResult:
    """Supprime toutes les games d'un BO."""
    _, errors = _match(games, match_id)
    if errors:
        return EditResult([], errors=errors)
    return EditResult(_replace(games, match_id, []))


def _match(games: list[dict[str, str]], match_id: str) -> tuple[list[dict[str, str]], list[str]]:
    """Les games d'un BO, triées par numéro ; erreur si le match_id est inconnu."""
    rows = [game for game in games if game["match_id"] == match_id]
    if not rows:
        return [], [f"BO inconnu : {match_id}"]
    return sorted(rows, key=lambda row: int(row["game"]) if row["game"].isdigit() else 0), []


def _unknown_fields(changes: dict[str, str], allowed: tuple[str, ...]) -> list[str]:
    if not changes:
        return ["rien à modifier"]
    return [f"champ non modifiable ici : {name} (possibles : {', '.join(allowed)})" for name in changes if name not in allowed]


def _rebuild(
    games: list[dict[str, str]], match_id: str, rows: list[dict[str, str]], changes: dict[str, str], refs: References
) -> EditResult:
    """Revérifie un BO comme un bloc de l'inbox (prepare_block) puis le remet à sa place dans games.csv.

    Les notes de chaque game sont gardées ; le match_id aussi, sauf si la date change.
    """
    block = {name: rows[0][name] for name in MATCH_FIELDS} | changes
    block["games"] = ", ".join(f"{row['position']} {row['resultat']}" for row in rows)
    used_ids = {game["match_id"] for game in games} - {match_id}
    prepared = prepare_block(block, refs.decks, refs.deck_index, refs.oppo_index, used_ids)
    if prepared.errors:
        return EditResult([], errors=[message.replace("games : BO 1 : ", f"{match_id} : ") for message in prepared.errors])

    same_date = normalize_date(block["date"]) == normalize_date(rows[0]["date"])
    new_id = match_id if same_date else prepared.rows[0]["match_id"]
    rebuilt = [
        {**new, "match_id": new_id, NOTE: " ".join(str(old[NOTE]).split())}
        for new, old in zip(prepared.rows, rows)
    ]
    return EditResult(_replace(games, match_id, rebuilt), new_id, len(rebuilt), [], prepared.warnings)


def _replace(games: list[dict[str, str]], match_id: str, rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """games.csv avec les games du BO remplacées par rows, à la place de sa première game (ordre du fichier gardé)."""
    first = next(index for index, game in enumerate(games) if game["match_id"] == match_id)
    others = [game for game in games if game["match_id"] != match_id]
    return others[:first] + rows + others[first:]
