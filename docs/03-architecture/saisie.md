# Saisie

> Comment le logiciel remplit lui-même les fichiers de saisie : créer un tournoi ou un deck, ajouter une version, un oppo,
> des games, et corriger une game ou un BO. Les services, les modules de la ligne de commande, les contrôles et le code.

## Contexte

Tous les fichiers de saisie (voir [Organisation des données](donnees.md)) peuvent s'écrire à la main. Mais une virgule oubliée
dans un YAML, une version mal tapée ou une game saisie à l'envers, et l'import ou les stats refusent de tourner.

Les **services de saisie** font ce travail à la place : on leur donne des valeurs (un formulaire de la GUI, ou des options
en ligne de commande), ils vérifient tout, puis écrivent le fichier sans toucher au reste.

Quatre principes :

- 🛡️ **Tout ou rien** : à la moindre erreur, aucun fichier n'est modifié.
- 🔁 **Les mêmes contrôles partout** : une game saisie passe exactement par les contrôles de l'import de l'inbox.
- ✍️ **Le reste du fichier est gardé** : commentaires, ordre et mise en forme ne bougent pas ; seule la ligne visée change.
- 🔍 **Relu avant d'écrire** : chaque texte produit est relu ; s'il ne donne pas le résultat attendu, rien n'est écrit.

## Vue d'ensemble

```
  🖥️ GUI / ⌨️ ligne de commande       ⚙️ services de saisie                      📂 data/
┌─────────────────────────────┐    ┌──────────────────────────────────┐    ┌─────────────────────────────┐
│ un formulaire,              │    │ tournoi   create / edit          │    │ tournaments/<slug>/         │
│ ou des options :            │ ─> │ games     add / edit / delete    │ ─> │   tournament.yaml           │
│ --deck Terra --games "…"    │    │ decks     create / version /     │    │   games.csv                 │
│                             │    │           statut / edit / alias  │    │   decks/<deck>.yaml, _alias │
│                             │    │ oppos     add                    │    │ oppos.yaml                  │
└─────────────────────────────┘    └──────────────────────────────────┘    └─────────────────────────────┘
```

Le téléphone garde sa voie : il remplit `inbox.yaml`, importé ensuite (voir [Import de l'inbox](import-inbox.md)).
Les deux chemins arrivent au même `games.csv`, par les mêmes contrôles :

```
 📱 téléphone ──> inbox.yaml ──> import ─────┐
                                             ├──> prepare_block() ──> games.csv
 🖥️ formulaire ──────────────> add_games() ──┘     (mêmes contrôles)
```

## 🧰 Les services

| Fichier | Service | Rôle | Module |
|---|---|---|---|
| 🏆 `tournament.yaml` | `create_tournament` | nouveau tournoi copié du modèle, slug déduit du nom | `tournament-create` |
| | `edit_tournament` | nom, date, lieu, format, banlist, notes | `tournament-edit` |
| 🎮 `games.csv` | `add_games` | les games d'une session (BO3, BO1) | `game-add` |
| | `edit_game` | une game : position, résultat, note | `game-edit` |
| | `edit_match` | un BO entier : date, source, deck, version, oppo | `bo-edit` |
| | `delete_game` | une game d'un BO | `game-delete` |
| | `delete_match` | un BO entier | `bo-delete` |
| 🃏 `decks/<deck>.yaml` | `create_deck` | nouvelle fiche, avec la version v1 | `deck-create` |
| | `add_version` | nouvelle version : cartes in / out, liste, notes | `deck-version` |
| | `set_status` | `retenu`, `envisage` ou `ecarte` | `deck-status` |
| | `edit_deck` | nom affiché, commandant | `deck-edit` |
| 🃏 `decks/_alias.yaml` | `add_deck_alias` | une appellation du deck (« Terra mid ») | `deck-alias` |
| ⚔️ `data/oppos.yaml` | `add_oppo` | nouvel oppo, ou variante d'un oppo connu | `oppo-add` |

Chaque service renvoie un **bilan** (ce qui a été écrit, erreurs, avertissements) : la ligne de commande l'affiche,
la GUI l'affichera à sa façon.

## ▶️ Lancer un module

Depuis `src/`, venv activé. `python -m dcprepa --help` liste les modules, `python -m dcprepa <module> --help` leurs options.

### 📋 Tous les modules

`<tournoi>` est le slug du dossier (ex. `relicfest-2026`) ; `<deck>` accepte le fichier, le `name` ou une appellation du deck ;
une game se désigne par `<match_id>` (ex. `02/10/2026-01`) et `<game>`, son numéro dans le BO. Options entre crochets : facultatives.

| Module | Arguments | Options | Rôle |
|---|---|---|---|
| `import` | `<tournoi>` | — | importe `inbox.yaml` dans `games.csv` (voir [Import de l'inbox](import-inbox.md)) |
| `meta` | `<tournoi>` | — | importe le méta MTGTop8 dans `meta/AAAA-MM-JJ/` (voir [Import du méta](import-meta.md)) |
| `stats` | `<tournoi>` | — | écrit les rapports de deck et la synthèse (voir [Rapports de stats](stats.md)) |
| `tournament-create` | `<nom>` | `[--date] [--location] [--format] [--banlist] [--notes]` | crée `data/tournaments/<slug>/`, slug déduit du nom |
| `tournament-edit` | `<tournoi>` | `[--name] [--date] [--location] [--format] [--banlist] [--notes]` | modifie `tournament.yaml` |
| `game-add` | `<tournoi>` | `--source --deck --version --oppo --games [--date] [--note]` | ajoute les games d'une session (date du jour par défaut) |
| `game-edit` | `<tournoi> <match_id> <game>` | `[--position] [--resultat] [--note]` | corrige une game |
| `bo-edit` | `<tournoi> <match_id>` | `[--date] [--source] [--deck] [--version] [--oppo]` | corrige toutes les games d'un BO |
| `game-delete` | `<tournoi> <match_id> <game>` | — | supprime une game, renumérote les suivantes |
| `bo-delete` | `<tournoi> <match_id>` | — | supprime un BO |
| `oppo-add` | `<nom>` | `[--variant-of <oppo>]` | ajoute un oppo, ou une variante d'un oppo connu, à `data/oppos.yaml` |
| `deck-create` | `<tournoi> <nom>` | `[--commandant] [--statut] [--liste <fichier>] [--notes]` | crée `decks/<deck>.yaml` avec la version v1 |
| `deck-version` | `<tournoi> <deck>` | `[--version] [--in <carte>]… [--out <carte>]… [--liste <fichier>] [--notes]` | ajoute une version (suivante automatique) |
| `deck-status` | `<tournoi> <deck> <statut>` | — | `retenu`, `envisage` ou `ecarte` |
| `deck-edit` | `<tournoi> <deck>` | `[--name] [--commandant]` | corrige le nom affiché ou le commandant |
| `deck-alias` | `<tournoi> <deck> <appellation>` | — | ajoute une appellation dans `decks/_alias.yaml` |

`--in` et `--out` se répètent, une carte par option : `--in "Force of Will" --in Daze`.

### Exemples

```
python -m dcprepa tournament-create "RelicFest 2026" --date 31/10/2026
python -m dcprepa deck-create relicfest-2026 "Kinnan Combo" --commandant "Kinnan, Bonder Prodigy" --liste kinnan.txt
python -m dcprepa game-add relicfest-2026 --source paper --deck Terra --version v2 --oppo Ragavan --games "OTP W, OTD L, OTP W / OTP W"
python -m dcprepa game-edit relicfest-2026 02/10/2026-01 2 --resultat W
python -m dcprepa deck-status relicfest-2026 terra retenu
```

Issues possibles :

```
✅ 2 BO, 4 game(s) ajoutés : 02/10/2026-02, 02/10/2026-03.
⚠️  Avertissements :
  - oppo inconnu : Ragavn → à ajouter dans data/oppos.yaml
```

```
❌ Rien n'a été modifié. Erreurs à corriger :
  - 02/10/2026-01 : game 3 : en trop, BO déjà terminé (2-0)
```

| Code de sortie | Signification |
|---|---|
| `0` | écrit (avec ou sans avertissements) |
| `1` | erreurs : rien n'a été modifié |
| `2` | mauvaise utilisation (module, argument) ou tournoi introuvable |

Une erreur d'utilisation affiche la ligne d'utilisation du module et la raison, en français :

```
utilisation : python -m dcprepa deck-status [-h] tournoi deck {retenu,envisage,ecarte}
python -m dcprepa deck-status : erreur : argument statut : valeur invalide : 'écarté' (possibles : 'retenu', 'envisage', 'ecarte')
```

Deux commodités : `game-add` prend la date du jour sans `--date` ; une liste de cartes se donne par un fichier texte
(`--liste kinnan.txt`, export MTGO / Moxfield, une ligne « 1 Nom de carte » par carte).

## 🏆 Tournoi

```
create_tournament("Été Duel #3", date 1/9/2026)

data/tournaments/ete-duel-3/          ← slug déduit du nom
├── tournament.yaml                   name, slug, date (01/09/2026) remplis, commentaires gardés
├── decks/  games.csv  inbox.yaml  meta/
└── stats/                            README du modèle et _modele-deck.md retirés
```

- **Slug** : minuscules, accents retirés, tout autre caractère que lettre ou chiffre devient `-`
  (« RelicFest 2026 » → `relicfest-2026`, « Été Duel #3 » → `ete-duel-3`).
- **Dossier déjà existant** : erreur, pas de suffixe automatique, pour ne jamais créer un doublon sans le voir.
- La copie se fait dans `<slug>.tmp`, renommé à la fin : jamais de tournoi à moitié créé.
- `edit_tournament` change les champs de la fiche, jamais le slug ni le dossier.

## 🎮 Games

### Ajouter

Le formulaire d'une session a **les mêmes champs qu'un bloc de l'inbox** : date, source, deck, version, oppo, games, note.
Il passe par `prepare_block()`, la fonction de l'import : deck ramené au nom de son fichier (« Terra » → `terra-midrange`),
oppo ramené à son nom de référence, `match_id` qui suivent ceux du jour, mêmes messages d'erreur.
Un oppo inconnu n'est pas bloquant : la game est écrite avec le nom saisi, et un avertissement propose de l'ajouter.

`games.csv` est entièrement vérifié avant tout ajout : si une de ses lignes est déjà invalide (position `OTX`, colonne manquante…),
rien n'est ajouté, comme pour l'import et les stats. On corrige d'abord le fichier, puis on relance.

### Corriger et supprimer

Une game se désigne par son **`match_id` et son numéro** : `02/10/2026-01`, game 2.

```
games.csv ──> BO 02/10/2026-01 ──> bloc + la correction ──> prepare_block() ──> BO remis à sa place ──> games.csv
```

- Le BO corrigé est **revérifié en entier**, comme à l'import. Une correction qui le rend impossible est refusée :

```
W L W  ── game 2 : L → W ──>  W W W   ❌ game 3 : en trop, BO déjà terminé (2-0)
```

  Si la game 2 était gagnée, la game 3 n'a pas été jouée : la supprimer d'abord, puis corriger la game 2.
- Les **notes** de chaque game sont gardées. Le **`match_id`** ne change que si la date du BO change
  (prochain numéro libre de la nouvelle date).
- **Supprimer une game** renumérote les suivantes (3 → 2). Un BO3 réduit à une seule game devient un BO1 et sort du winrate
  par BO3 : un avertissement le signale.
- `games.csv` est réécrit en entier via un fichier `.tmp` ; les autres lignes restent identiques, fins de ligne comprises.

## 🃏 Decks

```
create_deck("Kinnan Combo", liste)    ──> decks/kinnan-combo.yaml, version v1
add_version("Terra mid", in, out)     ──> v2 ajoutée (numéro suivant automatique)
set_status("terra", "retenu")
```

- **Nom du fichier** déduit du nom du deck, comme le slug d'un tournoi. Refusé : nom réservé (`synthese`, `README`,
  qui sont des fichiers de `stats/`), ou appellation déjà prise par un autre deck (fichier, `name` ou alias).
- **Désigner un deck** : par n'importe quelle appellation, son fichier, son `name` ou un alias.
- **Liste** : facultative pour v1 ; chaque ligne doit suivre « 1 Nom de carte » ; un total différent de 100 cartes donne un avertissement.
- **Version** : suivante automatique (v3 → v4), ou imposée ; refusée si elle existe déjà ou n'apporte aucun changement (ni in, ni out, ni liste).
  Elle s'ajoute après la dernière version réelle : un exemple commenté en fin de fiche reste en dessous.
- **Statut** : `retenu`, `envisage` ou `ecarte`, sans accents. Seuls les decks retenus ou envisagés sont comparés au méta
  dans la synthèse (voir [Rapports de stats](stats.md)).

## ⚔️ Oppos

```
add_oppo("Atraxa")                          ──> nouvel oppo, à la fin de data/oppos.yaml
add_oppo("Ragavn", variant_of="raga")       ──> variante, sous « Ragavan: »
```

- Refusé : nom vide, nom déjà connu (comme oppo ou comme variante), `@` (réservé au self-play `deck@version`), oppo de référence inconnu.
- `variant_of` accepte toute forme connue : « raga » désigne Ragavan.
- Utilité : éviter qu'un même deck compte sous deux noms dans les stats (*Ragavn* / *Ragavan*).

## ❌ Erreurs et ⚠️ avertissements

| | ❌ Erreur | ⚠️ Avertissement |
|---|---|---|
| Effet | rien n'est modifié | l'écriture est faite |
| Exemples | deck, version ou `match_id` inconnus ; BO impossible ; nom déjà pris ou réservé ; statut ou date invalide ; `games.csv`, fiche deck ou `oppos.yaml` illisible ou ambigu | oppo inconnu ; liste qui ne fait pas 100 cartes ; BO3 réduit à un BO1 |
| Que faire | corriger la valeur puis relancer | ajouter l'oppo, compléter la liste (facultatif) |

## 🛡️ Protection des données

- **Contrôles avant écriture** : aucune écriture tant qu'une erreur reste.
- **Écriture en deux temps** : chaque fichier est écrit dans un `.tmp`, puis renommé d'un coup par-dessus l'ancien.
- **Texte relu** : fiche deck, `tournament.yaml`, `oppos.yaml` et `_alias.yaml` sont relus après modification, avant d'être écrits ;
  un résultat inattendu annule l'écriture.
- **Commentaires gardés** : les YAML sont modifiés comme du texte (une ligne remplacée ou ajoutée), jamais réécrits en entier.

## 🧱 Organisation du code

```
src/dcprepa/
├── __main__.py              un module par service (argparse, messages en français), affiche le bilan
├── services/
│   ├── games.py             add_games, edit_game, edit_match, delete_game, delete_match, load_game_references
│   ├── tournament.py        create_tournament, edit_tournament
│   ├── decks.py             create_deck, add_version, set_status, edit_deck, add_deck_alias
│   └── oppos.py             add_oppo
├── domain/                  règles pures, sans fichier
│   ├── blocks.py            prepare_block : un bloc → lignes de games.csv (partagé avec l'import)
│   ├── edits.py             corrections d'un BO sur la liste des games
│   ├── saisie.py            slugify, contrôles du tournoi, du deck, de la liste, des versions
│   └── oppos.py             check_new_oppo
└── storage/                 seul accès aux fichiers de data/
    ├── games.py             append_rows, write_games
    ├── tournament.py        create_tournament_dir, update_tournament_file
    ├── decks.py             create_deck_file, append_version, update_deck_fields, add_alias
    ├── oppos.py             insert_variant
    └── yaml_text.py         set_fields, append_list_item : modifier un YAML en gardant ses commentaires
```

- Chaque service renvoie un bilan (`GamesReport`, `TournamentReport`, `DeckReport`, `OppoReport`) avec `errors`, `warnings` et `ok`.
- Chaque fichier a ses tests dans `src/tests/`, rangés de la même façon (`python -m pytest` depuis `src/`).
