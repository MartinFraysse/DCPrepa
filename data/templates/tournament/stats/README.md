# stats

Rapports de statistiques générés par le logiciel à partir de `games.csv`, `decks/`, `meta/` et `data/oppos.yaml`.
Fichiers Markdown, lisibles directement sur GitHub : ne pas les modifier à la main, ils sont réécrits à chaque génération.

- `synthese.md` : tous les decks côte à côte, poids des oppos dans le méta, winrate attendu, matchups non testés.
- `<deck>.md` : détail d'un deck (même nom que sa fiche dans `decks/`).
- `_modele-deck.md` (modèle uniquement) : à copier en `<deck>.md` pour chaque deck, puis supprimer.

Conventions :

- Winrate au format `55 % (66/120)` : victoires / parties (ou matchs pour le BO3).
  Une partie est toujours W ou L ; seul un BO3 peut être nul (1-1), il compte alors comme un match non gagné.
- Self-play (oppo = `deck@version`) : exclu du winrate général et des autres stats, affiché à part.
- Winrate général : toutes les parties réunies, toutes versions confondues.
- Écart d'une version : son winrate − la moyenne simple des winrates des autres versions, en points (ex. `+3`).
- ⚠️ : moins de 10 parties, chiffre peu fiable.
- `—` : pas de donnée ou pas assez de parties pour afficher le chiffre.
