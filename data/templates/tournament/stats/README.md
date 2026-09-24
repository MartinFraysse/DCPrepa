# stats

Rapports de statistiques générés par le logiciel (`python -m dcprepa stats <slug>`, depuis `src/`) à partir de `games.csv`, `decks/`, `meta/` et `data/oppos.yaml`.
Fichiers Markdown, lisibles directement sur GitHub : ne pas les modifier à la main, ils sont réécrits à chaque génération.

- `synthese.md` : tous les decks côte à côte avec leur winrate attendu, winrate de chaque deck contre les oppos du méta, matchups non testés.
- `<deck>.md` : détail d'un deck (même nom que sa fiche dans `decks/`).
- `_modele-deck.md` (modèle uniquement) : structure d'un rapport de deck, pour référence ; à supprimer de la copie.

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
- Winrate attendu au tournoi : moyenne des winrates du deck contre les oppos du méta (top 20), pondérée par leur poids.
  Seuls comptent les oppos joués (au moins une game ; au moins un BO3 pour le winrate BO3) : le reste du méta est ignoré, les poids retenus sont ramenés à 100 %.
  Calculé avec le méta papier et avec le méta général, par game et par BO3. Ex. `49.8 % (16.2 % du méta)` : la part du méta sur laquelle il repose ;
  ⚠️ sous 30 % du méta ; `—` si le deck n'a joué aucun oppo du méta.
- Statut d'un deck (fiche) : `retenu`, `envisage` ou `ecarte` ; seuls les decks retenus ou envisagés ont une colonne dans le tableau Méta de la synthèse
  et des matchups non testés.
- Matchups non testés : oppos du top 10 du méta papier contre lesquels un deck retenu ou envisagé a moins de 10 BO3 **et** moins de 30 games
  (un seul des deux seuils atteint suffit pour considérer le matchup testé).
- Écart d'une version : son winrate − la moyenne simple des winrates des autres versions, en points (ex. `+3.2`), calculé à part pour les games et pour les BO3.
- Meilleure version contre un oppo : la version au meilleur winrate contre lui, et son écart au winrate du matchup
  (toutes versions), en points (ex. `v2 (+12)`), par game et par BO3 ; ⚠️ si elle a moins de 10 games (ou BO3) contre l'oppo ;
  `—` si une seule version l'a joué. À égalité : la version avec le plus de games, puis la plus récente.
- ⚠️ : moins de 10 games (ou moins de 10 BO3), chiffre peu fiable.
- `—` : pas de donnée ou pas assez de games pour afficher le chiffre.
