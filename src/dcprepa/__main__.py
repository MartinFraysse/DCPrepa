"""Lancement minimal en ligne de commande, en attendant la vraie CLI (interfaces/cli/).

Usage, depuis src/ :  python -m dcprepa <module> <tournoi>
    ex. python -m dcprepa import relicfest-2026   puis   python -m dcprepa stats relicfest-2026
        python -m dcprepa meta relicfest-2026      (méta MTGTop8, avant stats)
Chaque module correspond à un service (services/) ; en ajouter un = une entrée de plus dans MODULES.
"""

import sys
from pathlib import Path

from dcprepa.services.import_inbox import import_inbox
from dcprepa.services.import_meta import META_LABELS, import_meta
from dcprepa.services.stats import generate_stats

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def run_import(tournament_dir: Path) -> int:
    """Module « import » : importe l'inbox du tournoi dans games.csv et affiche le bilan."""
    report = import_inbox(tournament_dir, DATA_DIR / "oppos.yaml")

    if not report.ok:
        print("❌ Import annulé, aucun fichier modifié. Erreurs à corriger :")
        for message in report.errors:
            print(f"  - {message}")
    elif report.blocks == 0:
        print("Inbox vide : rien à importer.")
    else:
        print(f"✅ {report.blocks} bloc(s) importé(s) : {report.matches} BO, {report.games} game(s).")

    if report.warnings:
        print("⚠️  Avertissements :")
        for message in report.warnings:
            print(f"  - {message}")

    return 0 if report.ok else 1


def run_stats(tournament_dir: Path) -> int:
    """Module « stats » : génère stats/<deck>.md pour chaque fiche deck du tournoi, stats/synthese.md, et affiche le bilan."""
    report = generate_stats(tournament_dir)

    if not report.ok:
        print("❌ Stats annulées, aucun rapport écrit. Erreurs à corriger :")
        for message in report.errors:
            print(f"  - {message}")
    else:
        print(
            f"✅ {len(report.decks)} rapport(s) + synthèse écrits à partir de {report.games} game(s) :"
            f" {', '.join(report.decks) or 'aucun deck'}."
        )
        if report.meta:
            print(f"   Méta : meta/{report.meta}/ (matchups triés par poids papier).")
        else:
            print("   Pas de méta : matchups triés par nombre de games.")

    if report.warnings:
        print("⚠️  Avertissements :")
        for message in report.warnings:
            print(f"  - {message}")

    return 0 if report.ok else 1


def run_meta(tournament_dir: Path) -> int:
    """Module « meta » : importe le méta MTGTop8 (général et papier) dans meta/AAAA-MM-JJ/ et affiche le bilan."""
    report = import_meta(tournament_dir, DATA_DIR / "oppos.yaml")

    if not report.ok:
        print("❌ Import du méta annulé, aucun fichier modifié. Erreurs à corriger :")
        for message in report.errors:
            print(f"  - {message}")
    else:
        details = ", ".join(
            f"{META_LABELS[kind].removeprefix('méta ')} {oppos} oppos ({decks} decks)" for kind, (oppos, decks) in report.metas.items()
        )
        replaced = " (remplace l'import du jour)" if report.replaced else ""
        print(f"✅ meta/{report.folder}/ écrit{replaced} : {details}.")
        if report.added_oppos:
            print(f"📝 {len(report.added_oppos)} oppo(s) ajouté(s) à data/oppos.yaml : {', '.join(report.added_oppos)}.")

    if report.warnings:
        print("⚠️  Avertissements :")
        for message in report.warnings:
            print(f"  - {message}")

    return 0 if report.ok else 1


MODULES = {
    "import": (run_import, "importe inbox.yaml dans games.csv (tout ou rien)"),
    "meta": (run_meta, "importe le méta MTGTop8 (général + papier, 2 mois, top 20) dans meta/AAAA-MM-JJ/"),
    "stats": (run_stats, "génère stats/<deck>.md pour chaque fiche deck + stats/synthese.md (tout ou rien)"),
}


def usage() -> str:
    lines = ["Usage : python -m dcprepa <module> <tournoi>   (ex. python -m dcprepa import relicfest-2026)", "Modules :"]
    lines += [f"  {name:<8} {description}" for name, (_, description) in MODULES.items()]
    return "\n".join(lines)


def main() -> int:
    if len(sys.argv) != 3:
        print(usage())
        return 2

    module, tournament = sys.argv[1], sys.argv[2]
    if module not in MODULES:
        print(f"Module inconnu : {module}\n{usage()}")
        return 2

    tournament_dir = DATA_DIR / "tournaments" / tournament
    if not tournament_dir.is_dir():
        print(f"Tournoi introuvable : {tournament_dir}")
        return 2

    run, _ = MODULES[module]
    return run(tournament_dir)


if __name__ == "__main__":
    sys.exit(main())
