import pytest

from dcprepa.storage.tournament import create_tournament_dir, load_tournament_name, load_tournament_sheet


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


def test_creation_remplace_un_tmp_abandonne(tmp_path):
    template = tmp_path / "modele"
    (template / "stats").mkdir(parents=True)
    (template / "tournament.yaml").write_text("name:\nslug:\n", encoding="utf-8")
    (template / "README.md").write_text("à retirer\n", encoding="utf-8")
    leftover = tmp_path / "tournaments" / "x.tmp"
    leftover.mkdir(parents=True)
    (leftover / "vieux.txt").write_text("", encoding="utf-8")

    assert create_tournament_dir(template, tmp_path / "tournaments" / "x", {"name": "X", "slug": "x"}) == []
    created = tmp_path / "tournaments" / "x"
    assert sorted(path.name for path in created.iterdir()) == ["stats", "tournament.yaml"]
    assert not leftover.exists()


def test_creation_modele_inattendu(tmp_path):
    template = tmp_path / "modele"
    template.mkdir()
    (template / "tournament.yaml").write_text("- liste\n", encoding="utf-8")
    errors = create_tournament_dir(template, tmp_path / "x", {"name": "X"})
    assert errors == ["modèle tournament.yaml inattendu : impossible d'y écrire name"]
    assert not (tmp_path / "x").exists()


def test_load_tournament_sheet(tmp_path):
    folder = tmp_path / "relicfest-2026"
    folder.mkdir()
    assert load_tournament_sheet(folder) == (
        {"name": "relicfest-2026", "slug": "", "format": "", "date": "", "location": "", "banlist": "", "notes": ""}, []
    )
    (folder / "tournament.yaml").write_text("name: RelicFest 2026\ndate: 31/10/2026   # JJ/MM/AAAA\nnotes:\n", encoding="utf-8")
    sheet, errors = load_tournament_sheet(folder)
    assert (sheet["name"], sheet["date"], sheet["notes"], errors) == ("RelicFest 2026", "31/10/2026", "", [])
    (folder / "tournament.yaml").write_text("name: [\n", encoding="utf-8")
    assert load_tournament_sheet(folder)[1] == ["tournament.yaml : YAML illisible"]
