from dataclasses import dataclass

from dcprepa.domain.decks import resolve_deck, resolve_self_play
from dcprepa.domain.games import parse_bos
from dcprepa.domain.oppos import SELF_PLAY_MARK, normalize_oppo
from dcprepa.domain.rows import build_rows
from dcprepa.domain.validation import validate_block


@dataclass(frozen=True)
class PreparedBlock:
    """Un bloc de games prêt à écrire : ses lignes de games.csv et son nombre de BO, ou ses erreurs (rows vide)."""

    rows: list[dict[str, str]]
    matches: int
    errors: list[str]
    warnings: list[str]


def prepare_block(
    block, decks: dict[str, list[str]], deck_index: dict[str, str], oppo_index: dict[str, str], used_ids: set[str]
) -> PreparedBlock:
    """Vérifie un bloc (inbox ou formulaire de saisie) et le transforme en lignes de games.csv.

    1. le deck saisi est ramené au nom de son fichier (nom du fichier, name: ou variante de decks/_alias.yaml) ;
    2. validate_block : champs, date, source, deck, version, games ; une erreur → aucune ligne ;
    3. oppo normalisé (data/oppos.yaml), ou deck d'un self-play « deck@version » ramené au nom de son fichier ;
       un oppo inconnu est un avertissement, pas une erreur ;
    4. build_rows : une ligne par game, un match_id par BO.

    decks : load_decks ; deck_index / oppo_index : index des appellations ; used_ids : match_id déjà pris,
    complété avec ceux attribués (les blocs suivants continuent la numérotation).
    """
    if isinstance(block, dict) and block.get("deck") is not None:
        deck = resolve_deck(block["deck"], deck_index)
        if deck is not None:
            block = {**block, "deck": deck}
    errors = validate_block(block, decks)
    if errors:
        return PreparedBlock([], 0, errors, [])

    if SELF_PLAY_MARK in str(block["oppo"]):
        oppo, warning = resolve_self_play(block["oppo"], deck_index)
    else:
        oppo, warning = normalize_oppo(block["oppo"], oppo_index)
    bos, _ = parse_bos(str(block["games"]))
    return PreparedBlock(build_rows(block, bos, oppo, used_ids), len(bos), [], [warning] if warning else [])
