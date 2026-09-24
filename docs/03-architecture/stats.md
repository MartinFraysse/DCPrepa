# Rapports de stats

> Comment les games de `games.csv` deviennent un rapport par deck, `stats/<deck>.md` : les fichiers, la commande,
> les règles de calcul, chaque section du rapport et les fonctions appelées. Pour lire les rapports ou faire évoluer leur calcul.

## Contexte

Préparer un tournoi, c'est choisir un deck et savoir contre quoi il tient. Les games jouées s'accumulent dans `games.csv`
(voir [Import de l'inbox](import-inbox.md)) ; une commande en tire, pour chaque deck, un **rapport Markdown**
lisible directement sur GitHub : winrate général, par version, par position, par source, par oppo.

Quatre principes guident les stats :

- 🛡️ **Une erreur bloque tout** : si `games.csv`, une fiche deck ou le méta est invalide, aucun rapport n'est écrit.
  On corrige, on relance.
- 📏 **Deux winrates, jamais mélangés** : le winrate **par game** et le winrate **par BO3** sont toujours calculés et affichés séparément.
- ⚠️ **Un petit échantillon se voit** : un chiffre calculé sur moins de 10 games (ou 10 BO3) porte un ⚠️.
- 🤖 **Les rapports sont générés** : on ne les modifie jamais à la main, ils sont réécrits à chaque lancement.

## Vue d'ensemble

```
  📊 games.csv            ⚙️ logiciel                              📈 rapports
┌──────────────────┐    ┌────────────────────────────────────┐    ┌─────────────────────────┐
│ 1 ligne par game │    │ python -m dcprepa stats <tournoi>  │    │ stats/<deck>.md         │
│ deck, oppo,      │ ─> │                                    │ ─> │ un rapport par fiche    │
│ position, W/L…   │    │ lire, vérifier, calculer, écrire   │    │ deck, même sans game    │
└──────────────────┘    └────────────────────────────────────┘    └─────────────────────────┘
         ▲                         ▲
  🃏 decks/<deck>.yaml      🌍 meta/AAAA-MM-JJ.csv
  nom, commandant,          facultatif : poids de chaque
  statut, versions          oppo dans le méta
```

## Les fichiers en jeu

Tous vivent dans le dossier du tournoi, `data/tournaments/<tournoi>/`.

```
data/tournaments/<tournoi>/
├── games.csv                   les games jouées, une ligne par game      📊
├── decks/
│   └── <deck>.yaml             une fiche par deck                        🃏
├── meta/
│   └── AAAA-MM-JJ.csv          instantanés du méta (facultatifs)         🌍
└── stats/
    ├── README.md               conventions de lecture des rapports       📖
    └── <deck>.md               un rapport par fiche deck (généré)        📈
```

| Fichier | Rôle dans les stats | Lu | Écrit |
|---|---|---|---|
| `games.csv` | les games : deck, version, oppo, position, résultat, `match_id` | ✅ | — |
| `decks/<deck>.yaml` | les decks à analyser : `name`, `commandant`, `statut`, versions | ✅ | — |
| `meta/AAAA-MM-JJ.csv` | le plus récent donne le poids de chaque oppo (facultatif) | ✅ | — |
| `stats/<deck>.md` | le rapport du deck | — | réécrit à chaque lancement |

Les fichiers de `decks/` qui commencent par `_` (`_alias.yaml`, `_modele.yaml`) ne sont pas des fiches deck : ils n'ont pas de rapport.

## 📏 Le vocabulaire et les règles de calcul

### Game, BO1, BO3

| Terme | Sens | Dans `games.csv` |
|---|---|---|
| 🎮 **Game** | une manche, à la fin de laquelle un joueur gagne : toujours W ou L | une ligne |
| 1️⃣ **BO1** | un BO d'une seule game | un `match_id` qui n'a qu'une ligne |
| 3️⃣ **BO3** | best of 3 games : jusqu'à 3 games, gagné à 2 victoires | un `match_id` qui a 2 ou 3 lignes |

Un BO3 est **gagné** avec 2 victoires. Un BO3 à 1-1 (arrêté après deux games) compte comme un BO3 **non gagné**.

### Les deux winrates

```
winrate par game  =  games gagnées  /  games jouées       (toutes : BO1 et games des BO3)
winrate par BO3   =  BO3 gagnés     /  BO3 joués          (les BO1 n'y comptent pas)
```

Exemple : 4 BO3 et 4 BO1.

```
BO3   W L W   ✅ gagné          games : 2 W / 3
BO3   W W     ✅ gagné          games : 2 W / 2
BO3   L W L   ❌ perdu          games : 1 W / 3
BO3   L W L   ❌ perdu          games : 1 W / 3
BO1   W  W  W  W                games : 4 W / 4
      ─────────────────────────────────────────
      par BO3  :  2 / 4   →  50 %
      par game : 10 / 15  →  66.7 %
```

### Ce qui est compté

- **Toutes versions réunies** : le winrate général d'un deck réunit les games de toutes ses versions.
- **Self-play à part** : une game contre un de ses propres decks (oppo `deck@version`) n'entre dans **aucune** stat,
  sauf la section « Self-play » du rapport.
- **Autres decks ignorés** : le rapport d'un deck ne lit que les lignes de `games.csv` dont le `deck` est le sien.

## 🔢 Lire un winrate

```
  ⚠️ 66.7 % (10/15)
  │   │       │  └── total : games jouées (ou BO3 joués)
  │   │       └───── victoires
  │   └───────────── pourcentage au dixième, décimale nulle omise
  └───────────────── moins de 10 games (ou 10 BO3) : chiffre peu fiable
```

| Affiché | Signification |
|---|---|
| `55 % (66/120)` | 66 victoires sur 120, fiable (10 ou plus) |
| `12.2 % (11/90)` | au dixième près : pas d'arrondi à l'entier |
| `⚠️ 33.3 % (1/3)` | moins de 10 : à prendre avec prudence |
| `—` | aucune donnée, ou pas assez de games pour afficher le chiffre |
| `+33.3` / `-30` / `0` | un écart, en points (voir « Versions » et « Matchups ») |
| `v2 (+12)` | meilleure version contre un oppo, et son écart au winrate du matchup (voir « Matchups ») |

Le pourcentage est arrondi au dixième le plus proche, 0,05 au-dessus (12,25 → `12.3`).
Le seuil ⚠️ porte sur le total affiché : 10 games pour un winrate par game, 10 BO3 pour un winrate par BO3.

## ▶️ Lancer la commande

Depuis `src/`, venv activé :

```
python -m dcprepa stats relicfest-2026
```

Issues possibles :

```
✅ 3 rapport(s) écrit(s) à partir de 404 game(s) : kinnan-combo, sythis-enchant, winota-aggro.
   Pas de méta : matchups triés par nombre de games.
```

```
✅ 3 rapport(s) écrit(s) à partir de 404 game(s) : kinnan-combo, sythis-enchant, winota-aggro.
   Méta : meta/2026-10-25.csv (matchups triés par poids).
⚠️  Avertissements :
  - games.csv : deck sans fiche : atraxa (41 game(s)) → pas de rapport
  - winota-aggro : version jouée absente de la fiche : v9
```

```
❌ Stats annulées, aucun rapport écrit. Erreurs à corriger :
  - games.csv : ligne 5 : position inconnue (OTP ou OTD) : OTX
  - meta/2026-10-25.csv : ligne 3 : poids attendu en nombre positif (ex. 12.5) : beaucoup
```

| Code de sortie | Signification |
|---|---|
| `0` | rapports écrits (avec ou sans avertissements) |
| `1` | erreurs : aucun rapport écrit |
| `2` | mauvaise utilisation (module ou tournoi inconnu) |

## 📄 Le rapport, section par section

Chaque `stats/<deck>.md` suit la même structure, fixée par le modèle `data/templates/tournament/stats/_modele-deck.md`.
Les extraits ci-dessous viennent d'un petit exemple, déroulé en entier plus bas (« Le trajet d'un deck »).

### 🏷️ En-tête

```
# Terra Midrange

> Généré le 05/10/2026 à partir de `games.csv`, `decks/terra-midrange.yaml` et `meta/—.csv`. Ne pas modifier à la main.

- **Commandant :** Terra, Magical Adept
- **Statut :** retenu
- **Dernière version :** v2
```

- Titre : le champ `name` de la fiche, ou le nom du fichier s'il est vide.
- Date de génération au format JJ/MM/AAAA ; fichier méta utilisé, ou `meta/—.csv` sans méta.
- Dernière version : la dernière de la liste `versions` de la fiche.

### 📊 Général

| | Winrate |
|---|---|
| Par game | ⚠️ 50 % (3/6) |
| Par BO3 | ⚠️ 50 % (1/2) |
| Winrate attendu au tournoi | — |

Toutes les games du deck, toutes versions réunies, self-play exclu.
Le winrate attendu au tournoi relève de la synthèse du tournoi (`stats/synthese.md`) : il reste à `—` dans le rapport du deck.

### 🔢 Versions

| Version | Games | Winrate (games) | Écart (games) | BO3 | Winrate BO3 | Écart BO3 |
|---|---|---|---|---|---|---|
| v1 | 3 | ⚠️ 66.7 % (2/3) | +33.3 | 1 | ⚠️ 100 % (1/1) | +100 |
| v2 | 3 | ⚠️ 33.3 % (1/3) | -33.3 | 1 | ⚠️ 0 % (0/1) | -100 |

- Une ligne par version de la fiche, dans son ordre, même jamais jouée (`—`).
  Une version jouée mais absente de la fiche est ajoutée à la fin, avec un ⚠️ avertissement.
- L'**écart** dit si une version fait mieux ou moins bien que les autres, calculé à part pour les games et pour les BO3 :

```
écart de v2  =  winrate de v2  −  moyenne simple des winrates des autres versions

ex.  v1 : 53 %    v2 : 57 %    v3 : 55 %
     écart de v2  =  57 − (53 + 55) / 2  =  57 − 54  =  +3
```

- Moyenne **simple** : chaque version pèse autant, quel que soit son nombre de games.
- Pas d'écart (`—`) si la version n'a pas de game, ou si aucune autre version n'en a.

### 🎲 Position

| OTP | OTD |
|---|---|
| ⚠️ 66.7 % (2/3) | ⚠️ 33.3 % (1/3) |

Par game seulement : dans un BO3, la position change d'une game à l'autre, un BO3 n'a donc pas de position.

### 🌐 Source

| Source | Winrate (games) | Winrate BO3 |
|---|---|---|
| Paper | ⚠️ 66.7 % (2/3) | ⚠️ 100 % (1/1) |
| Cockatrice | — | — |
| MTGO | ⚠️ 33.3 % (1/3) | ⚠️ 0 % (0/1) |

Les trois sources sont toujours affichées, dans cet ordre, même sans game.

### ⚔️ Matchups

Extrait d'un deck plus joué (Winota Aggro, deux versions, avec méta) :

| Oppo | Poids méta | Winrate (games) | Meilleure version (games) | Winrate BO3 | Meilleure version BO3 | OTP | OTD |
|---|---|---|---|---|---|---|---|
| Asmo | 18.3 % | 50 % (22/44) | v2 (+7.7) | 50 % (8/16) | v2 (+10) | 60.9 % (14/23) | 38.1 % (8/21) |
| Kess | 12.2 % | 69.2 % (27/39) | v2 (+20.8) | 80 % (12/15) | ⚠️ v2 (+20) | 78.6 % (11/14) | 64 % (16/25) |
| Magda | 6.5 % | 54.5 % (6/11) | ⚠️ v1 (+5.5) | ⚠️ 50 % (2/4) | ⚠️ v2 (0) | ⚠️ 50 % (3/6) | ⚠️ 60 % (3/5) |
| Ertai | — | 62.5 % (10/16) | ⚠️ v2 (+12.5) | ⚠️ 66.7 % (4/6) | ⚠️ v2 (+33.3) | ⚠️ 66.7 % (4/6) | 60 % (6/10) |

- Une ligne par oppo rencontré (self-play exclu).
- **OTP / OTD** : affichés seulement à partir de 10 games contre l'oppo ; en dessous, `—`.
- **Ordre et poids** : dépendent de la présence d'un méta (voir « Le méta » ci-dessous).
- **Meilleure version** : la version du deck qui gagne le plus contre cet oppo, à côté du winrate qu'elle dépasse.
  Calculée deux fois, par game et par BO3, chacune comparée à son propre winrate :

```
Kess, par game       winrate du matchup (toutes versions)   69.2 %  (27/39)
                     v1 contre Kess                         47.4 %  (9/19)
                     v2 contre Kess                         90 %    (18/20)   ← meilleure
                     ────────────────────────────────────────────────────
                     affiché :  v2 (+20.8)      90 − 69.2 = +20.8 points
```

- L'écart se mesure au winrate **du matchup** (la case d'à côté), pas au winrate général du deck.
  La meilleure version étant au-dessus de la moyenne des versions, l'écart est positif, ou `0` si toutes font pareil.
- ⚠️ si la meilleure version a moins de 10 games (ou 10 BO3) contre l'oppo : elle peut devoir sa place à peu de games.
- `—` si une seule version a joué l'oppo : il n'y a rien à comparer.
- À égalité de winrate : la version avec le plus de games (ou de BO3) contre l'oppo, puis la plus récente.

### 🪞 Self-play

| Oppo | Winrate (games) | Winrate BO3 | OTP | OTD |
|---|---|---|---|---|
| terra-midrange@v1 | ⚠️ 100 % (2/2) | ⚠️ 100 % (1/1) | — | — |

Les games contre ses propres decks, avec les mêmes calculs que les matchups, mais sans poids méta.
Elles ne comptent dans aucune autre section.

## 🌍 Le méta

Le méta dit quels decks adverses on croisera au tournoi, et avec quel poids. Il vit dans `meta/`, un fichier par import :

```
meta/2026-10-25.csv
oppo,decks,poids
Asmo,42,18.3
Ragavan,35,15.2
Kess,28,12.2
```

Les stats utilisent le fichier **le plus récent**, choisi d'après la date de son nom (`AAAA-MM-JJ.csv`) ;
les autres fichiers du dossier (`README.md`, CSV mal nommé) sont ignorés. Le méta change la section Matchups :

```
        sans méta                                     avec méta
───────────────────────────────────    ───────────────────────────────────────────
en-tête   meta/—.csv                   en-tête   meta/2026-10-25.csv
phrase    Triés par nombre de games    phrase    Triés par poids dans le méta
Poids     —                            Poids     14.5 %  (— si l'oppo n'y est pas)
ordre     games ↓, puis nom            ordre     poids ↓, puis oppos hors méta
                                                 (games ↓, puis nom)
```

- Un oppo du méta jamais rencontré n'apparaît pas : le tableau ne liste que les oppos joués.
- Oppos du méta et de `games.csv` sont rapprochés par leur **nom exact** : les deux passent par les noms de référence de `data/oppos.yaml`.
- Pas de méta (dossier vide ou absent) n'est pas une erreur. Un méta **invalide** en est une : aucun rapport n'est écrit.

| Contrôle du méta | Refusé si… |
|---|---|
| en-tête | pas exactement `oppo,decks,poids` |
| colonnes | pas 3 valeurs sur la ligne |
| oppo | vide, ou déjà présent plus haut |
| decks | pas un nombre entier |
| poids | pas un nombre positif avec un point décimal (`12.5`, pas `12,5` ni `12%`) |

## ⚙️ Ce qui se passe, étape par étape

`dcprepa/__main__.py` retrouve le dossier du tournoi, appelle le service `generate_stats()`
(`services/stats.py`), puis affiche le bilan qu'il renvoie. Tout le travail est dans le service :

```
python -m dcprepa stats <tournoi>
        │
  1. Lire les fichiers           games.csv, fiches deck, méta le plus récent    📂
        │
  2. Une erreur quelque part ?
        │
        ├── oui ──  rien n'est écrit                                           🚫
        │
        └── non ──  3. Avertissements   deck sans fiche, version hors fiche     ⚠️
                          │
                    4. Calculer et rédiger TOUS les rapports, en mémoire       🧮
                          │
                    5. Écrire stats/<deck>.md, un par fiche                    💾

  Dans tous les cas : bilan affiché   ✅ écrits   ❌ erreurs   ⚠️ avertissements
```

### 1. Lire les fichiers

- `read_games()` : toutes les lignes de `games.csv`. Vérifie l'en-tête, le nombre de colonnes, `OTP`/`OTD` et `W`/`L` ;
  chaque erreur donne son numéro de ligne.
- `load_deck_sheets()` : chaque fiche deck, avec ses versions (mêmes règles que l'import) et ses champs `name`, `commandant`, `statut`.
- `load_latest_meta()` : le fichier méta le plus récent et le poids de chaque oppo, ou rien s'il n'y a pas de méta.

### 2. Une erreur quelque part ?

S'il y a **au moins une erreur**, le service s'arrête et renvoie la liste complète : aucun rapport n'est écrit,
les anciens restent en place. On corrige tout d'un coup, puis on relance.

### 3. Les avertissements

L'écriture se fait quand même, mais le bilan signale :

- un deck présent dans `games.csv` **sans fiche** : ses games ne sont dans aucun rapport ;
- une version jouée **absente de la fiche** : elle apparaît quand même dans le tableau Versions.

### 4. Calculer et rédiger

Pour chaque fiche deck :

1. `compute_deck_stats()` (`domain/stats.py`) fait tous les calculs et renvoie un `DeckStats` :

```
games.csv (toutes les lignes)
   │
   ├── garder les games du deck
   │
   ├── oppo « deck@version » ? ─── oui ──> self-play                      🪞
   │
   └── le reste ──┬── général                  record()                    📊
                  ├── versions + écarts        record(), version_gaps()    🔢
                  ├── position OTP / OTD       par game                    🎲
                  ├── paper / cockatrice / mtgo  record()                  🌐
                  └── par oppo                 record(), tri, poids méta,  ⚔️
                                               best_version()

record(games)  =  Record(games = winrate par game, bo3 = winrate par BO3)
                   │
                   └── bo3_matches() : games regroupées par match_id,
                       gardées si 2 ou 3 games ; gagné = 2 victoires
```

2. `render_deck_report()` (`domain/report.py`) transforme ce `DeckStats` en texte Markdown, section par section.

Tous les rapports sont rédigés **en mémoire** avant la première écriture.

### 5. Écrire

`write_report()` écrit chaque `stats/<deck>.md`, en remplaçant l'ancien. Un rapport est écrit **pour chaque fiche**,
même sans aucune game : il est alors rempli de `—`.

## 🔎 Le trajet d'un deck

Les lignes de `games.csv` du deck `terra-midrange` (colonnes utiles seulement) :

```
match_id        game  source      version  oppo                position  resultat
02/10/2026-01   1     paper       v1       Ragavan             OTP       W   ┐
02/10/2026-01   2     paper       v1       Ragavan             OTD       L   ├─ BO3 2-1 ✅
02/10/2026-01   3     paper       v1       Ragavan             OTP       W   ┘
03/10/2026-01   1     mtgo        v2       Kess                OTD       W   ── BO1
03/10/2026-02   1     mtgo        v2       Kess                OTP       L   ┐
03/10/2026-02   2     mtgo        v2       Kess                OTD       L   ┘─ BO3 0-2 ❌
04/10/2026-01   1     cockatrice  v2       terra-midrange@v1   OTP       W   ┐
04/10/2026-01   2     cockatrice  v2       terra-midrange@v1   OTD       W   ┘─ self-play 🪞
```

Ce que le rapport en tire :

```
self-play mis à part           2 games, 1 BO3                       ──> section Self-play
reste                          6 games (3 W), 2 BO3 (1 gagné)

Général     par game   W L W · W · L L            =  3 / 6  →  ⚠️ 50 %
            par BO3    ✅ ❌                       =  1 / 2  →  ⚠️ 50 %

Versions    v1   2 / 3 = 66.7 %   BO3 1 / 1 = 100 %   écart  +33.3  /  +100
            v2   1 / 3 = 33.3 %   BO3 0 / 1 =   0 %   écart  -33.3  /  -100

Position    OTP   W W L   =  2 / 3        OTD   L W L   =  1 / 3

Matchups    Kess      1 / 3,  BO3 0 / 1       3 games chacun : à égalité,
            Ragavan   2 / 3,  BO3 1 / 1       ordre alphabétique (sans méta)
            meilleure version : —             chaque oppo n'a été joué que par une version
```

Tous les chiffres portent un ⚠️ : aucun total n'atteint 10.

## ❌ Erreurs et ⚠️ avertissements

| | ❌ Erreur | ⚠️ Avertissement |
|---|---|---|
| Effet | aucun rapport écrit | les rapports sont écrits |
| Exemples | `games.csv` absent, en-tête inattendu, position ou résultat inconnu ; fiche deck illisible ou sans version ; méta invalide | deck de `games.csv` sans fiche ; version jouée absente de la fiche |
| Que faire | corriger puis relancer | créer la fiche ou ajouter la version (facultatif) |

## 🛡️ Protection des données

- **Lecture seule sur les données** : `games.csv`, les fiches deck et le méta ne sont jamais modifiés par les stats.
- **Tout est préparé avant la moindre écriture** : une seule erreur suffit à tout annuler, les anciens rapports restent en place.
- **Écriture en deux temps** : `write_report()` écrit d'abord un fichier `.tmp`, puis le renomme d'un coup par-dessus l'ancien rapport.
  Une coupure pendant l'écriture ne laisse jamais un rapport à moitié écrit.
- **Rien n'est inventé** : pas de chiffre sans donnée (`—`), et un chiffre fragile est signalé (⚠️).

## 🧱 Organisation du code

Même architecture que l'import : chaque couche n'utilise que celles du dessous.

```
src/dcprepa/
├── __main__.py             point d'entrée : module « stats », affiche le bilan
├── services/
│   └── stats.py            generate_stats, StatsReport : enchaîne toutes les étapes
├── domain/                 règles pures, sans fichier ni affichage
│   ├── winrate.py          Winrate, format_percent : un winrate et son affichage
│   ├── stats.py            compute_deck_stats, record, bo3_matches, version_gaps, best_version
│   │                       Record, VersionStats, BestVersion, MatchupStats, DeckStats
│   └── report.py           render_deck_report : DeckStats → Markdown
└── storage/                seul accès aux fichiers de data/
    ├── games.py            read_games
    ├── decks.py            load_deck_sheets
    ├── meta.py             load_latest_meta
    └── stats.py            write_report
```

- Les fonctions de `storage/` renvoient `(résultat, erreurs)` au lieu d'afficher ou d'arrêter le programme.
- `Winrate(wins, total)` est la brique de tout le rapport : il garde les deux nombres, calcule le pourcentage exact (`rate`)
  pour les écarts, et ne s'arrondit qu'à l'affichage.
- Le service renvoie un `StatsReport` (decks, games, méta, erreurs, avertissements) : la ligne de commande
  et l'interface graphique l'affichent chacune à leur façon, à partir du même service.
- Chaque fichier a ses tests dans `src/tests/`, rangés de la même façon (`python -m pytest` depuis `src/`).
