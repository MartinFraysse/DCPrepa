import pytest
import yaml

from dcprepa.storage.yaml_text import append_list_item, set_fields, yaml_scalar

TEXT = (
    "# Fiche\n"
    "\n"
    "name:                       # nom affiché\n"
    "format: Duel Commander\n"
    "notes:\n"
)


def test_valeur_avec_commentaire_aligne():
    assert set_fields(TEXT, {"name": "RelicFest 2026"}) == TEXT.replace(
        "name:                       # nom affiché", "name: RelicFest 2026        # nom affiché"
    )


def test_valeur_longue_commentaire_decale():
    updated = set_fields(TEXT, {"name": "Un nom de tournoi vraiment très long"})
    assert "name: Un nom de tournoi vraiment très long # nom affiché\n" in updated


def test_remplacer_et_effacer():
    updated = set_fields(TEXT, {"format": "Legacy", "notes": "Top 8"})
    assert updated == TEXT.replace("format: Duel Commander", "format: Legacy").replace("notes:\n", "notes: Top 8\n")
    assert set_fields(updated, {"format": ""}) == updated.replace("format: Legacy", "format:")


def test_champ_absent_ajoute_a_la_fin():
    assert set_fields(TEXT, {"location": "Toulouse"}) == TEXT + "location: Toulouse\n"


@pytest.mark.parametrize("value", ["Été Duel #3", "a: b", "https://exemple.org/banlist", "- liste", "yes"])
def test_valeurs_speciales_relues_a_l_identique(value):
    assert yaml.safe_load(set_fields(TEXT, {"notes": value}))["notes"] == value


def test_texte_inattendu():
    assert set_fields("- une liste\n", {"name": "X"}) is None


def test_yaml_scalar():
    assert yaml_scalar("Phelia, Exuberant Shepherd") == "Phelia, Exuberant Shepherd"
    assert yaml_scalar("Été #3") == "'Été #3'"


def test_append_list_item():
    text = "# Appellations\nterra:\n    - Terra\n\nkinnan:\n"
    assert append_list_item(text, "terra", "Terra mid") == "# Appellations\nterra:\n    - Terra\n    - Terra mid\n\nkinnan:\n"
    assert append_list_item(text, "kinnan", "Kinnan") == text + "    - Kinnan\n"
    assert append_list_item(text, "sythis", "Sythis") == text + "\nsythis:\n    - Sythis\n"
    assert append_list_item("# commentaire\n", "terra", "Terra") == "# commentaire\n\nterra:\n    - Terra\n"
    assert append_list_item("", "terra", "Terra") == "terra:\n    - Terra\n"
    assert append_list_item("- liste\n", "terra", "x") is None
