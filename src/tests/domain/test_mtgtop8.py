from pathlib import Path

import pytest

from dcprepa.domain.mtgtop8 import MetaPage, parse_meta_page

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def row(name, permille, archetype=1):
    """Une ligne d'archétype, écrite comme MTGTop8 (attributs sans guillemets, ‰ en entité)."""
    return (
        '<div style="width:90%;" class=hover_tr>\n'
        f'  <div align=center style="width:60%;" class=S14><a href=archetype?a={archetype}&meta=121&f=EDH&color_id=&show=pop>{name}</a></div>\n'
        '  <div style="width:20%;" align=center><img src=/graph/manas/W.png></div>\n'
        f'  <div style="width:20%;" class=S14 align=center>{permille} <span class=O14>&permil;</span></div>\n'
        "</div>\n"
    )


def page(total, *rows):
    return f'<div class=S14 align=center style="margin:10px;">{total} decks</div>\n<div align=center>\n' + "".join(rows) + "</div>"


@pytest.mark.parametrize(
    "fixture, total, count, first",
    [
        ("mtgtop8_general.html", 1447, 159, ("Phelia, Exuberant Shepherd", 58.1)),
        ("mtgtop8_paper.html", 1309, 152, ("Cloud, Midgar Mercenary", 60.4)),
    ],
)
def test_vraies_pages(fixture, total, count, first):
    meta, errors = parse_meta_page((FIXTURES / fixture).read_text(encoding="utf-8"))
    assert errors == []
    assert meta.total == total
    assert len(meta.entries) == count
    assert meta.entries[0] == first
    assert abs(sum(permille for _, permille in meta.entries) - 1000) < 5
    names = [name for name, _ in meta.entries]
    assert "Brigid, Clachan's Heart" in names  # « &#039; » décodé
    assert any(name.startswith("Partner ") for name in names)  # partenaires regroupés par couleurs
    assert all(name == " ".join(name.split()) and "&" not in name.replace(" & ", "") for name in names)


def test_lecture_simple():
    text = page(200, row("Ragavan, Nimble Pilferer", "600.0"), row("Kess, Dissident Mage", "400"))
    assert parse_meta_page(text) == (
        MetaPage(200, [("Ragavan, Nimble Pilferer", 600.0), ("Kess, Dissident Mage", 400.0)]),
        [],
    )


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("Brigid, Clachan&#039;s Heart", "Brigid, Clachan's Heart"),
        ("K&iacute;li the Resourceful", "Kíli the Resourceful"),
        ("Raph &amp; Mikey, Troublemakers", "Raph & Mikey, Troublemakers"),
        ("  <b>Tifa</b>   Lockhart ", "Tifa Lockhart"),
    ],
)
def test_noms_decodes(raw, expected):
    meta, errors = parse_meta_page(page(10, row(raw, "1000")))
    assert errors == []
    assert meta.entries == [(expected, 1000.0)]


def test_page_rendue_par_le_navigateur():
    """Même contenu avec guillemets et « ‰ » en clair : lu pareil."""
    text = (
        '<div class="S14" align="center" style="margin:10px;">317 decks</div>'
        '<div style="width:90%;" class="hover_tr"><a href="archetype?a=2629&amp;meta=115">Cloud, Midgar Mercenary</a>'
        '<div class="S14" align="center">1000 <span class="O14">‰</span></div></div>'
    )
    assert parse_meta_page(text) == (MetaPage(317, [("Cloud, Midgar Mercenary", 1000.0)]), [])


def test_somme_tolere_les_arrondis():
    meta, errors = parse_meta_page(page(100, row("A", "501.4"), row("B", "500.0")))
    assert errors == []
    assert meta.entries == [("A", 501.4), ("B", 500.0)]


@pytest.mark.parametrize(
    "text, message",
    [
        ("", "page MTGTop8 inattendue : nombre total de decks introuvable (le site a peut-être changé)"),
        ("<html>Maintenance</html>", "page MTGTop8 inattendue : nombre total de decks introuvable (le site a peut-être changé)"),
        (page(10), "page MTGTop8 inattendue : aucun archétype trouvé (le site a peut-être changé)"),
        (page(10, row("A", "600"), row("B", "100")), "page MTGTop8 inattendue : la somme des parts vaut 700.0 ‰ au lieu d'environ 1000 ‰"),
    ],
)
def test_page_inattendue(text, message):
    assert parse_meta_page(text) == (None, [message])


def test_lignes_incompletes():
    sans_part = row("A", "500").replace("&permil;", "%")
    sans_nom = row("B", "500").replace("archetype?a=", "deck?d=")
    assert parse_meta_page(page(10, sans_part, sans_nom, row("C", "1000"))) == (
        None,
        [
            "page MTGTop8 inattendue : archétype n°1 sans part en ‰",
            "page MTGTop8 inattendue : archétype n°2 sans nom",
        ],
    )
