from pathlib import Path

import pytest

from dcprepa.domain.meta import META_TOP, MetaRow, build_meta, propose_oppos
from dcprepa.domain.mtgtop8 import MetaPage, parse_meta_page
from dcprepa.domain.oppos import build_oppo_index

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


@pytest.fixture
def index():
    index, errors = build_oppo_index(
        {
            "Ragavan": ["Ragavan, Nimble Pilferer", "raga"],
            "Kess": ["Kess, Dissident Mage"],
            "Tymna/Thrasios": ["Partner WUBG", "Tymna Thrasios"],
        }
    )
    assert errors == []
    return index


def test_noms_de_reference(index):
    page = MetaPage(1000, [("Ragavan, Nimble Pilferer", 600.0), ("KESS, Dissident   Mage", 400.0)])
    assert build_meta(page, index) == (
        [MetaRow("Ragavan", 600, 60.0), MetaRow("Kess", 400, 40.0)],
        [],
    )


def test_noms_inconnus_gardes(index):
    page = MetaPage(200, [("Phelia, Exuberant Shepherd", 700.0), ("Ragavan, Nimble Pilferer", 300.0)])
    rows, unknown = build_meta(page, index)
    assert rows == [MetaRow("Phelia, Exuberant Shepherd", 140, 70.0), MetaRow("Ragavan", 60, 30.0)]
    assert unknown == ["Phelia, Exuberant Shepherd"]


def test_fusion_des_archetypes(index):
    """« Partner WUBG » rattaché à Tymna/Thrasios par une variante : les ‰ s'additionnent."""
    page = MetaPage(1000, [("Tymna Thrasios", 150.0), ("Ragavan, Nimble Pilferer", 500.0), ("Partner WUBG", 350.0)])
    rows, unknown = build_meta(page, index)
    assert rows == [MetaRow("Ragavan", 500, 50.0), MetaRow("Tymna/Thrasios", 500, 50.0)]  # égalité : ordre alphabétique
    assert unknown == []


def test_tri_par_poids_puis_nom(index):
    page = MetaPage(100, [("b", 200.0), ("C", 500.0), ("a", 200.0), ("D", 100.0)])
    rows, _ = build_meta(page, index)
    assert [row.oppo for row in rows] == ["C", "a", "b", "D"]


@pytest.mark.parametrize(
    "total, permille, decks",
    [
        (1442, 58.3, 84),  # 84.07
        (1000, 0.5, 1),  # 0.5 → 1 (au-dessus)
        (1000, 0.4, 0),
        (1309, 60.4, 79),  # 79.06
    ],
)
def test_decks_estimes(total, permille, decks):
    rows, _ = build_meta(MetaPage(total, [("X", permille)]), {})
    assert rows[0].decks == decks


@pytest.mark.parametrize("permille, weight", [(58.1, 5.81), (51.9, 5.19), (49.7, 4.97), (0.7, 0.07)])
def test_poids_exact(permille, weight):
    rows, _ = build_meta(MetaPage(1447, [("X", permille)]), {})
    assert rows[0].weight == weight  # pas de bruit de calcul (5.8100000000000005)


def test_poids_fusionnes_a_2_decimales():
    rows, _ = build_meta(MetaPage(1000, [("Partner WUBG", 0.1), ("Tymna Thrasios", 0.2)]), {"partner wubg": "T", "tymna thrasios": "T"})
    assert rows == [MetaRow("T", 0, 0.03)]


def test_orthographes_differentes_sans_oppos_yaml():
    rows, unknown = build_meta(MetaPage(10, [("X", 500.0), ("x", 500.0)]), {})
    assert unknown == ["X", "x"]  # deux orthographes, deux lignes : rien ne les relie sans oppos.yaml
    assert [row.oppo for row in rows] == ["X", "x"]  # même poids, même nom en minuscules : ordre de la page


def test_top_20_poids_reels():
    entries = [(f"Deck {n:02d}", float(50 - n)) for n in range(30)]  # 50 ‰, 49 ‰, … ; somme sans importance ici
    rows, unknown = build_meta(MetaPage(1000, entries), {})
    assert META_TOP == 20
    assert [row.oppo for row in rows] == [f"Deck {n:02d}" for n in range(20)]
    assert rows[0].weight == 5.0  # poids réel dans le méta complet, pas ramené à 100 %
    assert unknown == [row.oppo for row in rows]  # seuls les inconnus gardés


def test_top_apres_fusion(index):
    """La fusion se fait avant la coupe : deux petits archétypes du même oppo peuvent entrer dans le top."""
    page = MetaPage(1000, [("A", 300.0), ("B", 250.0), ("Partner WUBG", 200.0), ("Tymna Thrasios", 200.0), ("C", 50.0)])
    rows, unknown = build_meta(page, index, top=2)
    assert rows == [MetaRow("Tymna/Thrasios", 400, 40.0), MetaRow("A", 300, 30.0)]
    assert unknown == ["A"]


def test_inconnus_hors_top_ignores():
    rows, unknown = build_meta(MetaPage(1000, [("A", 600.0), ("B", 400.0)]), {"a": "A"}, top=1)
    assert (rows, unknown) == ([MetaRow("A", 600, 60.0)], [])


@pytest.mark.parametrize(
    "names, expected",
    [
        (["Phelia, Exuberant Shepherd"], {"Phelia": ["Phelia, Exuberant Shepherd"]}),
        (["Tifa Lockhart", "Partner WUR"], {"Tifa Lockhart": [], "Partner WUR": []}),  # sans virgule
        (["Brigid, Clachan's Heart", "Cloud, Midgar Mercenary"], {"Brigid": ["Brigid, Clachan's Heart"], "Cloud": ["Cloud, Midgar Mercenary"]}),
        (["Kess, Dissident Mage"], {}),  # déjà connu
        (["Kess, Something Else"], {"Kess, Something Else": []}),  # nom court déjà pris dans oppos.yaml
        (["Tymna, A", "Tymna, B"], {"Tymna": ["Tymna, A"], "Tymna, B": []}),  # nom court pris par l'ajout précédent
        (["Raga, X"], {"Raga, X": []}),  # « raga » est une variante de Ragavan
        (["Phelia, E", "PHELIA, E"], {"Phelia": ["Phelia, E"]}),  # même nom à la casse près : une fois
    ],
)
def test_propose_oppos(index, names, expected):
    assert propose_oppos(names, index) == expected


def test_propose_oppos_rend_les_noms_connus(index):
    """Une fois ajoutées, les entrées font reconnaître les noms : l'index étendu n'a plus d'inconnu."""
    names = ["Phelia, Exuberant Shepherd", "Tifa Lockhart", "Partner WUBG"]
    entries = propose_oppos(names, index)
    extended, errors = build_oppo_index({"Ragavan": [], **entries})
    assert errors == []
    rows, unknown = build_meta(MetaPage(100, [("Phelia, Exuberant Shepherd", 600.0), ("Tifa Lockhart", 400.0)]), extended)
    assert unknown == []
    assert [row.oppo for row in rows] == ["Phelia", "Tifa Lockhart"]


@pytest.mark.parametrize("fixture", ["mtgtop8_general.html", "mtgtop8_paper.html"])
def test_vraies_pages(index, fixture):
    page, errors = parse_meta_page((FIXTURES / fixture).read_text(encoding="utf-8"))
    assert errors == []
    full, _ = build_meta(page, index, top=len(page.entries))
    assert sum(row.weight for row in full) == pytest.approx(100, abs=0.5)
    assert sum(row.decks for row in full) == page.total  # les arrondis retombent sur le total
    rows, unknown = build_meta(page, index)
    assert rows == full[:20]
    assert 50 < sum(row.weight for row in rows) < 90  # le top 20 ne fait pas 100 %
    assert "Partner WUBG" not in [row.oppo for row in full]
    assert unknown == [row.oppo for row in rows if row.oppo not in ("Ragavan", "Kess", "Tymna/Thrasios")]
