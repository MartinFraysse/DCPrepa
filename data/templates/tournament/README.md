# Modèle de dossier de tournoi

Point de départ pour préparer un nouveau tournoi à la main.

1. Copier ce dossier sous `data/tournaments/<slug>/` (slug en minuscules, ex. `relicfest-2026`) :
   `cp -r data/templates/tournament data/tournaments/<slug>`
2. Supprimer ce `README.md` de la copie.
3. Remplir `tournament.yaml` (nom, slug, date au format JJ/MM/AAAA, lieu, banlist).
4. Pour chaque deck envisagé : copier `decks/_modele.yaml` en `decks/<deck>.yaml` et le remplir
   (son champ `statut` suffit à le suivre, pas de liste à tenir ailleurs). Supprimer `decks/_modele.yaml` une fois inutile.
   Tant que le logiciel ne génère pas les stats : copier aussi `stats/_modele-deck.md` en `stats/<deck>.md`.
5. `games.csv`, `inbox.yaml`, `meta/` et `stats/` sont prêts : rien à modifier au départ.
