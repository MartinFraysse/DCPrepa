POSITIONS = {"OTP", "OTD"}
RESULTS = {"W", "L"}
MAX_GAMES_PER_BO = 3

def _parse_bo(text: str) -> tuple[list[list[str]], list[str]]:
    if not text.strip():
        return [], ["BO vide"]
    text = text.upper().split(",")
    game_result = []
    if len(text) > 3:
        return [], [f"plus de 3 games dans un BO : {text}"]
    error = []
    score = [0, 0]
    for i in text:
        i = i.split()
        if not i:
            error.append(f"game vide (virgule en trop ?) : {text}")
            continue
        if len(i) != 2:
            error.append(f"game mal formée (attendu : OTP W) : {i}")
            continue
        if i[0] not in POSITIONS:
            error.append(f"position inconnue (OTP ou OTD) : {i[0]}")
        if i[1] not in RESULTS:
            error.append(f"résultat inconnu (W ou L) : {i[1]}")
            continue
        if score[0] == 2 or score[1] == 2:
            error.append(f"BO déjà terminé ({score[0]}-{score[1]}) : game en trop")
            continue
        if i[1] == "W":
            score[0] += 1
        else:
            score[1] += 1
        game_result.append(i)

    if error:
        return [], error
    return game_result, error