from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from dcprepa.domain.oppos import build_oppo_index, check_new_oppo
from dcprepa.domain.validation import DATE_FORMAT
from dcprepa.storage.oppos import append_oppos, insert_variant, load_oppos


@dataclass
class OppoReport:
    """Bilan d'un ajout à data/oppos.yaml : le nom ajouté, sa référence (lui-même pour un nouvel oppo), les erreurs."""

    name: str | None = None
    reference: str | None = None
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def add_oppo(oppos_path: Path, name: str, variant_of: str | None = None, today: date | None = None) -> OppoReport:
    """Ajoute un oppo à data/oppos.yaml : nouvel oppo, ou variante d'un oppo connu (variant_of : son nom ou une variante).

    Ex. add_oppo(o, "Ragavan") ; add_oppo(o, "Ragavn", variant_of="Ragavan").
    Nouvel oppo : ajouté à la fin du fichier sous « # Ajouté par la saisie le JJ/MM/AAAA ». Variante : sous sa référence.
    oppos.yaml illisible ou ambigu, nom refusé (voir check_new_oppo) : rien n'est écrit.
    """
    report = OppoReport()
    oppos, errors = load_oppos(oppos_path)
    report.errors += errors
    index, errors = build_oppo_index(oppos) if not report.errors else ({}, [])
    report.errors += errors
    if report.errors:
        return report

    reference, errors = check_new_oppo(name, variant_of, index)
    report.errors += errors
    if report.errors:
        return report

    name = " ".join(str(name).split())
    if reference is None:
        stamp = (today or date.today()).strftime(DATE_FORMAT)
        append_oppos(oppos_path, {name: []}, f"Ajouté par la saisie le {stamp}")
        reference = name
    elif not insert_variant(oppos_path, reference, name):
        report.errors.append(f"oppos.yaml : impossible de placer la variante sous {reference} (fichier à vérifier à la main)")
        return report
    report.name, report.reference = name, reference
    return report
