# Journal de sessions

> Fichier de persistance entre les sessions Claude Code.
> Lu automatiquement au démarrage (hook `SessionStart`) et mis à jour par Claude après chaque tâche significative.
> Entrées les plus récentes en haut, une idée par puce.

## 🔜 Prochaines étapes
- Renseigner la date de la v1 de Terra Midrange.
- Compléter `tournament.yaml` de RelicFest 2026 (date, banlist).
- Remplir `oppos.yaml` au fil des decks adverses rencontrés.
- Plus tard : le logiciel (import de l'inbox, stats, rapports Markdown, import MTGTop8).

## 🗓️ Historique

<!-- Ajouter les entrées ici, la plus récente en haut :
### AAAA-MM-JJ — titre
- ce qui a été fait
- fichiers touchés
- décisions prises
- problèmes ouverts
-->

### 2026-09-23 — Cadrage du projet et format des données
- But : outil générique de préparation de tournois Duel Commander (suivi d'entraînement, stats méta, tests de decks).
- Données en fichiers texte dans git : `data/tournaments/<slug>/`, un dossier par tournoi ; decks et versions rangés dans le tournoi.
- Créés dans `data/tournaments/relicfest-2026/` : `tournament.yaml`, `games.csv` (en-tête seul), `inbox.yaml` (saisie mobile via GitHub).
- Format inbox validé avec PyYAML (exemple lu correctement, deux blocs à la suite).
- Décision : le logiciel (CLI ou interface) est reporté ; on fixe d'abord le format des données.
- README : section « Organisation du dépôt » mise à jour avec `data/`.
- Simplification : adversaire = `oppo` (son deck/commandant) ; nom du joueur et archétype retirés de l'inbox et de `games.csv`.
- `ressenti` (note 1-5) retiré, `notes` renommé `note/ressenti` ; inbox : un bloc par session, matchs séparés par `/` dans `parties`.
- Format deck créé : `decks/terra-midrange.yaml` (premier deck envisagé, liste v1 à coller) ; ajouté à `decks` dans `tournament.yaml`.
- Champ `commandant` ajouté aux fiches deck ; liste v1 de Terra Midrange collée par l'utilisateur et vérifiée (100 cartes, format OK).
- Ajouts : `oppos.yaml` (noms de référence + variantes), dossiers `meta/` et `stats/` (avec README) ; oppo self-play = `deck@version` ; `match_id` généré à l'import ; statut deck sans accents.
- Pas de sideboard en Duel Commander : rien à prévoir dans les fiches deck.
