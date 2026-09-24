from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from dcprepa.domain.meta import META_TOP, build_meta, propose_oppos
from dcprepa.domain.mtgtop8 import parse_meta_page
from dcprepa.domain.oppos import build_oppo_index
from dcprepa.storage.meta import META_FILES, META_NAME_FORMAT, write_meta
from dcprepa.storage.mtgtop8 import META_IDS, fetch_meta_page
from dcprepa.storage.oppos import append_oppos, load_oppos

META_LABELS = {"general": "méta général", "paper": "méta papier"}


@dataclass
class MetaReport:
    """Bilan d'un import du méta : dossier écrit, contenu de chaque méta, oppos ajoutés, erreurs et avertissements."""

    folder: str | None = None
    replaced: bool = False
    metas: dict[str, tuple[int, int]] = field(default_factory=dict)  # type → (oppos gardés, decks sur la période)
    added_oppos: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def import_meta(tournament_dir: Path, oppos_path: Path, today: date | None = None, fetch=fetch_meta_page) -> MetaReport:
    """Importe le méta MTGTop8 des 2 derniers mois (général et papier) dans meta/AAAA-MM-JJ/ du tournoi, en tout ou rien.

    1. lit data/oppos.yaml, télécharge et lit les deux pages MTGTop8 ;
    2. à la moindre erreur (fichier, réseau, page inattendue) : rien n'est écrit, le bilan liste les erreurs ;
    3. garde le top 20 de chaque méta ; les oppos du top absents de oppos.yaml reçoivent une entrée (propose_oppos),
       puis le méta est reconstruit avec ces noms ;
    4. écrit meta/<date>/general.csv et paper.csv (remplacés si le dossier du jour existe), PUIS ajoute les nouveaux
       oppos à la fin de data/oppos.yaml. Les imports des autres dates ne sont jamais touchés.

    today : date du dossier (aujourd'hui par défaut) ; fetch : téléchargement (storage.mtgtop8), remplaçable dans les tests.
    """
    report = MetaReport()
    today = today or date.today()

    oppos, errors = load_oppos(oppos_path)
    report.errors += errors
    index, errors = build_oppo_index(oppos)
    report.errors += errors
    if report.errors:
        return report

    pages = {}
    for kind, meta_id in META_IDS.items():
        html, errors = fetch(meta_id)
        if not errors:
            pages[kind], errors = parse_meta_page(html)
        report.errors += [f"{META_LABELS[kind]} : {message}" for message in errors]
    if report.errors:
        return report

    unknown = []
    for page in pages.values():
        _, names = build_meta(page, index, META_TOP)
        unknown += [name for name in names if name not in unknown]
    new_oppos = propose_oppos(unknown, index)
    index, errors = build_oppo_index({**oppos, **new_oppos})
    report.errors += errors
    if report.errors:
        return report
    metas = {kind: build_meta(page, index, META_TOP)[0] for kind, page in pages.items()}

    folder = tournament_dir / "meta" / today.strftime(META_NAME_FORMAT)
    report.replaced = any((folder / name).exists() for name in META_FILES.values())
    for kind, rows in metas.items():
        write_meta(folder / META_FILES[kind], [(row.oppo, row.decks, row.weight) for row in rows])
    append_oppos(
        oppos_path,
        new_oppos,
        f"Ajoutés par l'import du méta du {today:%d/%m/%Y} (top {META_TOP} MTGTop8) : à renommer ou regrouper au besoin.",
    )

    report.folder = folder.name
    report.metas = {kind: (len(metas[kind]), pages[kind].total) for kind in META_IDS}
    report.added_oppos = list(new_oppos)
    return report
