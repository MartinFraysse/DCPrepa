# meta

Instantanés du méta Duel Commander importés depuis MTGTop8 par `python -m dcprepa meta <slug>` (depuis `src/`).
Un dossier par import, nommé à sa date (`AAAA-MM-JJ`) ; les imports précédents sont gardés pour pouvoir vérifier :

```
meta/
├── 2026-09-10/
│   ├── general.csv      MTGTop8 « Last 2 Months » (paper + MTGO)
│   └── paper.csv        MTGTop8 « Paper Last 2 Months »
└── 2026-09-24/          ← le plus récent : lu par les stats
    ├── general.csv
    └── paper.csv
```

Colonnes des deux fichiers : `oppo,decks,poids`

- `oppo` : nom de référence de `data/oppos.yaml` (les oppos inconnus y sont ajoutés à l'import) ;
- `decks` : nombre de listes de ce deck sur la période, estimé à partir de sa part (MTGTop8 n'affiche que la part) ;
- `poids` : part du méta, en %, point décimal (ex. `5.81`).

Seuls les 20 premiers oppos de chaque méta sont gardés, avec leur poids réel (le top 20 ne fait pas 100 %).
Les stats utilisent le dossier le plus récent : matchups triés par poids papier, colonnes « Poids papier » et « Poids général ».
Deux imports le même jour : les fichiers du jour sont remplacés ; les autres dates ne sont jamais modifiées.
