# meta

Instantanés du méta importés depuis MTGTop8 : un fichier CSV par import, nommé `AAAA-MM-JJ.csv` (date de l'import).

Colonnes : `oppo,decks,poids`

- `oppo` : nom du deck tel qu'affiché par MTGTop8 (ramené au nom de référence via `data/oppos.yaml`) ;
- `decks` : nombre de listes de ce deck sur la période ;
- `poids` : part du méta, en %.

La période couverte (par ex. les 2 derniers mois) est choisie à l'import. Les stats utilisent le fichier le plus récent.
