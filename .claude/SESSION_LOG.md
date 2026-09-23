# Journal de sessions

> Fichier de persistance entre les sessions Claude Code.
> Lu automatiquement au démarrage (hook `SessionStart`) et mis à jour par Claude après chaque tâche significative.
> Entrées les plus récentes en haut, une idée par puce.

## 🔜 Prochaines étapes
- Compléter `tournament.yaml` de RelicFest 2026 (banlist).
- Remplir `data/oppos.yaml` au fil des decks adverses rencontrés.
- Valider le brouillon de doc de l'import, puis PR `feat/import-inbox` → `main`.
- Import de l'inbox utilisable (`python -m dcprepa import relicfest-2026`) : premier vrai import à faire.
- Logiciel, suite : stats (rapports Markdown dans `stats/`) ; plus tard vraie CLI, import MTGTop8, GUI.

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
- Commits sur `feat/import-inbox` : `412c2a6` (architecture) et `194371a` (`_parse_bo`) ; les scopes sont écrits `<…>` au lieu de `(…)`.
- `_parse_bo` renommée `_parse_games` (games d'un BO) ; `parse_bos` (champ `parties` entier, découpe sur `/`, erreurs préfixées « BO n : ») codée par Claude à la demande ; docstrings ajoutées ; 9 cas testés OK.
- `_parse_games` reprise par Claude pour la cohérence avec `parse_bos` : noms explicites (`chunks`, `parts`, `position`, `result`, `wins`, `losses`), constante `WINS_TO_END_BO`, messages préfixés « game n : » ; 25 cas testés, comportement inchangé.
- pytest retenu (`src/requirements-dev.txt`) ; tests dans `src/tests/domain/test_games.py` (écrits par Claude à la demande, `parametrize`) : 30 tests OK via `python -m pytest` depuis `src/`.
- `domain/validation.py` : `validate_block(block, decks)` codée par Claude à la demande ; `decks` = {deck: [versions]} fourni par l'appelant ; renvoie la liste de toutes les erreurs (champs, date, source, deck, version, parties via `parse_bos`) ; tests pytest dans `src/tests/domain/test_validation.py` (50 cas) ; suite complète : 80 tests OK.
- `storage/decks.py` : `load_decks(tournament_dir)` → `(decks, errors)` (option A : fiche invalide écartée et signalée) ; codée par Claude ; tests `src/tests/storage/test_decks.py` avec `tmp_path` (27 cas, dont le modèle réel du template) ; suite : 107 tests OK ; lit bien RelicFest → {terra-midrange: [v1]}.
- Décision (importante pour l'utilisateur) : import de l'inbox **tout ou rien** ; une seule erreur → rien n'est importé, aucun fichier modifié, toutes les erreurs affichées. Remplace « bloc invalide laissé dans l'inbox ».
- Commentaire d'en-tête des deux `inbox.yaml` mis à jour avec la règle tout ou rien.
- `storage/inbox.py` : `read_inbox(path)` → `(blocks, errors)`, découpe sur `---` et lit bloc par bloc (toutes les erreurs YAML d'un coup, avec n° de bloc et de ligne) ; codée par Claude ; tests `src/tests/storage/test_inbox.py` (25 cas) ; suite : 132 tests OK.
- `storage/inbox.py` : `clear_inbox(path)` (garde l'en-tête, écriture atomique via `.tmp`) ; 9 tests de plus ; suite : 141 tests OK ; `storage/inbox.py` terminé.
- Décisions : oppo inconnu = avertissement (import quand même) ; comparaison souple (majuscules, espaces).
- `storage/oppos.py::load_oppos` + `domain/oppos.py::build_oppo_index/normalize_oppo` codés par Claude ; 34 tests ; suite : 175 tests OK ; `.claude_avancement_import_inbox.md` mis à jour.
- Décision (par défaut, option conseillée) : la note du bloc est recopiée sur chaque ligne de `games.csv`.
- `storage/games.py` (`read_match_ids`, `append_rows`) + `domain/rows.py` (`next_match_id`, `build_rows`) codés par Claude ; 29 tests ; suite : 204 tests OK.
- `services/import_inbox.py` : `import_inbox` + `ImportReport` codés par Claude ; 12 tests d'intégration (mini-dépôt dans `tmp_path`, dont une copie du vrai modèle) ; suite : 216 tests OK.
- Décision : pas de vraie CLI pour l'instant ; lancement minimal `src/dcprepa/__main__.py` → `python -m dcprepa <tournoi>` depuis `src/`.
- Essayé à la main sur une copie de `data/` (scratchpad) : bloc invalide → rien modifié ; corrigé → 6 games dans games.csv, inbox vidée, relance → « Inbox vide » ; vrai RelicFest : inbox vide, rien modifié. Pas de test pytest pour `__main__.py`.
- `src/README.md` : point d'entrée et commande de lancement remplis.
- `data/test_tournoi/` (vide, créé par l'utilisateur) déplacé en `data/tournaments/test_tournoi/` (sinon introuvable par la commande) et rempli : tournament.yaml, deck `test-deck` (v1, v2), games.csv (en-tête), inbox avec 3 blocs (paper, mtgo, self-play cockatrice) ; import essayé sur une copie : 3 blocs, 6 matchs, 12 games, 2 avertissements d'oppo. README : organisation mise à jour.
- `data/oppos.yaml` prérempli : Ragavan, Kess, Tymna/Thrasios (+ variantes) ; l'exemple commenté remplacé par une aide courte ; lu et indexé sans erreur (10 formes).
- `__main__.py` : choix du module (`python -m dcprepa import <tournoi>`), table `MODULES` (un service = une entrée) ; seul `import` existe, les futurs modules seront ajoutés au besoin ; essayé à la main (usage, module/tournoi inconnus, import sur copie).
- Appellations de decks : `decks/_alias.yaml` par tournoi (choix de l'utilisateur, plutôt qu'un champ dans chaque fiche) ; deck reconnu par fichier, `name:` ou variante, ramené au nom du fichier ; inconnu = erreur listant les decks ; self-play résolu aussi (inconnu = avertissement).
- Code : `domain/names.py` (index souple partagé, extrait de `oppos.py`), `domain/decks.py`, `storage/decks.py::load_deck_aliases`, service mis à jour ; message « deck inconnu » avec decks disponibles ; `_alias.yaml` ajouté au modèle, à RelicFest (Terra, Terra mid) et à test_tournoi ; 44 tests de plus → 260 OK ; essayé sur une copie de test_tournoi.
- Commits `a7c4f62` (lancement par module) et `653532a` (appellations de decks) ; `test_tournoi` commité comme exemple.
- Brouillon de doc demandé : `docs/.claude_brouillon-import-inbox.md` (fonctionnement de l'import étape par étape, schémas) ; à valider puis à déplacer en `docs/03-architecture/import-inbox.md` (+ `index.md` du chapitre).
- Décision : `match_id` en `JJ/MM/AAAA-NN` (remplace `AAAA-MM-JJ-NN`) ; date normalisée avec ses zéros ; code (`domain/rows.py`), tests, commentaires des 3 inbox, `test_tournoi/games.csv` (19 identifiants convertis) et docs mis à jour ; 261 tests OK. Noms de fichiers `meta/` restent `AAAA-MM-JJ.csv` (`/` impossible).
- Brouillon de doc : schémas réalignés (flèches ASCII, emojis en fin de ligne), « tout ou rien » retiré, section « Lire » simplifiée.
- Brouillon de doc de l'import validé par l'utilisateur ; second brouillon demandé : `docs/.claude_brouillon-donnees.md` (organisation de `data/`, commun vs par tournoi, modèle, fichiers un par un, choix des formats, conventions, trajet des données ; dossiers d'exemple, pas RelicFest ni test_tournoi).
- Précision de l'utilisateur : à terme, le logiciel remplira tous les fichiers de saisie (en plus de la main) ; consigne : la doc décrit le logiciel comme terminé (pas de « aujourd'hui / à terme / à venir »), appliquée aux deux brouillons ; « qui écrit quoi » = saisie (logiciel ou main) / produits (logiciel uniquement).
- Créé à la demande `docs/.claude_avancement_import_inbox.md` (renommé par l'utilisateur) : schémas de l'avancement (vue d'ensemble, fichiers par couche, flux d'import, trajet d'un bloc, reste à faire) ; README : organisation mise à jour.
