import pytest

from dcprepa.storage.tournament import load_tournament_name


@pytest.fixture
def tournament(tmp_path):
    folder = tmp_path / "relicfest-2026"
    folder.mkdir()
    return folder


def test_nom_lu(tournament):
    (tournament / "tournament.yaml").write_text("name: RelicFest 2026  \nslug: relicfest-2026\n", encoding="utf-8")
    assert load_tournament_name(tournament) == ("RelicFest 2026", [])


@pytest.mark.parametrize("content", [None, "", "slug: relicfest-2026\n", "name:\n", "- liste\n"])
def test_nom_du_dossier_par_defaut(tournament, content):
    if content is not None:
        (tournament / "tournament.yaml").write_text(content, encoding="utf-8")
    assert load_tournament_name(tournament) == ("relicfest-2026", [])


def test_yaml_illisible(tournament):
    (tournament / "tournament.yaml").write_text("name: [RelicFest\n", encoding="utf-8")
    assert load_tournament_name(tournament) == (
        "relicfest-2026", ["tournament.yaml : YAML illisible → nom du dossier utilisé (relicfest-2026)"]
    )
