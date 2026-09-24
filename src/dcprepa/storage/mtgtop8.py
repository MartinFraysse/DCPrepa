import socket
import urllib.error
import urllib.parse
import urllib.request

BASE_URL = "https://www.mtgtop8.com/cEDH_decks"
FORMAT = "EDH"  # Duel Commander chez MTGTop8
META_IDS = {"general": "121", "paper": "308"}  # Last 2 Months, Paper Last 2 Months
USER_AGENT = "DCPrepa (préparation de tournois Duel Commander ; une requête par import)"
TIMEOUT = 20


def meta_url(meta_id: str) -> str:
    """URL du fragment qui liste les archétypes d'une période, ex. meta_id « 121 » (2 derniers mois).

    C'est le fragment que la page https://www.mtgtop8.com/format?f=EDH charge en JavaScript :
    lisible sans navigateur, une seule page (pas de pagination).
    """
    query = urllib.parse.urlencode(
        {"f": FORMAT, "show": "pop", "cid": "", "meta": meta_id, "gamerid1": "", "gamerid2": "", "cEDH_cp": "1"}
    )
    return f"{BASE_URL}?{query}"


def fetch_meta_page(meta_id: str, opener=urllib.request.urlopen, timeout: float = TIMEOUT) -> tuple[str, list[str]]:
    """Télécharge la répartition du méta d'une période : seul accès au réseau du logiciel.

    opener : fonction d'ouverture d'URL (urllib.request.urlopen par défaut), remplaçable dans les tests.
    Renvoie (html, errors), jamais les deux remplis : site injoignable, délai dépassé, réponse HTTP
    en erreur ou page vide donnent un message clair, sans lever d'exception.
    """
    url = meta_url(meta_id)
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with opener(request, timeout=timeout) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            body = response.read()
    except urllib.error.HTTPError as error:
        return "", [f"MTGTop8 : réponse HTTP {error.code} pour {url}"]
    except urllib.error.URLError as error:
        if isinstance(error.reason, (TimeoutError, socket.timeout)):
            return "", [f"MTGTop8 ne répond pas (délai de {timeout:g} s dépassé)"]
        return "", [f"MTGTop8 injoignable ({error.reason}) : vérifier la connexion internet"]
    except (TimeoutError, socket.timeout):
        return "", [f"MTGTop8 ne répond pas (délai de {timeout:g} s dépassé)"]

    try:
        html = body.decode(charset, errors="replace")
    except LookupError:
        html = body.decode("utf-8", errors="replace")
    if not html.strip():
        return "", [f"MTGTop8 : page vide pour {url}"]
    return html, []
