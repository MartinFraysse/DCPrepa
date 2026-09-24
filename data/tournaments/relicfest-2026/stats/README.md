# stats

Rapports de statistiques générés par le logiciel (`python -m dcprepa stats <slug>`, depuis `src/`) à partir de `games.csv`, `decks/`, `meta/` et `data/oppos.yaml`.
Fichiers Markdown, lisibles directement sur GitHub : ne pas les modifier à la main, ils sont réécrits à chaque génération.

- `synthese.md` : tous les decks côte à côte, poids des oppos dans le méta, winrate attendu, matchups non testés.
- `<deck>.md` : détail d'un deck (même nom que sa fiche dans `decks/`).

Conventions :

- Winrate au format `55 % (66/120)` ou `12.2 % (11/90)` : victoires / games (ou BO3 gagnés / BO3 joués), au dixième, décimale nulle omise.
- Deux winrates distincts, côte à côte dans les tableaux :
  - par game : toutes les games, BO1 et games des BO3 ;
  - par BO3 : un BO de 2 ou 3 games, gagné à 2 victoires ; un BO1 (une seule game) n'y compte pas.
  Ex. BO3 `WLW`, `WW`, `LWL`, `LWL` + BO1 `W W W W` : BO3 = `50 % (2/4)`, games = `66.7 % (10/15)`.
  Une game est toujours W ou L ; seul un BO3 peut être nul (1-1), il compte alors comme un BO3 non gagné.
- Self-play (oppo = `deck@version`) : exclu du winrate général et des autres stats, affiché à part.
- Poids papier / Poids général : part de l'oppo dans le méta papier / général des 2 derniers mois (MTGTop8, top 20,
  dossier `meta/AAAA-MM-JJ/` le plus récent) ; matchups triés par poids papier ; `—` si l'oppo n'est pas dans ce méta.
- Winrate général : toutes les games réunies, toutes versions confondues.
- Écart d'une version : son winrate − la moyenne simple des winrates des autres versions, en points (ex. `+3.2`), calculé à part pour les games et pour les BO3.
- Meilleure version contre un oppo : la version au meilleur winrate contre lui, et son écart au winrate du matchup
  (toutes versions), en points (ex. `v2 (+12)`), par game et par BO3 ; ⚠️ si elle a moins de 10 games (ou BO3) contre l'oppo ;
  `—` si une seule version l'a joué. À égalité : la version avec le plus de games, puis la plus récente.
- ⚠️ : moins de 10 games (ou moins de 10 BO3), chiffre peu fiable.
- `—` : pas de donnée ou pas assez de games pour afficher le chiffre.
