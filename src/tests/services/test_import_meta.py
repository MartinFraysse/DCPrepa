from datetime import date
from pathlib import Path

import pytest

from dcprepa.services.import_meta import import_meta
from dcprepa.storage.meta import load_latest_meta
from dcprepa.storage.mtgtop8 import META_IDS
from dcprepa.storage.oppos import load_oppos

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
TODAY = date(2026, 9, 24)
OPPOS = "# Noms de référence des decks adverses.\n\nRagavan:\n    - raga\n"


class FakeFetch:
    """Remplace le téléchargement : renvoie les pages enregistrées (ou une erreur) et compte les appels."""

    def __init__(self, pages=None):
        self.pages = pages or {
            META_IDS[kind]: ((FIXTURES / f"mtgtop8_{kind}.html").read_text(encoding="utf-8"), []) for kind in META_IDS
        }
        self.calls = []

    def __call__(self, meta_id):
        self.calls.append(meta_id)
        return self.pages[meta_id]


@pytest.fixture
def setup(tmp_path):
    """Un mini-dépôt : data/oppos.yaml et un tournoi avec meta/README.md."""
    tournament = tmp_path / "tournaments" / "test"
    (tournament / "meta").mkdir(parents=True)
    (tournament / "meta" / "README.md").write_text("# meta\n", encoding="utf-8")
    oppos = tmp_path / "oppos.yaml"
    oppos.write_text(OPPOS, encoding="utf-8")
    return tournament, oppos


def test_import(setup):
    tournament, oppos = setup
    fetch = FakeFetch()
    report = import_meta(tournament, oppos, TODAY, fetch)
    assert report.errors == []
    assert fetch.calls == ["121", "308"]
    assert report.folder == "2026-09-24"
    assert report.replaced is False
    assert report.metas == {"general": (20, 1447), "paper": (20, 1309)}
    assert len(report.added_oppos) == 20
    assert report.added_oppos[:3] == ["Phelia", "Cloud", "Brigid"]

    general = (tournament / "meta" / "2026-09-24" / "general.csv").read_text(encoding="utf-8").splitlines()
    assert general[:3] == ["oppo,decks,poids", "Phelia,84,5.81", "Cloud,83,5.74"]
    assert len(general) == 21
    paper = (tournament / "meta" / "2026-09-24" / "paper.csv").read_text(encoding="utf-8").splitlines()
    assert paper[:2] == ["oppo,decks,poids", "Cloud,79,6.04"]


def test_oppos_ajoutes_a_oppos_yaml(setup):
    tournament, oppos = setup
    report = import_meta(tournament, oppos, TODAY, FakeFetch())
    text = oppos.read_text(encoding="utf-8")
    assert text.startswith(OPPOS)  # rien de modifié avant les ajouts
    assert "\n# Ajoutés par l'import du méta du 24/09/2026 (top 20 MTGTop8) : à renommer ou regrouper au besoin.\nPhelia:\n    - Phelia, Exuberant Shepherd\n" in text
    loaded, errors = load_oppos(oppos)
    assert errors == []
    assert list(loaded) == ["Ragavan", *report.added_oppos]


def test_relu_par_les_stats(setup):
    tournament, oppos = setup
    import_meta(tournament, oppos, TODAY, FakeFetch())
    name, metas, errors = load_latest_meta(tournament)
    assert (name, errors) == ("2026-09-24", [])
    assert metas["general"]["Phelia"] == 5.81
    assert metas["paper"]["Cloud"] == 6.04
    assert len(metas["general"]) == len(metas["paper"]) == 20


def test_deuxieme_import_du_jour(setup):
    tournament, oppos = setup
    import_meta(tournament, oppos, TODAY, FakeFetch())
    after_first = oppos.read_text(encoding="utf-8")
    report = import_meta(tournament, oppos, TODAY, FakeFetch())
    assert report.errors == []
    assert report.replaced is True
    assert report.added_oppos == []  # tous connus depuis le premier import
    assert oppos.read_text(encoding="utf-8") == after_first
    assert sorted(p.name for p in (tournament / "meta").iterdir()) == ["2026-09-24", "README.md"]


def test_imports_precedents_gardes(setup):
    tournament, oppos = setup
    import_meta(tournament, oppos, date(2026, 9, 10), FakeFetch())
    old = (tournament / "meta" / "2026-09-10" / "general.csv").read_text(encoding="utf-8")
    report = import_meta(tournament, oppos, TODAY, FakeFetch())
    assert report.replaced is False
    assert (tournament / "meta" / "2026-09-10" / "general.csv").read_text(encoding="utf-8") == old
    assert load_latest_meta(tournament)[0] == "2026-09-24"


def test_noms_de_oppos_yaml_utilises(setup):
    tournament, oppos = setup
    oppos.write_text(OPPOS + "Cloudy:\n    - Cloud, Midgar Mercenary\n", encoding="utf-8")
    report = import_meta(tournament, oppos, TODAY, FakeFetch())
    assert "Cloud" not in report.added_oppos
    general = (tournament / "meta" / "2026-09-24" / "general.csv").read_text(encoding="utf-8")
    assert "\nCloudy,83,5.74\n" in general


def assert_nothing_written(tournament, oppos):
    assert [p.name for p in (tournament / "meta").iterdir()] == ["README.md"]
    assert oppos.read_text(encoding="utf-8") == OPPOS


def test_erreur_reseau(setup):
    tournament, oppos = setup
    fetch = FakeFetch()
    fetch.pages["308"] = ("", ["MTGTop8 ne répond pas (délai de 20 s dépassé)"])
    report = import_meta(tournament, oppos, TODAY, fetch)
    assert report.errors == ["méta papier : MTGTop8 ne répond pas (délai de 20 s dépassé)"]
    assert (report.folder, report.metas, report.added_oppos) == (None, {}, [])
    assert_nothing_written(tournament, oppos)


def test_page_inattendue(setup):
    tournament, oppos = setup
    fetch = FakeFetch()
    fetch.pages["121"] = ("<html>Maintenance</html>", [])
    report = import_meta(tournament, oppos, TODAY, fetch)
    assert report.errors == [
        "méta général : page MTGTop8 inattendue : nombre total de decks introuvable (le site a peut-être changé)"
    ]
    assert_nothing_written(tournament, oppos)


def test_oppos_yaml_invalide(setup):
    tournament, oppos = setup
    oppos.write_text("Ragavan:\n    - raga\nRagavan2:\n    - raga\n", encoding="utf-8")
    fetch = FakeFetch()
    report = import_meta(tournament, oppos, TODAY, fetch)
    assert report.errors == ["oppos.yaml : « raga » renvoie à la fois vers Ragavan et Ragavan2"]
    assert fetch.calls == []  # pas de requête inutile
    assert [p.name for p in (tournament / "meta").iterdir()] == ["README.md"]


def test_oppos_yaml_absent(setup, tmp_path):
    tournament, _ = setup
    report = import_meta(tournament, tmp_path / "absent.yaml", TODAY, FakeFetch())
    assert report.errors == [f"fichier introuvable : {tmp_path / 'absent.yaml'}"]


def test_date_du_jour_par_defaut(setup):
    tournament, oppos = setup
    report = import_meta(tournament, oppos, fetch=FakeFetch())
    assert report.folder == date.today().strftime("%Y-%m-%d")
