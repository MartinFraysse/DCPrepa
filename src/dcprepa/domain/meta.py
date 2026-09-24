from dataclasses import dataclass

from dcprepa.domain.mtgtop8 import MetaPage
from dcprepa.domain.names import name_key

PERMILLE_TOTAL = 1000
META_TOP = 20


@dataclass(frozen=True)
class MetaRow:
    """Une ligne de meta/…/<type>.csv : oppo (nom de référence), decks (estimés), poids en % (exact)."""

    oppo: str
    decks: int
    weight: float


def build_meta(page: MetaPage, oppo_index: dict[str, str], top: int = META_TOP) -> tuple[list[MetaRow], list[str]]:
    """Transforme une répartition MTGTop8 en lignes de méta, avec les noms de data/oppos.yaml.

    - nom : ramené à son nom de référence par oppo_index (build_oppo_index) ; absent, il est gardé tel quel ;
    - fusion : plusieurs archétypes ramenés au même oppo voient leurs ‰ additionnés ;
    - poids : ‰ / 10, à 2 décimales (ex. 58.1 ‰ → 5.81 %) : exact, MTGTop8 donne les ‰ au dixième ;
    - decks : ‰ × total / 1000, arrondi à l'entier le plus proche (MTGTop8 n'affiche pas ce nombre) ;
    - top : seuls les `top` premiers oppos (20 par défaut) sont gardés, avec leur poids réel dans le méta complet.

    Renvoie (lignes triées par poids décroissant puis par nom, noms absents de oppos.yaml parmi les lignes gardées).
    """
    permilles = {}
    unknown = set()
    for name, permille in page.entries:
        reference = oppo_index.get(name_key(name))
        if reference is None:
            reference = name
            unknown.add(name)
        permilles[reference] = permilles.get(reference, 0.0) + permille

    rows = [
        MetaRow(oppo, int(permille * page.total / PERMILLE_TOTAL + 0.5), round(permille / 10, 2))
        for oppo, permille in permilles.items()
    ]
    rows.sort(key=lambda row: (-row.weight, row.oppo.lower()))
    rows = rows[:top]
    return rows, [row.oppo for row in rows if row.oppo in unknown]


def propose_oppos(names: list[str], oppo_index: dict[str, str]) -> dict[str, list[str]]:
    """Entrées à ajouter dans data/oppos.yaml pour des noms MTGTop8 inconnus, sur le modèle des entrées existantes.

    Nom court (avant la virgule) en référence, nom complet en variante : « Phelia, Exuberant Shepherd » →
    {"Phelia": ["Phelia, Exuberant Shepherd"]}. Sans virgule (« Tifa Lockhart », « Partner WUR »), ou si le nom
    court est déjà pris (dans oppos.yaml ou par un ajout précédent), le nom complet devient la référence, sans variante.
    Un nom déjà connu ou déjà proposé est ignoré.
    """
    taken = dict(oppo_index)
    entries = {}
    for name in names:
        if name_key(name) in taken:
            continue
        short = name.split(",", 1)[0].strip()
        if short != name and short and name_key(short) not in taken:
            reference, variants = short, [name]
        else:
            reference, variants = name, []
        entries[reference] = variants
        taken[name_key(reference)] = reference
        taken[name_key(name)] = reference
    return entries
