from pathlib import Path

import pytest

from dcprepa.storage.decks import load_deck_aliases, load_decks

DECK_V1_V2 = """\
name: Terra Midrange
commandant: Terra, Magical Adept
statut: envisage
versions:
    -   version: v1
        liste: |
                1 Abrupt Decay
    -   version: v2
        in:
            - Carte ajoutée
"""


def write_deck(tournament_dir, filename, content):
    """Crée decks/<filename> dans un dossier de tournoi de test."""
    decks_dir = tournament_dir / "decks"
    decks_dir.mkdir(exist_ok=True)
    (decks_dir / filename).write_text(content, encoding="utf-8")


def test_deck_valide(tmp_path):
    write_deck(tmp_path, "terra-midrange.yaml", DECK_V1_V2)
    assert load_decks(tmp_path) == ({"terra-midrange": ["v1", "v2"]}, [])


def test_plusieurs_decks(tmp_path):
    write_deck(tmp_path, "terra-midrange.yaml", DECK_V1_V2)
    write_deck(tmp_path, "tymna-thrasios.yaml", "versions:\n    - version: v3\n")
    decks, errors = load_decks(tmp_path)
    assert decks == {"terra-midrange": ["v1", "v2"], "tymna-thrasios": ["v3"]}
    assert errors == []


def test_modele_ignore(tmp_path):
    write_deck(tmp_path, "_modele.yaml", "name:\nversions:\n    - version: v1\n")
    assert load_decks(tmp_path) == ({}, [])


def test_autres_extensions_ignorees(tmp_path):
    write_deck(tmp_path, "notes.txt", "pas un deck")
    assert load_decks(tmp_path) == ({}, [])


def test_dossier_decks_absent(tmp_path):
    decks, errors = load_decks(tmp_path)
    assert decks == {}
    assert errors == [f"dossier introuvable : {tmp_path / 'decks'}"]


def test_dossier_decks_vide(tmp_path):
    (tmp_path / "decks").mkdir()
    assert load_decks(tmp_path) == ({}, [])


def test_version_numerique_convertie_en_texte(tmp_path):
    write_deck(tmp_path, "deck.yaml", "versions:\n    - version: 3\n    - version: 1.10\n")
    assert load_decks(tmp_path) == ({"deck": ["3", "1.1"]}, [])


def test_fiche_invalide_ecartee_les_autres_chargees(tmp_path):
    write_deck(tmp_path, "terra-midrange.yaml", DECK_V1_V2)
    write_deck(tmp_path, "casse.yaml", "versions: [v1\n")
    decks, errors = load_decks(tmp_path)
    assert decks == {"terra-midrange": ["v1", "v2"]}
    assert len(errors) == 1
    assert errors[0].startswith("casse.yaml : YAML illisible")


def test_sans_versions(tmp_path):
    write_deck(tmp_path, "deck.yaml", "name: Deck\n")
    assert load_decks(tmp_path) == (
        {},
        ["deck.yaml : aucune version (champ « versions » manquant ou vide)"],
    )


def test_fichier_vide(tmp_path):
    write_deck(tmp_path, "deck.yaml", "")
    assert load_decks(tmp_path) == (
        {},
        ["deck.yaml : aucune version (champ « versions » manquant ou vide)"],
    )


def test_version_sans_identifiant(tmp_path):
    write_deck(tmp_path, "deck.yaml", "versions:\n    - version: v1\n    - liste: x\n")
    assert load_decks(tmp_path) == (
        {},
        ["deck.yaml : version n°2 sans identifiant (champ « version »)"],
    )


def test_version_en_double(tmp_path):
    write_deck(tmp_path, "deck.yaml", "versions:\n    - version: v1\n    - version: v1\n")
    assert load_decks(tmp_path) == ({}, ["deck.yaml : version en double : v1"])


def test_espaces_autour_de_la_version(tmp_path):
    write_deck(tmp_path, "deck.yaml", 'versions:\n    - version: " v1 "\n')
    assert load_decks(tmp_path) == ({"deck": ["v1"]}, [])


def test_accents_dans_la_fiche(tmp_path):
    write_deck(tmp_path, "deck.yaml", "name: Éowyn\nversions:\n    - version: v1\n      notes: Plus de removal, carte retirée\n")
    assert load_decks(tmp_path) == ({"deck": ["v1"]}, [])


def test_decks_tries_par_nom(tmp_path):
    for name in ["zur.yaml", "atraxa.yaml", "kess.yaml"]:
        write_deck(tmp_path, name, "versions:\n    - version: v1\n")
    decks, _ = load_decks(tmp_path)
    assert list(decks) == ["atraxa", "kess", "zur"]


@pytest.mark.parametrize(
    "content",
    [
        "- version: v1\n",
        "juste du texte\n",
        "versions: v1\n",
        "versions:\n",
        "versions: []\n",
    ],
)
def test_structure_sans_liste_de_versions(tmp_path, content):
    write_deck(tmp_path, "deck.yaml", content)
    assert load_decks(tmp_path) == (
        {},
        ["deck.yaml : aucune version (champ « versions » manquant ou vide)"],
    )


@pytest.mark.parametrize(
    "entry",
    [
        "    - v1\n",
        "    - version:\n",
        '    - version: ""\n',
        '    - version: "   "\n',
    ],
)
def test_entree_de_version_invalide(tmp_path, entry):
    write_deck(tmp_path, "deck.yaml", "versions:\n" + entry)
    assert load_decks(tmp_path) == (
        {},
        ["deck.yaml : version n°1 sans identifiant (champ « version »)"],
    )


def test_toutes_les_erreurs_d_une_fiche(tmp_path):
    content = "versions:\n    - version: v1\n    - liste: x\n    - version: v1\n"
    write_deck(tmp_path, "deck.yaml", content)
    assert load_decks(tmp_path) == (
        {},
        [
            "deck.yaml : version n°2 sans identifiant (champ « version »)",
            "deck.yaml : version en double : v1",
        ],
    )


def test_erreurs_de_plusieurs_fiches(tmp_path):
    write_deck(tmp_path, "a.yaml", "name: A\n")
    write_deck(tmp_path, "b.yaml", "versions:\n    - version: v1\n    - version: v1\n")
    write_deck(tmp_path, "c.yaml", "versions:\n    - version: v1\n")
    assert load_decks(tmp_path) == (
        {"c": ["v1"]},
        [
            "a.yaml : aucune version (champ « versions » manquant ou vide)",
            "b.yaml : version en double : v1",
        ],
    )


def test_modele_du_template_ignore():
    template = Path(__file__).resolve().parents[3] / "data" / "templates" / "tournament"
    assert load_decks(template) == ({}, [])


def load_all(tmp_path):
    decks, errors = load_decks(tmp_path)
    assert errors == []
    return load_deck_aliases(tmp_path, decks)


def test_appellations_fichier_et_name(tmp_path):
    write_deck(tmp_path, "terra-5c.yaml", "name: Terra 5C\nversions:\n    - version: v1\n")
    assert load_all(tmp_path) == ({"terra-5c": ["terra-5c", "Terra 5C"]}, [])


@pytest.mark.parametrize("name_line", ["", "name:\n", "name: '   '\n"])
def test_appellations_sans_name(tmp_path, name_line):
    write_deck(tmp_path, "terra-5c.yaml", name_line + "versions:\n    - version: v1\n")
    assert load_all(tmp_path) == ({"terra-5c": ["terra-5c"]}, [])


def test_appellations_avec_alias(tmp_path):
    write_deck(tmp_path, "terra-5c.yaml", "name: Terra 5C\nversions:\n    - version: v1\n")
    write_deck(tmp_path, "tnt.yaml", "versions:\n    - version: v1\n")
    write_deck(tmp_path, "_alias.yaml", "# commentaire\nterra-5c:\n    - Terra\n    - ' Terra mid '\ntnt:\n")
    assert load_all(tmp_path) == ({"terra-5c": ["terra-5c", "Terra 5C", "Terra", "Terra mid"], "tnt": ["tnt"]}, [])


@pytest.mark.parametrize("text", ["", "# seulement des commentaires\n"])
def test_alias_vide(tmp_path, text):
    write_deck(tmp_path, "terra-5c.yaml", "versions:\n    - version: v1\n")
    write_deck(tmp_path, "_alias.yaml", text)
    assert load_all(tmp_path) == ({"terra-5c": ["terra-5c"]}, [])


def test_alias_deck_inconnu(tmp_path):
    write_deck(tmp_path, "terra-5c.yaml", "versions:\n    - version: v1\n")
    write_deck(tmp_path, "_alias.yaml", "terra:\n    - Terra mid\n")
    assert load_all(tmp_path) == (
        {},
        ["_alias.yaml : deck inconnu : terra (decks disponibles : terra-5c)"],
    )


def test_alias_variantes_pas_en_liste(tmp_path):
    write_deck(tmp_path, "terra-5c.yaml", "versions:\n    - version: v1\n")
    write_deck(tmp_path, "_alias.yaml", "terra-5c: Terra\n")
    assert load_all(tmp_path) == (
        {},
        ["_alias.yaml : terra-5c : variantes attendues sous forme de liste (« - variante »)"],
    )


@pytest.mark.parametrize("text", ["- terra-5c\n", "juste du texte\n"])
def test_alias_structure_invalide(tmp_path, text):
    write_deck(tmp_path, "terra-5c.yaml", "versions:\n    - version: v1\n")
    write_deck(tmp_path, "_alias.yaml", text)
    assert load_all(tmp_path) == (
        {},
        ["_alias.yaml : attendu « nom-du-fichier-deck: » suivi de ses variantes"],
    )


def test_alias_yaml_illisible(tmp_path):
    write_deck(tmp_path, "terra-5c.yaml", "versions:\n    - version: v1\n")
    write_deck(tmp_path, "_alias.yaml", "terra-5c: [Terra\n")
    aliases, errors = load_all(tmp_path)
    assert aliases == {}
    assert errors[0].startswith("_alias.yaml : YAML illisible")


def test_alias_ignore_par_load_decks(tmp_path):
    write_deck(tmp_path, "terra-5c.yaml", "versions:\n    - version: v1\n")
    write_deck(tmp_path, "_alias.yaml", "terra-5c:\n    - Terra\n")
    assert load_decks(tmp_path) == ({"terra-5c": ["v1"]}, [])
