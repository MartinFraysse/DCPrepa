from dataclasses import dataclass, field
from pathlib import Path

from dcprepa.domain.rows import normalize_date
from dcprepa.domain.saisie import check_tournament_fields, slugify
from dcprepa.storage.tournament import create_tournament_dir, update_tournament_file

TEMPLATE = Path("templates") / "tournament"
TOURNAMENTS = "tournaments"


@dataclass
class TournamentReport:
    """Bilan d'une création ou d'une modification de tournoi : son slug, son dossier, les erreurs (rien n'est écrit si erreur)."""

    slug: str | None = None
    folder: Path | None = None
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def create_tournament(data_dir: Path, name: str, fields: dict[str, str] | None = None) -> TournamentReport:
    """Crée data/tournaments/<slug>/ depuis data/templates/tournament/, slug déduit du nom (« RelicFest 2026 » → relicfest-2026).

    fields : date, location, format (Duel Commander par défaut, celui du modèle), banlist, notes, tous facultatifs.
    Dossier déjà existant : erreur (pas de suffixe automatique). En cas d'erreur, rien n'est créé.
    """
    report = TournamentReport()
    values = {"name": name, **(fields or {})}
    report.errors += check_tournament_fields(values, creating=True)
    if report.errors:
        return report

    values = _cleaned(values)
    slug = slugify(values["name"])
    target = data_dir / TOURNAMENTS / slug
    report.errors += create_tournament_dir(data_dir / TEMPLATE, target, {**values, "slug": slug})
    if not report.errors:
        report.slug, report.folder = slug, target
    return report


def edit_tournament(tournament_dir: Path, changes: dict[str, str]) -> TournamentReport:
    """Modifie la fiche d'un tournoi : name, format, date, location, banlist, notes (le slug et le dossier ne changent pas).

    Ex. edit_tournament(t, {"banlist": "01/09/2026", "notes": "Top 8 à 16 h"}). Une valeur vide efface le champ.
    """
    report = TournamentReport()
    report.errors += check_tournament_fields(changes, creating=False)
    if not report.errors:
        report.errors += update_tournament_file(tournament_dir, _cleaned(changes))
    if not report.errors:
        report.slug, report.folder = tournament_dir.name, tournament_dir
    return report


def _cleaned(values: dict[str, str]) -> dict[str, str]:
    """Espaces en trop retirés, date réécrite avec ses zéros (« 1/9/2026 » → « 01/09/2026 »)."""
    cleaned = {name: " ".join(str(value).split()) if value is not None else "" for name, value in values.items()}
    if cleaned.get("date"):
        cleaned["date"] = normalize_date(cleaned["date"])
    return cleaned
