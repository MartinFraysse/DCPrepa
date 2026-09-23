# Journal de sessions

> Fichier de persistance entre les sessions Claude Code.
> Lu automatiquement au démarrage (hook `SessionStart`) et mis à jour par Claude après chaque tâche significative.
> Entrées les plus récentes en haut, une idée par puce.

## 🔜 Prochaines étapes
- Compléter `tournament.yaml` de RelicFest 2026 (banlist).
- Remplir `data/oppos.yaml` au fil des decks adverses rencontrés.
- Logiciel, import de l'inbox : `__init__.py` + `requirements.txt`, choisir pytest/unittest, puis `parse_games` (découpe sur `/`, appelle `_parse_bo`) dans `domain/games.py`.
- Ensuite : validation d'un bloc, lecture inbox, normalisation oppo, games.csv, service d'import, CLI ; puis stats et import MTGTop8.

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
- Champ `date` retiré des versions de deck par l'utilisateur (non pertinent) ; liste v1 revérifiée : 100 cartes.
- `tournament.yaml` : date du tournoi renseignée, `31/10/2026`.
- Décision : dates saisies en `JJ/MM/AAAA` (`tournament.yaml`, `inbox.yaml`, `games.csv`) ; identifiants (`match_id`, fichiers `meta/`) gardés en `AAAA-MM-JJ`.
- Ouvert : format des dates dans `docs/README.md` (ADR), `CLAUDE.md` et le journal, laissés en `AAAA-MM-JJ`.
- Créé `data/templates/tournament/` : modèle de dossier de tournoi (tournament.yaml vierge, inbox, oppos, games.csv, meta/, stats/, `decks/_modele.yaml`, README d'emploi).
- Décision : les modèles vivent dans `data/templates/` ; l'import ignorera ce dossier et les fichiers `decks/_*.yaml`.
- README : section « Organisation du dépôt » mise à jour avec `data/templates/`.
- `oppos.yaml` sorti du tournoi et du modèle → `data/oppos.yaml`, commun à tous les tournois ; `meta/` reste par tournoi (le méta change).
- Stats voulues, par deck : winrate général (toutes versions), par oppo (matchup), OTP/OTD, par source (paper/cockatrice/mtgo), par match BO3, matchup × OTP/OTD ; poids des oppos dans le méta ; winrate attendu au tournoi ; matchups non testés ; taille d'échantillon.
- Décision : pas de winrate par version, mais un indicateur d'écart = winrate de la version − moyenne simple des winrates des autres versions (ex. +3).
- Décision : winrate général du deck calculé en réunissant toutes les parties, toutes versions confondues.
- Rapports-modèles de stats créés (valeurs `—`, servent de spec au logiciel) : `stats/README.md`, `synthese.md`, `terra-midrange.md` dans RelicFest ; `README.md`, `synthese.md`, `_modele-deck.md` dans le template.
- Conventions : winrate `55 % (66/120)`, nul = non gagnée, ⚠️ sous 10 parties.
- Décision : matchup non testé = oppo du top 10 du méta avec moins de 10 BO3 et moins de 30 parties (un seul seuil atteint suffit) ; tableau de `synthese.md` mis à jour (rang méta, BO3 joués).
- Format `meta/` fixé : `oppo,decks,poids` ; période choisie à l'import ; stats sur le fichier le plus récent (README `meta/` mis à jour, tournoi + template).
- Self-play exclu du winrate général, affiché dans une section « Self-play » du rapport deck.
- Une partie est toujours W ou L (D retiré de l'inbox) ; seul un BO3 peut être nul (1-1), compté comme match non gagné.
- Validation à l'import : bloc invalide laissé dans l'inbox avec message ; oppo inconnu gardé avec avertissement.
- Liste `decks` retirée de `tournament.yaml` (tournoi + template), le `statut` des fiches suffit.
- Reporté : noms MTGTop8 dans `data/oppos.yaml` (plus tard, pas urgent).
- claude_doc : nouvelle sous-section « Statistiques » (`04-reference/statistiques.md`, page absente de `docs/`).
- Début du logiciel, branche `feat/import-inbox` : l'utilisateur écrit le code lui-même, Claude guide et relit.
- Architecture en couches décidée : `src/dcprepa/{domain,storage,services,interfaces}` + `src/tests/` ; arborescence créée par l'utilisateur (dossiers vides pour l'instant).
- `src/README.md` rempli (stack Python 3.13 + PyYAML, organisation, installation, conventions) ; README racine : organisation mise à jour.
- Convention : tout le code en anglais (fichiers, fonctions, variables, constantes) ; clés de `data/` inchangées, messages utilisateur en français.
- Venv recréé à la racine (`.venv/`), `src/requirements.txt` (pyyaml).
- `src/dcprepa/domain/games.py` : `_parse_bo(text)` écrite par l'utilisateur (un BO « OTP W, OTD L… ») ; valide format, position, résultat, max 3 games, BO déjà terminé à 2 victoires ; 26 cas testés OK.
- `_parse_bo` renvoie toujours `(games, errors)` ; exclusifs : s'il y a des erreurs, `games` est vide (jamais de games partielles).
- Ouvert : pytest ou unittest ; `__init__.py` et `requirements.txt` à créer.
