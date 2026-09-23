POSITIONS = {"OTP", "OTD"}
RESULTS = {"W", "L"}
MAX_GAMES_PER_BO = 3
WINS_TO_END_BO = 2


def _parse_games(text: str) -> tuple[list[list[str]], list[str]]:
    """Analyse les games d'un BO, ex. « OTP W, OTD L, OTP W ».

    Une game = « position résultat » (OTP/OTD + W/L), games séparées par des virgules ;
    majuscules et espaces libres. Un BO compte au plus 3 games et se termine dès 2 victoires.

    Renvoie (games, errors), jamais les deux remplis :
    - tout est valide : ([["OTP", "W"], ["OTD", "L"], ...], []) ;
    - sinon : ([], [tous les messages d'erreur]).
    """
    if not text.strip():
        return [], ["BO vide"]
    chunks = text.upper().split(",")
    if len(chunks) > MAX_GAMES_PER_BO:
        return [], [f"{len(chunks)} games dans un BO ({MAX_GAMES_PER_BO} maximum)"]

    games = []
    errors = []
    wins = 0
    losses = 0
    for number, chunk in enumerate(chunks, start=1):
        parts = chunk.split()
        if not parts:
            errors.append(f"game {number} : vide (virgule en trop ?)")
            continue
        if len(parts) != 2:
            errors.append(f"game {number} : mal formée (attendu : OTP W) : {chunk.strip()}")
            continue
        position, result = parts
        if position not in POSITIONS:
            errors.append(f"game {number} : position inconnue (OTP ou OTD) : {position}")
        if result not in RESULTS:
            errors.append(f"game {number} : résultat inconnu (W ou L) : {result}")
            continue
        if wins == WINS_TO_END_BO or losses == WINS_TO_END_BO:
            errors.append(f"game {number} : en trop, BO déjà terminé ({wins}-{losses})")
            continue
        if result == "W":
            wins += 1
        else:
            losses += 1
        games.append([position, result])

    if errors:
        return [], errors
    return games, errors


def parse_bos(text: str) -> tuple[list[list[list[str]]], list[str]]:
    """Analyse le champ « parties » d'un bloc d'inbox : un ou plusieurs BO séparés par « / ».

    Ex. « OTP W, OTD W / OTD L » = un BO3 gagné 2-0 puis un BO1.
    Chaque BO passe par _parse_games ; ses erreurs sont préfixées par « BO <numéro> : ».

    Renvoie (bos, errors), jamais les deux remplis :
    - tout est valide : ([games du BO 1, games du BO 2, ...], []) ;
    - sinon : ([], [toutes les erreurs de tous les BO]).
    """
    bos = []
    errors = []
    for number, chunk in enumerate(text.split("/"), start=1):
        games, bo_errors = _parse_games(chunk)
        bos.append(games)
        for message in bo_errors:
            errors.append(f"BO {number} : {message}")

    if errors:
        return [], errors
    return bos, errors
