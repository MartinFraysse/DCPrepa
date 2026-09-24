from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from dcprepa.domain.decks import resolve_deck
from dcprepa.domain.names import build_name_index, name_key
from dcprepa.domain.saisie import (
    DECK_FIELDS,
    check_new_deck,
    check_new_version,
    check_status,
    next_version,
    parse_card_list,
)
from dcprepa.domain.validation import DATE_FORMAT
from dcprepa.storage.decks import (
    add_alias,
    append_version,
    create_deck_file,
    load_deck_aliases,
    load_decks,
    update_deck_fields,
    version_lines,
)

DECKS = "decks"


@dataclass
class DeckReport:
    """Bilan d'une saisie sur les decks : le deck (nom de son fichier), la version ajoutée, erreurs (rien écrit) et avertissements."""

    deck: str | None = None
    version: str | None = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def create_deck(
    tournament_dir: Path, name: str, commandant: str = "", statut: str = "envisage",
    liste: str = "", notes: str = "", today: date | None = None,
) -> DeckReport:
    """Crée decks/<deck>.yaml avec sa version v1 ; fichier déduit du nom (« Terra Midrange » → terra-midrange).

    liste : export MTGO / Moxfield collé (« 1 Nom de carte » par ligne), facultatif ; pas 100 cartes → avertissement.
    Refusé : nom vide, réservé ou déjà pris par un deck (fichier, name ou appellation), statut inconnu, ligne de liste mal formée.
    """
    report = DeckReport()
    decks, deck_index = _references(tournament_dir, report)
    if report.errors:
        return report

    deck, errors = check_new_deck(name, deck_index)
    report.errors += errors + check_status(statut)
    card_list, errors, warnings = parse_card_list(liste)
    report.errors += errors
    if report.errors:
        return report

    stamp = (today or date.today()).strftime(DATE_FORMAT)
    fields = {"name": " ".join(str(name).split()), "commandant": " ".join(str(commandant).split()), "statut": str(statut).strip()}
    report.errors += create_deck_file(
        tournament_dir / DECKS / f"{deck}.yaml", f"Fiche deck créée par la saisie le {stamp}.", fields, card_list, " ".join(str(notes).split())
    )
    if not report.errors:
        report.deck, report.version, report.warnings = deck, "v1", warnings
    return report


def add_version(
    tournament_dir: Path, deck: str, version: str | None = None,
    cards_in: list[str] | None = None, cards_out: list[str] | None = None, liste: str = "", notes: str = "",
) -> DeckReport:
    """Ajoute une version à la fin de la fiche d'un deck (désigné par son fichier, son name ou une appellation).

    version : None → suivante automatique (v3 → v4). Au moins un changement : cartes ajoutées (in), retirées (out) ou liste complète.
    """
    report = DeckReport()
    decks, deck_index = _references(tournament_dir, report)
    found = _resolve(deck, decks, deck_index, report)
    if report.errors:
        return report

    cards_in = [" ".join(str(card).split()) for card in cards_in or [] if str(card).strip()]
    cards_out = [" ".join(str(card).split()) for card in cards_out or [] if str(card).strip()]
    card_list, errors, warnings = parse_card_list(liste)
    version = str(version).strip() if version is not None else next_version(decks[found])
    report.errors += errors + check_new_version(version, decks[found], cards_in, cards_out, card_list)
    if report.errors:
        return report

    lines = version_lines(version, cards_in, cards_out, card_list, " ".join(str(notes).split()))
    report.errors += append_version(tournament_dir / DECKS / f"{found}.yaml", lines, version)
    if not report.errors:
        report.deck, report.version, report.warnings = found, version, warnings
    return report


def set_status(tournament_dir: Path, deck: str, statut: str) -> DeckReport:
    """Change le statut d'un deck : retenu, envisage ou ecarte (la synthèse ne compare au méta que les decks retenus ou envisagés)."""
    report = DeckReport()
    report.errors += check_status(statut)
    return _update(tournament_dir, deck, {"statut": str(statut).strip()}, report)


def edit_deck(tournament_dir: Path, deck: str, changes: dict[str, str]) -> DeckReport:
    """Corrige le nom affiché (name) et / ou le commandant d'un deck ; le fichier du deck ne change pas.

    Un nouveau name ne doit pas être une appellation d'un autre deck.
    """
    report = DeckReport()
    report.errors += [f"champ non modifiable ici : {name} (possibles : {', '.join(DECK_FIELDS)})" for name in changes if name not in DECK_FIELDS]
    if not changes:
        report.errors.append("rien à modifier")
    if "name" in changes and not str(changes["name"]).strip():
        report.errors.append("nom du deck vide")
    return _update(tournament_dir, deck, {key: " ".join(str(value).split()) for key, value in changes.items()}, report)


def add_deck_alias(tournament_dir: Path, deck: str, alias: str) -> DeckReport:
    """Ajoute une appellation d'un deck (ex. « Terra mid ») dans decks/_alias.yaml : reconnue ensuite par l'import et la saisie."""
    report = DeckReport()
    decks, deck_index = _references(tournament_dir, report)
    found = _resolve(deck, decks, deck_index, report)
    alias = " ".join(str(alias).split())
    if not alias:
        report.errors.append("appellation vide")
    elif name_key(alias) in deck_index:
        report.errors.append(f"appellation déjà prise : {alias} → {deck_index[name_key(alias)]}")
    if report.errors:
        return report
    report.errors += add_alias(tournament_dir / DECKS, found, alias)
    if not report.errors:
        report.deck = found
    return report


def _references(tournament_dir: Path, report: DeckReport) -> tuple[dict[str, list[str]], dict[str, str]]:
    """Decks (fiches et versions) et index de leurs appellations ; les erreurs de lecture vont dans report."""
    decks, errors = load_decks(tournament_dir)
    report.errors += errors
    aliases, errors = load_deck_aliases(tournament_dir, decks)
    report.errors += errors
    deck_index, errors = build_name_index(aliases, "decks")
    report.errors += errors
    return decks, deck_index


def _resolve(deck: str, decks: dict[str, list[str]], deck_index: dict[str, str], report: DeckReport) -> str | None:
    """Nom de fichier du deck désigné par une appellation ; erreur dans report s'il est inconnu."""
    found = resolve_deck(deck, deck_index)
    if found is None or found not in decks:
        available = ", ".join(sorted(decks)) or "aucun"
        report.errors.append(f"deck inconnu : {deck} (decks disponibles : {available})")
        return None
    return found


def _update(tournament_dir: Path, deck: str, fields: dict[str, str], report: DeckReport) -> DeckReport:
    """Écrit des champs de la fiche d'un deck (set_status, edit_deck) après contrôles ; rien n'est écrit si report a une erreur."""
    decks, deck_index = _references(tournament_dir, report)
    found = _resolve(deck, decks, deck_index, report) if not report.errors else None
    new_name = fields.get("name")
    if found and new_name and deck_index.get(name_key(new_name), found) != found:
        report.errors.append(f"appellation déjà prise : {new_name} → {deck_index[name_key(new_name)]}")
    if report.errors:
        return report
    report.errors += update_deck_fields(tournament_dir / DECKS / f"{found}.yaml", fields)
    if not report.errors:
        report.deck = found
    return report
