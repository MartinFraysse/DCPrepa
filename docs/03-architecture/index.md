# Architecture

> Comment DCPrepa est construit : ses données, son code et leurs mécanismes. Pour comprendre le projet ou le faire évoluer.

## Pages du chapitre

- [Organisation des données](donnees.md) : le dossier `data/`, chaque fichier, les formats et les conventions.
- [Import de l'inbox](import-inbox.md) : comment une session saisie sur le téléphone devient des lignes de `games.csv`.
- [Import du méta](import-meta.md) : comment le méta Duel Commander de MTGTop8 devient `meta/AAAA-MM-JJ/`, et complète `data/oppos.yaml`.
- [Rapports de stats](stats.md) : comment les games de `games.csv` deviennent un rapport par deck, `stats/<deck>.md`, et la synthèse du tournoi avec le winrate attendu, `stats/synthese.md`.
