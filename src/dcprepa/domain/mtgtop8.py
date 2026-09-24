import html
import re
from dataclasses import dataclass

ROW_MARK = "hover_tr"
TOTAL_RE = re.compile(r">\s*(\d+)\s+decks\s*<")
NAME_RE = re.compile(r"<a\s[^>]*href=[\"']?archetype\?a=\d+[^>]*>(.*?)</a>", re.S)
PERMILLE_RE = re.compile(r">\s*(\d+(?:\.\d+)?)\s*<span[^>]*>\s*(?:&permil;|‰)")
PERMILLE_TOTAL = 1000
PERMILLE_TOLERANCE = 20  # arrondis de MTGTop8 : la somme des ‰ tombe à ± quelques ‰ de 1000


@dataclass(frozen=True)
class MetaPage:
    """Une répartition du méta lue sur MTGTop8 : nombre total de decks, et part de chaque archétype en ‰."""

    total: int
    entries: list[tuple[str, float]]


def parse_meta_page(page: str) -> tuple[MetaPage | None, list[str]]:
    """Lit le fragment « cEDH_decks » de MTGTop8 (voir storage/mtgtop8.py).

    Attendu : « 1442 decks », puis une ligne par archétype (classe hover_tr) avec un lien
    « archetype?a=… » (son nom) et sa part en ‰ (« 58.3 ‰ »). Les noms sont décodés (« &#039; » → « ' »).

    Renvoie (MetaPage, []) ou (None, erreurs) : total ou archétypes introuvables, ligne incomplète,
    somme des ‰ trop loin de 1000. Une page inattendue n'est jamais lue comme un méta vide.
    """
    total_match = TOTAL_RE.search(page)
    if total_match is None:
        return None, ["page MTGTop8 inattendue : nombre total de decks introuvable (le site a peut-être changé)"]
    total = int(total_match.group(1))

    entries = []
    errors = []
    for number, row in enumerate(page.split(ROW_MARK)[1:], start=1):
        name_match = NAME_RE.search(row)
        permille_match = PERMILLE_RE.search(row)
        if name_match is None or permille_match is None:
            missing = "nom" if name_match is None else "part en ‰"
            errors.append(f"page MTGTop8 inattendue : archétype n°{number} sans {missing}")
            continue
        name = " ".join(html.unescape(re.sub(r"<[^>]+>", "", name_match.group(1))).split())
        entries.append((name, float(permille_match.group(1))))

    if not entries and not errors:
        errors.append("page MTGTop8 inattendue : aucun archétype trouvé (le site a peut-être changé)")
    if errors:
        return None, errors

    permille_sum = sum(permille for _, permille in entries)
    if abs(permille_sum - PERMILLE_TOTAL) > PERMILLE_TOLERANCE:
        return None, [f"page MTGTop8 inattendue : la somme des parts vaut {permille_sum:.1f} ‰ au lieu d'environ 1000 ‰"]
    return MetaPage(total, entries), []
