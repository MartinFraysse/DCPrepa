from dcprepa.storage.stats import write_report


def read_raw(path):
    with path.open(encoding="utf-8", newline="") as file:
        return file.read()


def test_ecrit_et_cree_le_dossier(tmp_path):
    path = tmp_path / "stats" / "terra.md"
    write_report(path, "# Terra\n\n| ⚠️ 33.3 % (1/3) |\n")
    assert read_raw(path) == "# Terra\n\n| ⚠️ 33.3 % (1/3) |\n"


def test_remplace_l_ancien_rapport(tmp_path):
    path = tmp_path / "terra.md"
    path.write_text("ancien rapport, bien plus long que le nouveau\n", encoding="utf-8")
    write_report(path, "nouveau\n")
    assert read_raw(path) == "nouveau\n"


def test_pas_de_fichier_temporaire_restant(tmp_path):
    write_report(tmp_path / "terra.md", "texte\n")
    assert [p.name for p in tmp_path.iterdir()] == ["terra.md"]


def test_fins_de_ligne_lf(tmp_path):
    path = tmp_path / "terra.md"
    write_report(path, "a\nb\n")
    assert path.read_bytes() == b"a\nb\n"
