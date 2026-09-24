import socket
import urllib.error
from email.message import Message
from urllib.parse import parse_qs, urlsplit

import pytest

from dcprepa.storage.mtgtop8 import META_IDS, TIMEOUT, USER_AGENT, fetch_meta_page, meta_url

PAGE = '<div class=S14 align=center style="margin:10px;">1442 decks</div>'


class FakeResponse:
    """Réponse HTTP minimale : en-têtes (charset), corps, utilisable avec « with »."""

    def __init__(self, body: bytes, content_type: str = "text/html; charset=ISO-8859-1"):
        self.headers = Message()
        self.headers["Content-Type"] = content_type
        self.body = body

    def read(self):
        return self.body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class FakeOpener:
    """Remplace urllib.request.urlopen : garde la requête reçue, renvoie une réponse ou lève une erreur."""

    def __init__(self, result):
        self.result = result
        self.request = None
        self.timeout = None

    def __call__(self, request, timeout):
        self.request, self.timeout = request, timeout
        if isinstance(self.result, BaseException):
            raise self.result
        return self.result


def test_meta_ids():
    assert META_IDS == {"general": "121", "paper": "308"}


def test_meta_url():
    parts = urlsplit(meta_url("308"))
    assert (parts.scheme, parts.netloc, parts.path) == ("https", "www.mtgtop8.com", "/cEDH_decks")
    query = parse_qs(parts.query, keep_blank_values=True)
    assert query == {
        "f": ["EDH"], "show": ["pop"], "cid": [""], "meta": ["308"], "gamerid1": [""], "gamerid2": [""], "cEDH_cp": ["1"],
    }


def test_telechargement():
    opener = FakeOpener(FakeResponse(PAGE.encode("latin-1")))
    assert fetch_meta_page("121", opener=opener) == (PAGE, [])
    assert opener.request.full_url == meta_url("121")
    assert opener.request.get_header("User-agent") == USER_AGENT
    assert opener.timeout == TIMEOUT


@pytest.mark.parametrize(
    "body, content_type, expected",
    [
        ("Kíli".encode("latin-1"), "text/html; charset=ISO-8859-1", "Kíli"),
        ("Kíli".encode("utf-8"), "text/html; charset=utf-8", "Kíli"),
        ("Kíli".encode("utf-8"), "text/html", "Kíli"),  # pas de charset : utf-8
        ("Kíli".encode("utf-8"), "text/html; charset=inconnu", "Kíli"),  # charset inconnu : utf-8
    ],
)
def test_encodage(body, content_type, expected):
    assert fetch_meta_page("121", opener=FakeOpener(FakeResponse(body, content_type))) == (expected, [])


def test_page_vide():
    html, errors = fetch_meta_page("121", opener=FakeOpener(FakeResponse(b"  \n")))
    assert html == ""
    assert errors == [f"MTGTop8 : page vide pour {meta_url('121')}"]


def test_erreur_http():
    error = urllib.error.HTTPError(meta_url("121"), 503, "Service Unavailable", Message(), None)
    assert fetch_meta_page("121", opener=FakeOpener(error)) == ("", [f"MTGTop8 : réponse HTTP 503 pour {meta_url('121')}"])


def test_site_injoignable():
    error = urllib.error.URLError(socket.gaierror(-3, "Temporary failure in name resolution"))
    html, errors = fetch_meta_page("121", opener=FakeOpener(error))
    assert html == ""
    assert len(errors) == 1
    assert errors[0].startswith("MTGTop8 injoignable (")
    assert errors[0].endswith(") : vérifier la connexion internet")


@pytest.mark.parametrize("error", [TimeoutError("timed out"), urllib.error.URLError(TimeoutError("timed out"))])
def test_delai_depasse(error):
    assert fetch_meta_page("121", opener=FakeOpener(error), timeout=5) == ("", ["MTGTop8 ne répond pas (délai de 5 s dépassé)"])
