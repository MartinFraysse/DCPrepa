"""Lancement en ligne de commande : un module par service (services/), sans questions interactives.

Pas de CLI complète : la GUI sera l'interface principale ; ces modules servent à dépanner et à saisir sans ouvrir de fichier.
Usage, depuis src/ :  python -m dcprepa <module> [arguments]     (python -m dcprepa --help, python -m dcprepa <module> --help)
    ex. python -m dcprepa import relicfest-2026   puis   python -m dcprepa stats relicfest-2026
        python -m dcprepa game-add relicfest-2026 --deck Terra --version v2 --oppo Ragavan --games "OTP W, OTD L, OTP W"
Ajouter un module = une fonction run_… (arguments nommés comme ses options) + une entrée dans MODULES.
"""

import argparse
import re
import sys
from datetime import date
from pathlib import Path

from dcprepa.domain.saisie import STATUSES
from dcprepa.domain.validation import DATE_FORMAT, SOURCES
from dcprepa.services import decks, games, oppos, tournament
from dcprepa.services.import_inbox import import_inbox
from dcprepa.services.import_meta import META_LABELS, import_meta
from dcprepa.services.stats import generate_stats

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
OPPOS_PATH = DATA_DIR / "oppos.yaml"


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


def show(report, success: str, failure: str = "Rien n'a été modifié") -> int:
    """Affiche le bilan d'un service de saisie : ❌ erreurs (rien écrit) ou ✅ success, puis ⚠️ avertissements ; code 0 ou 1."""
    if report.errors:
        print(f"❌ {failure}. Erreurs à corriger :")
        for message in report.errors:
            print(f"  - {message}")
    else:
        print(f"✅ {success}")
    warnings = getattr(report, "warnings", [])
    if warnings:
        print("⚠️  Avertissements :")
        for message in warnings:
            print(f"  - {message}")
    return 0 if report.ok else 1


def run_tournament_create(name: str, **fields) -> int:
    """Module « tournament-create » : crée data/tournaments/<slug>/ depuis le modèle."""
    report = tournament.create_tournament(DATA_DIR, name, _given(fields))
    return show(report, f"Tournoi créé : data/tournaments/{report.slug}/ (slug déduit du nom).", "Tournoi non créé")


def run_tournament_edit(tournament_dir: Path, **fields) -> int:
    """Module « tournament-edit » : modifie des champs de tournament.yaml."""
    changes = _given(fields)
    return show(tournament.edit_tournament(tournament_dir, changes), f"tournament.yaml modifié : {', '.join(changes)}.")


def run_game_add(tournament_dir: Path, note: str | None = None, **fields) -> int:
    """Module « game-add » : ajoute les games d'une session à games.csv (mêmes contrôles que l'import)."""
    block = {**fields, "note/ressenti": note}
    report = games.add_games(tournament_dir, block, OPPOS_PATH)
    return show(report, f"{report.matches} BO, {report.games} game(s) ajoutés : {', '.join(report.match_ids)}.")


def run_game_edit(tournament_dir: Path, match_id: str, game: str, note: str | None = None, **fields) -> int:
    """Module « game-edit » : corrige une game (position, résultat, note)."""
    changes = _given({**fields, "note/ressenti": note})
    report = games.edit_game(tournament_dir, match_id, game, changes, OPPOS_PATH)
    return show(report, f"{match_id} game {game} corrigée.")


def run_bo_edit(tournament_dir: Path, match_id: str, **fields) -> int:
    """Module « bo-edit » : corrige toutes les games d'un BO (date, source, deck, version, oppo)."""
    report = games.edit_match(tournament_dir, match_id, _given(fields), OPPOS_PATH)
    return show(report, f"BO corrigé : {', '.join(report.match_ids)} ({report.games} game(s)).")


def run_game_delete(tournament_dir: Path, match_id: str, game: str) -> int:
    """Module « game-delete » : supprime une game d'un BO (les suivantes sont renumérotées)."""
    report = games.delete_game(tournament_dir, match_id, game)
    return show(report, f"{match_id} game {game} supprimée ({report.games} game(s) restante(s) dans le BO).")


def run_bo_delete(tournament_dir: Path, match_id: str) -> int:
    """Module « bo-delete » : supprime toutes les games d'un BO."""
    return show(games.delete_match(tournament_dir, match_id), f"BO {match_id} supprimé.")


def run_oppo_add(name: str, variant_of: str | None = None) -> int:
    """Module « oppo-add » : ajoute un oppo (ou une variante d'un oppo connu) à data/oppos.yaml."""
    report = oppos.add_oppo(OPPOS_PATH, name, variant_of)
    success = f"Variante ajoutée : {report.name} → {report.reference}." if variant_of else f"Oppo ajouté : {report.name}."
    return show(report, success)


def run_deck_create(tournament_dir: Path, name: str, liste: Path | None = None, **fields) -> int:
    """Module « deck-create » : crée decks/<deck>.yaml avec la version v1 (liste lue dans un fichier texte)."""
    text, report = _read_list(liste)
    if report is None:
        report = decks.create_deck(tournament_dir, name, liste=text, **_given(fields))
    return show(report, f"Deck créé : decks/{report.deck}.yaml (v1).")


def run_deck_version(tournament_dir: Path, deck: str, liste: Path | None = None, **fields) -> int:
    """Module « deck-version » : ajoute une version (in, out, liste, notes) à la fiche d'un deck."""
    text, report = _read_list(liste)
    if report is None:
        report = decks.add_version(tournament_dir, deck, liste=text, **_given(fields))
    return show(report, f"Version {report.version} ajoutée à decks/{report.deck}.yaml.")


def run_deck_status(tournament_dir: Path, deck: str, statut: str) -> int:
    """Module « deck-status » : change le statut d'un deck (retenu, envisage, ecarte)."""
    report = decks.set_status(tournament_dir, deck, statut)
    return show(report, f"decks/{report.deck}.yaml : statut {statut}.")


def run_deck_edit(tournament_dir: Path, deck: str, **fields) -> int:
    """Module « deck-edit » : corrige le nom affiché et / ou le commandant d'un deck."""
    changes = _given(fields)
    report = decks.edit_deck(tournament_dir, deck, changes)
    return show(report, f"decks/{report.deck}.yaml modifié : {', '.join(changes)}.")


def run_deck_alias(tournament_dir: Path, deck: str, alias: str) -> int:
    """Module « deck-alias » : ajoute une appellation d'un deck dans decks/_alias.yaml."""
    report = decks.add_deck_alias(tournament_dir, deck, alias)
    return show(report, f"Appellation ajoutée : {' '.join(alias.split())} → {report.deck}.")


def _given(fields: dict) -> dict:
    """Options renseignées seulement (None = option absente)."""
    return {name: value for name, value in fields.items() if value is not None}


def _read_list(path: Path | None):
    """(texte de la liste, None) ; (« », rapport d'erreur) si le fichier est illisible."""
    if path is None:
        return "", None
    try:
        return path.read_text(encoding="utf-8"), None
    except OSError as error:
        return "", decks.DeckReport(errors=[f"liste illisible : {path} ({error.strerror})"])


def _tournament(parser):
    parser.add_argument("tournament", metavar="tournoi", help="slug du tournoi, ex. relicfest-2026")


def _tournament_fields(parser, name_required: bool):
    if name_required:
        parser.add_argument("name", metavar="nom", help="nom affiché, ex. « RelicFest 2026 » (slug déduit)")
    else:
        parser.add_argument("--name", metavar="nom", help="nom affiché (le slug ne change pas)")
    parser.add_argument("--date", help="JJ/MM/AAAA")
    parser.add_argument("--location", metavar="lieu")
    parser.add_argument("--format", help="Duel Commander par défaut")
    parser.add_argument("--banlist", help="date ou lien de la banlist")
    parser.add_argument("--notes")


def _game_add(parser):
    _tournament(parser)
    parser.add_argument("--date", default=date.today().strftime(DATE_FORMAT), help="JJ/MM/AAAA (aujourd'hui par défaut)")
    parser.add_argument("--source", required=True, choices=sorted(SOURCES))
    parser.add_argument("--deck", required=True, help="fichier, nom ou appellation du deck")
    parser.add_argument("--version", required=True, help="ex. v2")
    parser.add_argument("--oppo", required=True, help="nom de référence ou variante (data/oppos.yaml), ou deck@version")
    parser.add_argument("--games", required=True, help="format de l'inbox, ex. « OTP W, OTD L, OTP W / OTP W »")
    parser.add_argument("--note", help="note / ressenti")


def _game_edit(parser):
    _tournament(parser)
    parser.add_argument("match_id", help="ex. 02/10/2026-01")
    parser.add_argument("game", help="numéro de la game dans le BO")
    parser.add_argument("--position", choices=["OTP", "OTD"])
    parser.add_argument("--resultat", choices=["W", "L"])
    parser.add_argument("--note", help="note / ressenti (« » pour l'effacer)")


def _bo_edit(parser):
    _tournament(parser)
    parser.add_argument("match_id", help="ex. 02/10/2026-01")
    for option, text in (("--date", "JJ/MM/AAAA (nouveau match_id)"), ("--source", None), ("--deck", None), ("--version", None), ("--oppo", None)):
        parser.add_argument(option, help=text)


def _game_delete(parser):
    _tournament(parser)
    parser.add_argument("match_id", help="ex. 02/10/2026-01")
    parser.add_argument("game", help="numéro de la game dans le BO")


def _bo_delete(parser):
    _tournament(parser)
    parser.add_argument("match_id", help="ex. 02/10/2026-01")


def _oppo_add(parser):
    parser.add_argument("name", metavar="nom", help="nom de l'oppo à ajouter")
    parser.add_argument("--variant-of", metavar="oppo", help="en faire une variante de cet oppo connu")


def _deck_create(parser):
    _tournament(parser)
    parser.add_argument("name", metavar="nom", help="nom affiché, ex. « Kinnan Combo » (fichier déduit)")
    parser.add_argument("--commandant")
    parser.add_argument("--statut", choices=STATUSES)
    parser.add_argument("--liste", type=Path, metavar="fichier", help="export MTGO / Moxfield (« 1 Nom de carte » par ligne)")
    parser.add_argument("--notes")


def _deck_version(parser):
    _tournament(parser)
    parser.add_argument("deck", help="fichier, nom ou appellation du deck")
    parser.add_argument("--version", help="identifiant (suivant automatique par défaut, ex. v3 → v4)")
    parser.add_argument("--in", dest="cards_in", action="append", metavar="carte", help="carte ajoutée (option répétable)")
    parser.add_argument("--out", dest="cards_out", action="append", metavar="carte", help="carte retirée (option répétable)")
    parser.add_argument("--liste", type=Path, metavar="fichier", help="liste complète (export MTGO / Moxfield)")
    parser.add_argument("--notes")


def _deck_status(parser):
    _tournament(parser)
    parser.add_argument("deck", help="fichier, nom ou appellation du deck")
    parser.add_argument("statut", choices=STATUSES)


def _deck_edit(parser):
    _tournament(parser)
    parser.add_argument("deck", help="fichier, nom ou appellation du deck")
    parser.add_argument("--name", metavar="nom", help="nouveau nom affiché (le fichier ne change pas)")
    parser.add_argument("--commandant")


def _deck_alias(parser):
    _tournament(parser)
    parser.add_argument("deck", help="fichier, nom ou appellation du deck")
    parser.add_argument("alias", help="nouvelle appellation, ex. « Terra mid »")


MODULES = {
    "import": (run_import, "importe inbox.yaml dans games.csv (tout ou rien)", _tournament),
    "meta": (run_meta, "importe le méta MTGTop8 (général + papier, 2 mois, top 20) dans meta/AAAA-MM-JJ/", _tournament),
    "stats": (run_stats, "génère stats/<deck>.md pour chaque fiche deck + stats/synthese.md (tout ou rien)", _tournament),
    "tournament-create": (run_tournament_create, "crée un tournoi depuis le modèle (slug déduit du nom)", lambda p: _tournament_fields(p, True)),
    "tournament-edit": (run_tournament_edit, "modifie tournament.yaml (nom, date, lieu, format, banlist, notes)", lambda p: (_tournament(p), _tournament_fields(p, False))),
    "game-add": (run_game_add, "ajoute les games d'une session à games.csv", _game_add),
    "game-edit": (run_game_edit, "corrige une game (position, résultat, note)", _game_edit),
    "bo-edit": (run_bo_edit, "corrige un BO entier (date, source, deck, version, oppo)", _bo_edit),
    "game-delete": (run_game_delete, "supprime une game d'un BO", _game_delete),
    "bo-delete": (run_bo_delete, "supprime un BO", _bo_delete),
    "oppo-add": (run_oppo_add, "ajoute un oppo ou une variante à data/oppos.yaml", _oppo_add),
    "deck-create": (run_deck_create, "crée une fiche deck avec la version v1", _deck_create),
    "deck-version": (run_deck_version, "ajoute une version à un deck", _deck_version),
    "deck-status": (run_deck_status, "change le statut d'un deck (retenu, envisage, ecarte)", _deck_status),
    "deck-edit": (run_deck_edit, "corrige le nom affiché ou le commandant d'un deck", _deck_edit),
    "deck-alias": (run_deck_alias, "ajoute une appellation d'un deck (decks/_alias.yaml)", _deck_alias),
}


ARGPARSE_FR = [
    (r"the following arguments are required: ", "arguments obligatoires manquants : "),
    (r"unrecognized arguments: ", "arguments inconnus : "),
    (r"invalid choice: (.*) \(choose from (.*)\)", r"valeur invalide : \1 (possibles : \2)"),
    (r"expected one argument", "une valeur est attendue"),
    (r"^argument ([^:]+): ", r"argument \1 : "),
]


class FrenchHelpFormatter(argparse.HelpFormatter):
    """Aide en français : « utilisation : » au lieu de « usage: »."""

    def add_usage(self, usage, actions, groups, prefix=None):
        super().add_usage(usage, actions, groups, "utilisation : " if prefix is None else prefix)


class FrenchParser(argparse.ArgumentParser):
    """ArgumentParser dont l'aide et les erreurs d'arguments s'affichent en français (code de sortie 2, comme argparse)."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("formatter_class", FrenchHelpFormatter)
        super().__init__(*args, add_help=False, **{k: v for k, v in kwargs.items() if k != "add_help"})
        self._positionals.title = "arguments"
        self._optionals.title = "options"
        self.add_argument("-h", "--help", action="help", help="affiche cette aide")

    def error(self, message: str):
        for pattern, replacement in ARGPARSE_FR:
            message = re.sub(pattern, replacement, message)
        self.print_usage(sys.stderr)
        self.exit(2, f"{self.prog} : erreur : {message}\n")


def build_parser() -> argparse.ArgumentParser:
    parser = FrenchParser(prog="python -m dcprepa", description="DCPrepa : préparation d'un tournoi de Duel Commander.")
    modules = parser.add_subparsers(dest="module", required=True, metavar="module", title="modules")
    for name, (_, description, configure) in MODULES.items():
        configure(modules.add_parser(name, help=description, description=description))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = vars(build_parser().parse_args(argv))
    run, _, _ = MODULES[args.pop("module")]
    slug = args.pop("tournament", None)
    if slug is not None:
        tournament_dir = DATA_DIR / "tournaments" / slug
        if not tournament_dir.is_dir():
            print(f"Tournoi introuvable : {tournament_dir}")
            return 2
        args["tournament_dir"] = tournament_dir
    return run(**args)


if __name__ == "__main__":
    sys.exit(main())
