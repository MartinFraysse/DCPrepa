# Modèle de dossier de tournoi

Point de départ d'un nouveau tournoi. Le plus simple : le logiciel fait les étapes 1 à 4 (depuis `src/`) :

```
python -m dcprepa tournament-create "RelicFest 2026" --date 31/10/2026     # étapes 1 à 3, slug déduit du nom
python -m dcprepa deck-create relicfest-2026 "Terra Midrange" --liste terra.txt   # étape 4, un deck à la fois
```

À la main :

1. Copier ce dossier sous `data/tournaments/<slug>/` (slug en minuscules, ex. `relicfest-2026`) :
   `cp -r data/templates/tournament data/tournaments/<slug>`
2. Supprimer ce `README.md` de la copie.
3. Remplir `tournament.yaml` (nom, slug, date au format JJ/MM/AAAA, lieu, banlist).
4. Pour chaque deck envisagé : copier `decks/_modele.yaml` en `decks/<deck>.yaml` et le remplir
   (son champ `statut` suffit à le suivre, pas de liste à tenir ailleurs). Supprimer `decks/_modele.yaml` une fois inutile.
   Appellations acceptées dans l'inbox (« Terra », « Terra mid »…) : les ajouter dans `decks/_alias.yaml`.
5. `games.csv`, `inbox.yaml`, `meta/` et `stats/` sont prêts : rien à modifier au départ (supprimer `stats/_modele-deck.md`).
6. Les rapports `stats/<deck>.md` sont générés, un par fiche deck : `python -m dcprepa stats <slug>` (depuis `src/`).
