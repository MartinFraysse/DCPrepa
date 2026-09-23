"""Lancement minimal en ligne de commande, en attendant la vraie CLI (interfaces/cli/).

Usage, depuis src/ :  python -m dcprepa <module> <tournoi>      ex. python -m dcprepa import relicfest-2026
Chaque module correspond à un service (services/) ; en ajouter un = une entrée de plus dans MODULES.
"""

import sys
from pathlib import Path

from dcprepa.services.import_inbox import import_inbox

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
        print(f"✅ {report.blocks} bloc(s) importé(s) : {report.matches} match(s), {report.games} game(s).")

    if report.warnings:
        print("⚠️  Avertissements :")
        for message in report.warnings:
            print(f"  - {message}")

    return 0 if report.ok else 1


MODULES = {
    "import": (run_import, "importe inbox.yaml dans games.csv (tout ou rien)"),
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
