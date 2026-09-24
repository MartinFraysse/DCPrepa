# Journal de sessions

> Fichier de persistance entre les sessions Claude Code.
> Lu automatiquement au démarrage (hook `SessionStart`) et mis à jour par Claude après chaque tâche significative.
> Entrées les plus récentes en haut, une idée par puce.

## 🔜 Prochaines étapes
- `feat/stats-synthese` : relire et commiter l'étape 5 (`synthese.md`), puis étape 6 (service : écrire `synthese.md`, nom du tournoi, avertissement statut inconnu).
- Premier vrai import de l'inbox (`python -m dcprepa import relicfest-2026`).
- Compléter `tournament.yaml` de RelicFest 2026 (banlist) ; remplir `data/oppos.yaml` au fil des decks adverses rencontrés.
- Après `feat/stats-synthese` : vraie CLI, puis GUI.

## 🗓️ Historique

<!-- Ajouter les entrées ici, la plus récente en haut :
### AAAA-MM-JJ — titre
- ce qui a été fait
- fichiers touchés
- décisions prises
- problèmes ouverts
-->

### 2026-09-24 — Synthèse du tournoi : plan d'action
- Étape 1 (décisions) : calcul sur les données disponibles seulement ; ⚠️ si couverture < 30 % ; `—` sans oppo joué ; section Général validée ;
  tableau Decks en méta papier seulement ; tableau Méta = union des top 20, une colonne par deck non écarté ; Claude code et explique, l'utilisateur supervise.
- Couverture affichée (`49.8 % (16.2 % du méta)`) ; étape 1 ✅.
- Étape 2 codée : `src/dcprepa/domain/synthese.py` (`ExpectedWinrate`, `expected_winrate`) + 10 tests (`src/tests/domain/test_synthese.py`) ; suite : 482 OK.
- `.venv/` absent de la racine : tests lancés dans un venv du scratchpad.
- Feuille de route : `feat/stats-synthese` 🔄.
- Étape 2 commitée et poussée par l'utilisateur (`e691515`).
- Étape 3 codée : `untested_matchups` + `UntestedMatchup` dans `domain/synthese.py`, 11 tests ; suite : 493 OK ; statut vide ou mal écrit → deck ignoré, avec un avertissement dans le bilan de `stats` (décision utilisateur, étape 6).
- Étape 3 commitée et poussée par l'utilisateur (`3f5f21c`).
- Étape 4 codée : section Général du rapport de deck (`domain/report.py`, `_modele-deck.md`), tests adaptés ; suite : 493 OK ; essai sur une copie de `test_tournoi` OK.
- `docs/03-architecture/stats.md` décrit encore l'ancienne section Général : signalé, à mettre à jour à l'étape 7.
- Étape 4 commitée et poussée par l'utilisateur (`fa83d22`), rapports de `test_tournoi` régénérés avec `stats`.
- Étape 5 codée : `src/dcprepa/domain/synthese_report.py` (`render_synthese`), modèle `synthese.md`, 5 tests ; suite : 498 OK ; rendu sur `test_tournoi` vérifié.
- Décisions utilisateur : winrate attendu calculé avec le méta papier ET général, par game ET par BO3, sur les seuls oppos joués du top 20 (poids ramenés à 100 %) ;
  matchups non testés : top 10 papier, decks `envisage` / `retenu`, seuils 10 BO3 / 30 games.
- Plan créé à partir du modèle : `docs/.claude_plan_stats_synthese.md` (7 étapes ; pas de nouvelle commande, `stats` écrit aussi `synthese.md`).
- Ouverts : couverture affichée (« 16.2 % du méta »), ⚠️ si faible, colonnes des tableaux Decks et Méta, section Général du rapport de deck.
- README : organisation de `docs/` (plan ajouté) ; feuille de route : décisions notées ; branche `feat/stats-synthese` à créer par l'utilisateur.

### 2026-09-24 — Import du méta : plan d'action
- Branche `feat/import-meta` créée par l'utilisateur (depuis `main` après la PR #4).
- Plan créé à la demande à partir du modèle : `docs/.claude_plan_import_meta.md` (8 étapes : décisions, récupérer, lire, construire, écrire, service, commande, essai).
- Architecture proposée : `storage/mtgtop8.py` (seul accès réseau), `domain/mtgtop8.py` (HTML → decks), `domain/meta.py` (noms, fusion, poids), `storage/meta.py::write_meta`, `services/import_meta.py` ; tests sans réseau (pages enregistrées).
- Décisions ouvertes : source MTGTop8, dépendances, période, noms inconnus, fichier du jour existant.
- Feuille de route : import-meta 🔄 ; README : organisation de `docs/` mise à jour.
- Étape 1, analyse de MTGTop8 (outil browse + curl) : liste chargée en JS, mais fragment `cEDH_decks?f=EDH&show=pop&meta=<id>…` lisible sans navigateur ;
  total de decks + une ligne par archétype avec sa part en ‰ ; 159 archétypes sur 2 mois, pas de pagination ; partenaires regroupés par couleurs (« Partner WUR ») ;
  `meta=` inconnu → toute la base (à valider) ; decks par archétype estimés (‰ × total) ; pas de robots.txt ni d'API ; urllib suffit. Détails dans le plan.
- Décisions utilisateur : période en option (`--periode`, 2 mois par défaut, noms courts validés) ; noms inconnus gardés tels quels + un avertissement récapitulatif ;
  partenaires « Partner XYZ » rapprochés d'un duo par variante dans `oppos.yaml` ; fichier du jour remplacé.
- Décisions par défaut (dans le plan) : fusion = ‰ additionnés ; poids = ‰ / 10 ; decks = ‰ × total / 1000 arrondi ; erreur réseau / HTML = rien écrit ; Claude code.
- Ajouts utilisateur : importer à chaque fois le méta général 2 mois ET papier 2 mois ; un dossier par import `meta/AAAA-MM-JJ/` avec `general.csv` et `paper.csv` ;
  imports précédents gardés (historique trié par date) ; option `--periode` retirée.
- Stats à adapter (étape 5b ajoutée au plan) : dossier daté le plus récent, colonnes « Poids papier » et « Poids général », tri par poids papier.
- Doc publiée (`stats.md`, `donnees.md`) à mettre à jour en fin de branche (nouveau rangement de `meta/`).
- Étape 1 ✅ ; prochaine : étape 2 (`storage/mtgtop8.py`, seul accès réseau).
- Étape 2 codée : `src/dcprepa/storage/mtgtop8.py` (`META_IDS`, `meta_url`, `fetch_meta_page` avec `opener` injectable, timeout 20 s, User-Agent, erreurs HTTP / réseau / délai / page vide sans exception).
- 12 tests (`src/tests/storage/test_mtgtop8.py`, sans réseau) ; suite : 394 OK ; essai réel : général 1447 decks, papier 1309 decks.
- Page MTGTop8 gardée en mémoire seulement ; décision utilisateur : ne pas stocker les pages brutes dans `meta/`.
- Étape 2 commitée et poussée (`f5142e7`). Étape 3 codée : `src/dcprepa/domain/mtgtop8.py` (`MetaPage`, `parse_meta_page` : total + parts ‰, erreurs si page inattendue, somme ± 20 ‰).
- Fixtures réelles enregistrées : `src/tests/fixtures/mtgtop8_general.html` et `mtgtop8_paper.html` ; 14 tests ; suite : 408 OK ; `src/README.md` : `fixtures/` ajouté à l'organisation.
- Étape 3 commitée et poussée (`ada5155`). Étape 4 codée : `src/dcprepa/domain/meta.py` (`MetaRow`, `build_meta` : noms de référence, fusion des ‰, poids ‰/10 à 2 décimales, decks estimés, tri, liste des inconnus).
- 16 tests (`src/tests/domain/test_meta.py`) ; suite : 424 OK. Constat : avec le `oppos.yaml` actuel, tous les noms du méta sont inconnus (Ragavan, Kess, Tymna/Thrasios absents des 2 derniers mois).
- Demandes utilisateur : garder seulement le top 20 de chaque méta (poids réels, pas ramenés à 100 %) ; ajouter automatiquement à `data/oppos.yaml`
  les oppos du top absents (nom court avant la virgule + nom complet en variante, sinon nom complet).
- Code : `domain/meta.py` (`META_TOP`, coupe dans `build_meta`, `propose_oppos`) ; `storage/oppos.py::append_oppos` (ajout en fin de fichier, commentaire daté, guillemets si besoin, `.tmp`).
- Tests : 12 + 5 ; suite : 441 OK. Essai sur une copie de `oppos.yaml` avec les vraies pages : 20 oppos ajoutés, relus sans erreur, plus aucun inconnu ; top 20 ≈ 63 % du méta.
- Étape 4 commitée (`7a69b49`). Étape 5 codée : `storage/meta.py::write_meta` (dossier daté, `.tmp`, poids sans zéro inutile) et `read_meta` extrait de `load_latest_meta` (réutilisé en 5b).
- 10 tests (aller-retour, format du poids, remplacement du jour, autres dates intactes) ; suite : 451 OK.
- Étape 5 commitée (`985bcc0`). Étape 5b codée : `load_latest_meta` lit le dossier daté le plus récent (`general.csv` + `paper.csv` requis) ;
  `MatchupStats.weight_paper` / `weight_general`, tri papier puis général ; rapport : colonnes « Poids papier » + « Poids général », en-tête `meta/<date>/`.
- Données : modèle `_modele-deck.md`, conventions `stats/README.md` ×3, `meta/README.md` ×3 réécrits, en-tête `synthese.md` ; méta de test_tournoi converti (`meta/2026-10-25/`) ; rapports régénérés.
- Suite : 457 OK. Reste signalé : pages publiées `stats.md` / `donnees.md` (étape 8) ; `synthese.md` une seule colonne de poids (feat/stats-synthese).
- Étape 6 codée : `src/dcprepa/services/import_meta.py` (`MetaReport`, `import_meta` : oppos.yaml → 2 pages → top 20 → nouveaux oppos → méta reconstruit → écriture méta puis oppos.yaml ; tout ou rien).
- 11 tests d'intégration (`src/tests/services/test_import_meta.py`, fixtures à la place du réseau) ; suite : 468 OK.
- Étape 7 codée : `run_meta` + `MODULES["meta"]` (`__main__.py`) ; bilan ✅ / 📝 oppos ajoutés / ❌ ; 4 tests ; suite : 472 OK ; `src/README.md` : commande `meta`.
- Essai réel (réseau) sur une copie : OK (général 20 oppos / 1447 decks, papier 20 / 1309, 20 oppos ajoutés) ; `data/` non touché.
- ⚠️ Constat : le méta fictif de test_tournoi est daté 2026-10-25 (futur) → il reste « le plus récent » ; à supprimer pour tester le vrai import.
- ⚠️ `meta` modifie le vrai `data/oppos.yaml` (commun à tous les tournois), même lancé sur test_tournoi.
- Test utilisateur : méta fictif 2026-10-25 supprimé, `meta test_tournoi` lancé → `meta/2026-09-24/` + 20 oppos dans `data/oppos.yaml` ; Ragavan, Kess, Tymna/Thrasios retirés par l'utilisateur.
- À la demande : `test_tournoi/games.csv` régénéré avec les 20 oppos du méta (tirage pondéré par le poids général, graine fixe, script dans le scratchpad) :
  418 games de septembre 2026 (winota 221, sythis 171, kinnan 26), self-play gardé, plus de lignes test-deck ; `stats` relancé : poids papier / général remplis ; suite : 472 OK.
- Étape 8 : nouvelle page publiée `docs/03-architecture/import-meta.md` (source MTGTop8, commande, étapes, noms ajoutés à oppos.yaml, historique, code) + index du chapitre ;
  `stats.md` et `donnees.md` mis à jour (dossier daté, Poids papier / général, commande `meta`) ; README : organisation de `docs/`.
- Page publiée directement (pas de brouillon) car `stats.md` et `donnees.md` y renvoient déjà ; liens relatifs vérifiés.
- Reste : commit de tout (données de test comprises), puis PR `feat/import-meta` → `main` (texte préparé).
- Demande utilisateur : passer par un brouillon comme pour `stats.md` → page déplacée en `docs/.claude_brouillon-import-meta.md` ;
  retirée de l'index du chapitre et du README ; liens de `stats.md` / `donnees.md` remplacés par du texte simple, à remettre à la publication.
- Oubli signalé par l'utilisateur, corrigé : l'ajout automatique des oppos par `meta` est décrit dans `donnees.md` (section `oppos.yaml`) et dans l'en-tête de `data/oppos.yaml`.
- Brouillon validé par l'utilisateur et publié : `docs/03-architecture/import-meta.md` ; index du chapitre, liens depuis `stats.md` et `donnees.md` (×2), README mis à jour.
- PR #5 `feat/import-meta` fusionnée dans `main` ; feuille de route : import-meta ✅ (#5), stats-synthese 🔜.

### 2026-09-24 — Stats d'un deck : brique winrate (étape 3)
- Étape 2 validée par l'utilisateur.
- Créé `src/dcprepa/domain/winrate.py` : `Winrate(wins, total)` figé ; `rate` (exact), `reliable` (≥ 10) ; `str` → `55 % (66/120)`, `⚠️ 33.3 % (1/3)`, `—`.
- Décision utilisateur : pas d'arrondi à l'entier ; affichage au dixième, décimale nulle omise (`55 %`, `12.2 %`), via `format_percent()` (0,05 au-dessus, signe géré pour l'écart).
- Décision : winrate par partie (toutes les games, BO1 + games des BO3) et winrate BO3 (matchs de 2-3 games) toujours distincts ; seuil ⚠️ BO3 = 10 matchs.
- Rapports-modèles modifiés (`_modele-deck.md`, `relicfest-2026/stats/terra-midrange.md`) : Versions → Parties / Écart (parties) / Matchs BO3 / Écart BO3 ; Source en lignes avec winrate parties + BO3 ; Position reste par partie (note ajoutée).
- Conventions des 3 `stats/README.md` (template, RelicFest, test_tournoi) : format au dixième, définition des deux winrates avec exemple, écart `+3.2` par type, ⚠️ BO3 en matchs.
- 27 tests dans `src/tests/domain/test_winrate.py` ; suite complète : 310 OK (venv `.venv/` à la racine).
- Correction : le venv est bien à la racine, `src/README.md` est juste ; le point « venv dans `src/.venv` » était faux, retiré.
- Plan mis à jour à la demande : étape 3 ✅ (nouveau format), étape 4 🔄 avec les colonnes BO3.
- Étape 4 codée : `src/dcprepa/domain/stats.py` → `compute_deck_stats(games, deck, versions)` renvoie `DeckStats` (overall, versions, positions, sources, matchups, self_play).
- `Record(games, bo3)` porte les deux winrates partout ; `bo3_matches` = games regroupées par `match_id`, 2 games ou plus ; gagné = 2 victoires.
- Écarts de version parties et BO3 via `version_gaps` (versions sans donnée hors moyenne) ; version jouée absente de la fiche ajoutée à la fin.
- Matchups triés par parties décroissantes puis nom ; OTP / OTD à `None` sous 10 parties ; self-play : mêmes calculs, à part.
- 15 tests (`test_stats.py`, dont l'exemple des conventions) ; suite : 325 OK ; essai sur test_tournoi vérifié à la main (10/17 parties, 3/5 BO3, écart v1 +30 / BO3 +66.7).
- Décision utilisateur : ⚠️ gardés tels quels dans les rapports (convention inchangée).
- Étapes 3 et 4 commitées et poussées par l'utilisateur.
- Étape 5 codée : `src/dcprepa/domain/report.py` → `render_deck_report(deck, sheet, stats, generated)` ; structure du modèle, date `JJ/MM/AAAA`, écart `+3.2` / `-30` / `0`, compteur 0 → `—`, tableau vide → ligne de `—`.
- Sans méta : phrase des matchups « Triés par nombre de parties (pas encore de méta) » au lieu de « Triés par poids dans le méta » (seul écart au modèle) ; « Poids méta » et « Winrate attendu » à `—`.
- 11 tests (`test_report.py`, dont deck vide = `_modele-deck.md` avec en-tête rempli) ; suite : 336 OK ; rapport de test_tournoi relu.
- Demande utilisateur : détecter la présence d'un méta pour trier les matchups par poids ; ajouté au plan en étape 5b.
- Créé `src/dcprepa/storage/meta.py` : `load_latest_meta(tournament_dir)` → (fichier, poids par oppo, erreurs) ; fichier le plus récent d'après le nom `AAAA-MM-JJ.csv`, autres fichiers ignorés ; pas de méta = pas d'erreur.
- Décision : méta invalide (en-tête, colonnes, oppo vide ou en double, decks non entier, poids non numérique ou négatif) = erreur bloquante, rien ne sera écrit.
- `compute_deck_stats(..., weights)` : `MatchupStats.weight` ; tri par poids ↓, oppos hors méta à la fin (parties ↓, puis nom) ; self-play sans poids.
- `render_deck_report(..., meta_file)` : en-tête `meta/<fichier>`, phrase « Triés par poids dans le méta », colonne « Poids méta » (`12.5 %`) ; sans méta, comportement précédent.
- Correspondance oppo méta ↔ games.csv au nom exact (les deux sont normalisés via `data/oppos.yaml`).
- 21 tests ajoutés (`test_meta.py` 17, `test_stats.py` 2, `test_report.py` 2) ; suite : 357 OK.
- Étapes 5 et 5b commitées par l'utilisateur.
- Étape 6 codée : `src/dcprepa/storage/stats.py::write_report` (dossier créé si besoin, `.tmp` puis remplacement, LF).
- `src/dcprepa/services/stats.py::generate_stats(tournament_dir, generated=None)` → `StatsReport(decks, games, meta, errors, warnings)` ; tout ou rien : erreur games.csv / fiche / méta → rien écrit.
- Avertissements : deck de games.csv sans fiche (pas de rapport), version jouée absente de la fiche (ajoutée au tableau Versions).
- 12 tests (`tests/storage/test_stats.py` 4, `tests/services/test_stats.py` 8, dont test_tournoi copié) ; suite : 369 OK.
- Étape 6 commitée et poussée par l'utilisateur.
- Étape 7 codée : `run_stats` + `MODULES["stats"]` dans `src/dcprepa/__main__.py` ; bilan ✅ (rapports, games, méta ou non), ❌ erreurs, ⚠️ avertissements ; code de sortie 0 / 1.
- 4 tests (`src/tests/test_main.py`, sur copie de test_tournoi) ; suite : 373 OK ; `python -m dcprepa` liste bien le module `stats`.
- Pas encore lancé sur les vrais dossiers de `data/` (écrit des fichiers : étape 8).
- `src/README.md` : commande `stats` ajoutée dans « Commandes ».
- Étape 7 commitée par l'utilisateur ; étape 8 lancée : jeu d'essai dans `data/tournaments/test_tournoi/`, à la demande.
- 3 fiches deck fictives ajoutées : `winota-aggro` (v1-v3, v3 jamais jouée), `sythis-enchant` (v1-v2), `kinnan-combo` (v1, peu de parties) ; `test-deck` gardé.
- `games.csv` : 19 lignes d'origine gardées + 404 générées (script à graine fixe dans le scratchpad, pas dans le dépôt) ; 11 oppos, self-play, 3 sources, BO1 et BO3.
- `meta/2026-10-25.csv` fictif ajouté (9 oppos, dont Kraum/Tymna jamais joué ; Kinnan, Ertai, Tevesh Szat absents du méta).
- Oppos fictifs non ajoutés à `data/oppos.yaml` (fichier commun réel) : inutile pour les stats.
- Tests détachés du contenu de test_tournoi (`test_main.py` sur mini-tournoi, `test_test_tournoi` générique, `test_meta` adapté) ; suite : 373 OK.
- Contrôle indépendant (csv brut) : winota 109/196 parties, 43/73 BO3 ; sythis 42/123, 10/40 ; kinnan 4/15, 1/5 ; test-deck 30/58, 10/19.
- L'utilisateur a retiré les 19 lignes d'origine et `decks/test-deck.yaml` ; l'en-tête de `games.csv` est parti avec → erreur « en-tête inattendu ». En-tête remis par Claude ; 404 games lues sans erreur.
- Reste : 41 games `test-deck` sans fiche → avertissement « deck sans fiche » au lancement (à trancher).
- Décision utilisateur : vocabulaire des joueurs dans tout le projet — « game » (une manche) et « BO3 » / « BO1 », plus de « partie » ni de « match » ; `match_id` gardé.
- Format des données changé : colonne `partie` → `game` dans `games.csv` (template, RelicFest, test_tournoi) ; champ d'inbox `parties:` → `games:` (code, validation, 3 inbox.yaml).
- Textes : rapports (« Par game », « Par BO3 », « Games », « Écart (games) », « BO3 », « Winrate (games) », « Winrate BO3 »), messages CLI (« 3 BO, 6 game(s) »), docstrings, tests.
- Aussi mis à jour à la demande : `data/` (modèles, README de stats, synthese.md, terra-midrange.md), `README.md`, `src/README.md`, `docs/03-architecture/donnees.md` et `import-inbox.md`, `.claude_doc.md` (glossaire : Game, BO1/BO3), plan.
- Non touchés : historique du journal, `CLAUDE.md` (« une partie du projet » = un morceau), rapports déjà générés de test_tournoi (réécrits au prochain `stats`).
- Suite : 373 OK.
- Décision utilisateur : le tableau Versions affiche aussi les winrates (revient sur « pas de winrate par version ») ;
  colonnes Version · Games · Winrate (games) · Écart (games) · BO3 · Winrate BO3 · Écart BO3 ; phrase d'intro = définition de l'écart.
- Touchés : `domain/report.py`, `_modele-deck.md`, `relicfest-2026/stats/terra-midrange.md`, `test_report.py` ; suite : 373 OK.
- Étape 8 finalisée à la demande : `stats` lancé sur test_tournoi (3 rapports, 404 games, avertissement test-deck sans fiche) et RelicFest (terra-midrange.md réécrit, vide).
- Rapports test_tournoi = contrôle indépendant (winota 109/196, 43/73 ; sythis 42/123, 10/40 ; kinnan 4/15, 1/5).
- README : `stats/README.md` ×3 citent la commande ; README du template : copie de `_modele-deck.md` remplacée par la commande ; README racine : test_tournoi sert aussi aux stats.
- Reste pour clore la branche : commits, puis PR `feat/stats-deck` → `main` (texte préparé) ; page de doc officielle reportée (sur demande).
- Créés à la demande : `docs/.claude_plan_modele.md` (modèle de plan de branche, structure du plan des stats) et
  `docs/.claude_feuille_de_route.md` (branches faites / en cours / à faire : import-meta, stats-synthese, cli, gui, docs ; tâches de données).
- README : organisation de `docs/` mise à jour ; plan des stats renvoie à la feuille de route.
- `.claude/CLAUDE.md` modifié à la demande : `docs/.claude_feuille_de_route.md` ajouté aux fichiers que Claude tient à jour seul ; nouvelle section « Feuille de route » (quand, comment, plan de branche à partir du modèle).
- Brouillon de doc demandé : `docs/.claude_brouillon-stats.md` (« Rapports de stats », sur le modèle de `import-inbox.md`) :
  principes, fichiers, vocabulaire game / BO1 / BO3 et règles, lecture d'un winrate, commande, rapport section par section,
  méta, étapes du service, trajet d'un deck (exemple chiffré vérifié avec le vrai code), erreurs, protection, code. À valider puis publier.
- `docs/03-architecture/import-inbox.md` : 4 schémas réalignés (décalés par le remplacement partie → game).
- README : organisation de `docs/` mise à jour (brouillon).
- L'utilisateur a commité `src/` seulement (`428aa76`) ; `data/`, `docs/`, README, CLAUDE.md restent à commiter.
- Demande : colonne « meilleure version » par matchup. Décisions utilisateur : écart au winrate du matchup (même ligne), par game ET par BO3, ⚠️ si la version a < 10 games / BO3 contre l'oppo.
- Code : `BestVersion` + `best_version()` dans `domain/stats.py` (≥ 2 versions jouées, égalité → plus de games puis plus récente) ; `MatchupStats.best_games` / `best_bo3` ; `report.py` : colonnes « Meilleure version (games) » et « Meilleure version BO3 » à côté de chaque winrate, phrase d'explication ; self-play inchangé.
- Modèle `_modele-deck.md`, conventions des 3 `stats/README.md`, brouillon de doc, claude_doc, plan, feuille de route mis à jour ; rapports test_tournoi et RelicFest régénérés.
- 9 tests ajoutés ; suite : 382 OK.
- Push fait par l'utilisateur. Brouillon publié à la demande : `docs/.claude_brouillon-stats.md` → `docs/03-architecture/stats.md` ;
  `03-architecture/index.md` : lien ajouté ; README : organisation de `docs/` mise à jour ; feuille de route et plan : doc des stats ✅.
- PR #4 `feat/stats-deck` fusionnée dans `main` ; `docs/.claude_plan_stats_deck.md` supprimé par l'utilisateur (branche finie) ; feuille de route : stats-deck ✅ (#4), import-meta 🔜.

### 2026-09-23 — Stats d'un deck : plan d'action
- Branche `feat/stats-deck` créée par l'utilisateur ; périmètre : `stats/<deck>.md` seulement (synthèse et méta reportés à d'autres branches).
- Plan créé à la demande : `docs/.claude_plan_stats_deck.md` (objectif, chemin en 8 étapes, fichiers par couche, statuts ✅/⬜).
- Étape 1 tranchée : BO3 = match de 2 ou 3 games, 1 game = BO1 (compte par partie, pas en BO3) ; matchups triés par nombre de parties tant qu'il n'y a pas de méta ;
  nouvelle fonction `load_deck_sheets()` (import intact) ; rapport généré même sans partie ; Claude code, l'utilisateur relit étape par étape.
- README : organisation de `docs/` mise à jour (plan ajouté, `.claude_avancement_import_inbox.md` absent du disque retiré de l'arbre).
- Étape 2 codée par Claude : `storage/games.py::read_games` (en-tête, 10 colonnes, OTP/OTD, W/L, n° de ligne) et `storage/decks.py::load_deck_sheets` (versions via `load_decks`, + name/commandant/statut).
- 22 tests ajoutés (`test_games.py`, `test_decks.py`) ; suite : 283 OK ; lancée dans un venv du scratchpad car `.venv/` absent de la racine.
- Venv recréé par l'utilisateur dans `src/.venv` (ignoré par git) ; `src/README.md` dit encore « `.venv/` à la racine » : correction proposée, pas encore faite.
- Commits proposés : `feat(stats): lire games.csv et les fiches deck complètes` + `docs(stats): plan d'action…` ; branche poussée par l'utilisateur (`git push -u origin feat/stats-deck`).
- Pause : étape 2 livrée, en attente de relecture ; reprise à l'étape 3 (brique winrate).

### 2026-09-23 — Documentation officielle : chapitre Architecture
- Brouillons publiés dans `docs/03-architecture/` : `donnees.md` et `import-inbox.md`, section « Voir aussi » retirée des deux.
- `docs/03-architecture/index.md` créé (présentation du chapitre et liens vers les deux pages).
- Dans `donnees.md`, la mention de la page « Import de l'inbox » devient un lien relatif.
- Brouillons `docs/.claude_brouillon-*.md` supprimés ; README : organisation mise à jour.
- `donnees.md` : schéma « Le trajet des données » jugé peu clair, remplacé par deux étapes (import, puis stats) et une légende saisie / produits.

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
