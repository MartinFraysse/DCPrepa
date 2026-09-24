# Import de l'inbox

> Comment une session saisie sur le téléphone devient des lignes de `games.csv` : les fichiers, la commande,
> chaque étape et les fonctions appelées. Pour comprendre le mécanisme ou le faire évoluer.

## Contexte

Pendant la préparation d'un tournoi, les games sont souvent jouées loin de l'ordinateur.
On les note donc vite, depuis le téléphone (via GitHub), dans une **boîte de réception** : `inbox.yaml`.
Ensuite, sur l'ordinateur, une commande **importe** ces saisies dans `games.csv`, le fichier qui sert aux stats.

Deux principes guident l'import :

- 🛡️ **Une erreur bloque tout** : si un seul bloc est invalide, rien n'est importé et aucun fichier n'est modifié.
  On corrige, on relance.
- 🔤 **Saisie souple, données propres** : au téléphone on peut écrire « raga » ou « terra mid » ;
  dans `games.csv`, chaque deck et chaque oppo n'a qu'un seul nom.

## Vue d'ensemble

```
  📱 téléphone                    💻 ordinateur                           📊 stats
┌──────────────────┐       ┌──────────────────────────────────┐       ┌──────────────────┐
│ inbox.yaml       │  git  │ python -m dcprepa import <nom>   │       │ games.csv        │
│ date: 02/10/2026 │ ────> │                                  │ ────> │ 1 ligne par game │
│ deck: terra mid  │  pull │ lire, vérifier, écrire           │       │ (sert aux stats) │
│ oppo: raga       │       │                                  │       │                  │
└──────────────────┘       └──────────────────────────────────┘       └──────────────────┘
         ^                                  │
         └──────────────────────────────────┘
           si l'import réussit : inbox vidée, son en-tête est gardé   🧹
```

## Les fichiers en jeu

Tous vivent dans `data/`. Un tournoi = un dossier `data/tournaments/<tournoi>/`.

```
data/
├── oppos.yaml                  commun à tous les tournois          🌍
└── tournaments/<tournoi>/
    ├── inbox.yaml              saisies à importer                  📥
    ├── games.csv               games importées                     📊
    └── decks/
        ├── <deck>.yaml         une fiche par deck (name, versions) 🃏
        └── _alias.yaml         appellations acceptées des decks    🔤
```

| Fichier | Rôle dans l'import | Lu | Écrit |
|---|---|---|---|
| `inbox.yaml` | les sessions à importer, un bloc par session | ✅ | vidé après un import réussi |
| `decks/<deck>.yaml` | decks existants, leurs versions (`v1`, `v2`…) et leur `name` | ✅ | — |
| `decks/_alias.yaml` | appellations acceptées pour chaque deck (facultatif) | ✅ | — |
| `data/oppos.yaml` | nom de référence de chaque deck adverse et ses variantes | ✅ | — |
| `games.csv` | `match_id` déjà utilisés, pour continuer la numérotation | ✅ | lignes ajoutées à la fin |

Les fichiers de `decks/` qui commencent par `_` (`_alias.yaml`, `_modele.yaml`) ne sont pas des fiches deck.

## 📝 Saisir une session

Un **bloc** par session : même date, source, deck, version et oppo. Les blocs sont séparés par une ligne `---`.
L'en-tête commenté du fichier (lignes `#`) sert de mode d'emploi et n'est jamais importé.

```yaml
date: 02/10/2026                  # JJ/MM/AAAA
source: paper                     # paper | mtgo | cockatrice
deck: terra mid                   # fichier, name ou variante de _alias.yaml
version: v1                       # doit exister dans la fiche du deck
oppo: raga                        # deck adverse ; self-play : terra@v2
games: OTP W, OTD W / OTD L       # BO séparés par « / », games par « , »
note/ressenti: Matchup jouable    # facultatif
---
date: 03/10/2026
source: mtgo
```

Le champ `games` se lit ainsi :

```
games:  OTP W, OTD W  /  OTD L
        └────┬─────┘     └─┬─┘
           BO 1          BO 2
        2 games, 2-0     1 game (BO1)

une game = position + résultat
           OTP : je commence    W : gagnée
           OTD : je suis 2e     L : perdue
```

## ▶️ Lancer l'import

Depuis `src/`, venv activé :

```
python -m dcprepa import relicfest-2026
```

Trois issues possibles :

```
✅ 2 bloc(s) importé(s) : 3 BO, 6 game(s).
⚠️  Avertissements :
  - bloc 2 : oppo inconnu : Atraxa → à ajouter dans data/oppos.yaml
```

```
❌ Import annulé, aucun fichier modifié. Erreurs à corriger :
  - bloc 2 : source inconnue (paper, mtgo ou cockatrice) : arena
  - bloc 2 : games : BO 1 : game 3 : en trop, BO déjà terminé (2-0)
```

```
Inbox vide : rien à importer.
```

| Code de sortie | Signification |
|---|---|
| `0` | import réussi, ou inbox vide |
| `1` | erreurs : rien n'a été modifié |
| `2` | mauvaise utilisation (module ou tournoi inconnu) |

## ⚙️ Ce qui se passe, étape par étape

`dcprepa/__main__.py` retrouve le dossier du tournoi, appelle le service `import_inbox()`
(`services/import_inbox.py`), puis affiche le bilan qu'il renvoie. Tout le travail est dans le service :

```
python -m dcprepa import <tournoi>
        │
  1. Lire les fichiers         inbox, decks, appellations, oppos, games.csv   📂
        │
  2. Vérifier chaque bloc      deck, champs, date, source, version, games     🔍
        │
  3. Préparer les lignes       nom de l'oppo, une ligne par game, match_id    🧮
        │
  4. Une erreur quelque part ?
        │
        ├── oui ──  rien n'est écrit                                          🚫
        │
        └── non ──  5. Écrire : games.csv, puis vider inbox.yaml              💾

  Dans tous les cas : bilan affiché   ✅ importé   ❌ erreurs   ⚠️ avertissements
```

### 1. Lire les fichiers

Le service lit tout une seule fois, avant de regarder le moindre bloc :

- `read_inbox()` : les blocs de `inbox.yaml`. Chaque bloc est lu séparément, pour que deux blocs mal écrits
  soient signalés d'un coup, avec leur numéro de ligne.
- `load_decks()` et `load_deck_aliases()` : les decks du tournoi, leurs versions et toutes leurs appellations.
- `load_oppos()` : les decks adverses connus.
- `read_match_ids()` : les `match_id` déjà présents dans `games.csv`.

Si un de ces fichiers manque ou est illisible, ou si l'inbox ne contient aucun bloc, le service s'arrête là.

### 2. Vérifier chaque bloc

1. `resolve_deck()` remplace le deck saisi par le nom de son fichier (« terra mid » → `terra-midrange`).
2. `validate_block()` fait tous les contrôles et renvoie la liste des problèmes :

| Contrôle | Refusé si… | Exemple de message |
|---|---|---|
| forme du bloc | ce n'est pas une suite de « champ: valeur » | `bloc mal formé (…)` |
| champs obligatoires | `date`, `source`, `deck`, `version`, `oppo` ou `games` absent ou vide | `champ manquant : oppo` |
| date | pas au format JJ/MM/AAAA, ou date impossible | `date invalide (attendu : JJ/MM/AAAA) : 31/02/2026` |
| source | pas `paper`, `mtgo` ou `cockatrice` | `source inconnue (…) : arena` |
| deck | aucune fiche ne correspond | `deck inconnu : x (decks disponibles : …)` |
| version | absente de la fiche du deck | `version inconnue pour terra-midrange : v9` |
| games | voir ci-dessous | `games : BO 2 : game 1 : …` |

3. Pour le champ `games`, `parse_bos()` découpe sur `/` et confie chaque BO à `_parse_games()` :

```
parse_bos("OTP W, OTD W / OTD L")
   │
   ├── _parse_games("OTP W, OTD W")   →   [OTP W] [OTD W]
   │
   └── _parse_games("OTD L")          →   [OTD L]

contrôles : format « position résultat », OTP/OTD, W/L,
            3 games au plus, BO terminé dès 2 victoires
```

Les messages s'emboîtent pour dire exactement où chercher :
`bloc 2 : games : BO 1 : game 3 : en trop, BO déjà terminé (2-0)`.

### 3. Préparer les lignes

- **L'oppo** : `normalize_oppo()` le ramène à son nom de référence (« RAGA » → `Ragavan`).
  Inconnu, il est gardé tel quel avec un ⚠️ avertissement : l'import se fait quand même.
  Pour un self-play (`deck@version`), c'est `resolve_self_play()` qui reconnaît le deck (« terra mid@v2 » → `terra-midrange@v2`).
- **Les lignes** : `build_rows()` produit une ligne par game et un `match_id` par BO.
  `next_match_id()` le numérote `JJ/MM/AAAA-NN` (ex. `02/10/2026-01`) : NN repart de 01 chaque jour et suit le plus grand numéro
  déjà utilisé ce jour-là, dans `games.csv` comme dans les blocs précédents.

### 4. Une erreur quelque part ?

Tous les blocs ont été vérifiés. S'il y a **au moins une erreur**, le service s'arrête et renvoie la liste complète :
`games.csv` et `inbox.yaml` n'ont pas été touchés. On corrige tout d'un coup, puis on relance.

### 5. Écrire

1. `append_rows()` ajoute les lignes à la fin de `games.csv`.
2. `clear_inbox()` vide `inbox.yaml` en gardant son en-tête commenté.

L'ordre est volontaire : si le programme était coupé entre les deux, les games seraient déjà dans
`games.csv` et encore dans l'inbox. Au pire un doublon à retirer, **jamais une game perdue**.

## 🔎 Le trajet d'un bloc

```
inbox.yaml                        ce que l'import en fait
┌──────────────────────────┐
│ date: 02/10/2026         │      deck    terra mid    →  terra-midrange
│ source: Paper            │      oppo    raga         →  Ragavan
│ deck: terra mid          │      source  Paper        →  paper
│ version: v1              │      BO      2 BO         →  2 match_id
│ oppo: raga               │
│ games: OTP W, OTD W      │      games.csv contient déjà 02/10/2026-01,
│          / OTD L         │      les BO reçoivent donc -02 et -03
│ note/ressenti: serré, OK │
└──────────────────────────┘
```

Lignes ajoutées à `games.csv` :

```
date,match_id,game,source,deck,version,oppo,position,resultat,note/ressenti
02/10/2026,02/10/2026-02,1,paper,terra-midrange,v1,Ragavan,OTP,W,"serré, OK"
02/10/2026,02/10/2026-02,2,paper,terra-midrange,v1,Ragavan,OTD,W,"serré, OK"
02/10/2026,02/10/2026-03,1,paper,terra-midrange,v1,Ragavan,OTD,L,"serré, OK"
```

La note est recopiée sur chaque ligne du bloc, et mise entre guillemets si elle contient une virgule.

## 🔤 Reconnaissance des noms

La comparaison est **souple** : majuscules et espaces en trop sont ignorés (« TERRA  mid » = « terra mid »).

| | Decks (tes decks) | Oppos (decks adverses) |
|---|---|---|
| Noms acceptés | nom du fichier, champ `name` de la fiche, variantes de `decks/_alias.yaml` | nom de référence et variantes de `data/oppos.yaml` |
| Portée | par tournoi | commun à tous les tournois |
| Écrit dans `games.csv` | le nom du fichier (`terra-midrange`) | le nom de référence (`Ragavan`) |
| Nom inconnu | ❌ erreur, avec la liste des decks disponibles | ⚠️ avertissement, gardé tel quel |
| Même appellation pour deux noms | ❌ erreur | ❌ erreur |

```yaml
# decks/_alias.yaml               # data/oppos.yaml
terra-midrange:                   Ragavan:
    - Terra                           - Ragavan, Nimble Pilferer
    - Terra mid                       - raga
```

## ❌ Erreurs et ⚠️ avertissements

| | ❌ Erreur | ⚠️ Avertissement |
|---|---|---|
| Effet | rien n'est importé | l'import se fait |
| Exemples | date, source, deck, version ou games invalides ; bloc YAML illisible ; fichier manquant ; `_alias.yaml` ou `oppos.yaml` incohérent | oppo inconnu ; deck inconnu dans un self-play |
| Que faire | corriger puis relancer | ajouter le nom dans `oppos.yaml` ou `_alias.yaml` (facultatif) |

## 🛡️ Protection des données

- **Tout est vérifié avant la moindre écriture** : une seule erreur suffit à tout annuler.
- **Écriture en deux temps** : `append_rows()` et `clear_inbox()` écrivent d'abord un fichier `.tmp`,
  puis le renomment d'un coup par-dessus l'original. Une coupure pendant l'écriture laisse l'ancien fichier intact.
- **Fins de ligne conservées** : un fichier en CRLF (Windows) reste en CRLF, pour éviter des diffs git inutiles.
- **Rien n'est inventé** : un deck inconnu bloque l'import plutôt que de créer un deck fantôme dans les stats.

## 🧱 Organisation du code

Le code est rangé en couches ; chaque couche n'utilise que celles du dessous.

```
src/dcprepa/
├── __main__.py             point d'entrée, affiche le bilan
├── services/
│   └── import_inbox.py     import_inbox, ImportReport : enchaîne toutes les étapes
├── domain/                 règles pures, sans fichier ni affichage
│   ├── validation.py       validate_block
│   ├── games.py            parse_bos, _parse_games
│   ├── names.py            name_key, build_name_index (comparaison souple)
│   ├── decks.py            resolve_deck, resolve_self_play
│   ├── oppos.py            build_oppo_index, normalize_oppo
│   └── rows.py             next_match_id, build_rows
└── storage/                seul accès aux fichiers de data/
    ├── inbox.py            read_inbox, clear_inbox
    ├── decks.py            load_decks, load_deck_aliases
    ├── oppos.py            load_oppos
    └── games.py            read_match_ids, append_rows
```

- Les fonctions de `domain/` et `storage/` renvoient `(résultat, erreurs)` au lieu d'afficher ou d'arrêter le programme.
- Le service renvoie un `ImportReport` (blocs, BO, games, erreurs, avertissements) : la ligne de commande
  et l'interface graphique l'affichent chacune à leur façon, à partir du même service.
- Chaque fichier a ses tests dans `src/tests/`, rangés de la même façon (`python -m pytest` depuis `src/`).
