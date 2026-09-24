from dcprepa.domain.names import name_key
from dcprepa.domain.oppos import SELF_PLAY_MARK


def resolve_deck(name: str, index: dict[str, str]) -> str | None:
    """Ramène un nom de deck saisi (fichier, name: ou variante de _alias.yaml) au nom de son fichier.

    Renvoie None si le nom n'est pas reconnu.
    """
    return index.get(name_key(name))


def resolve_self_play(oppo: str, index: dict[str, str]) -> tuple[str, str | None]:
    """Reconnaît le deck d'un oppo self-play « deck@version », ex. « terra mid@v1 » → « terra-5c@v1 ».

    Deck reconnu : (« fichier@version », None) ; sinon l'oppo est gardé tel quel avec un avertissement.
    """
    deck, _, version = " ".join(str(oppo).split()).partition(SELF_PLAY_MARK)
    version = version.strip()
    resolved = resolve_deck(deck, index)
    if resolved is None:
        return f"{deck.strip()}{SELF_PLAY_MARK}{version}", f"self-play : deck inconnu : {deck.strip()}"
    return f"{resolved}{SELF_PLAY_MARK}{version}", None
