# Import du méta

> Comment le méta Duel Commander de MTGTop8 devient `meta/AAAA-MM-JJ/general.csv` et `paper.csv` : la source, la commande,
> chaque étape, les noms ajoutés à `data/oppos.yaml` et les fonctions appelées. Pour comprendre le mécanisme ou le faire évoluer.

## Contexte

Savoir contre quoi on jouera au tournoi est aussi important que ses propres winrates. MTGTop8 recense les decks classés
dans les tournois Duel Commander : une commande en tire le **méta du moment**, que les [rapports de stats](stats.md) utilisent
pour trier les matchups et afficher le poids de chaque oppo.

Quatre principes guident l'import :

- 🛡️ **Une erreur bloque tout** : site injoignable, page inattendue ou `oppos.yaml` invalide : rien n'est écrit. On relance plus tard.
- 🎯 **Deux métas, top 20** : à chaque import, le méta **général** et le méta **papier** des 2 derniers mois ; seuls les 20 oppos
  les plus joués de chacun sont gardés, avec leur poids réel.
- 📅 **L'historique est gardé** : un dossier daté par import ; les imports précédents ne sont jamais modifiés.
- 🔤 **Des noms propres, sans saisie** : chaque oppo reçoit son nom de référence de `oppos.yaml` ; un oppo inconnu y est
  **ajouté automatiquement**, sous un nom court.

## Vue d'ensemble

```
  🌐 MTGTop8                    💻 ordinateur                           🌍 méta
┌──────────────────┐       ┌──────────────────────────────────┐       ┌─────────────────────────┐
│ méta général     │ https │ python -m dcprepa meta <tournoi> │       │ meta/2026-09-24/        │
│ méta papier      │ ────> │                                  │ ────> │ ├── general.csv         │
│ 2 derniers mois  │       │ télécharger, lire, nommer, écrire│       │ └── paper.csv           │
└──────────────────┘       └──────────────────────────────────┘       └─────────────────────────┘
                                          │
                                          └──> 📖 data/oppos.yaml : nouveaux oppos ajoutés à la fin
```

Ensuite, `python -m dcprepa stats <tournoi>` lit le dossier le plus récent : colonnes « Poids papier » et « Poids général »,
matchups triés par poids papier.

## Les fichiers en jeu

```
data/
├── oppos.yaml                  noms de référence des oppos (commun)       📖
└── tournaments/<tournoi>/
    └── meta/
        ├── README.md           format des fichiers
        ├── 2026-09-10/         import précédent, gardé                    📅
        │   ├── general.csv
        │   └── paper.csv
        └── 2026-09-24/         import du jour                             🌍
            ├── general.csv     top 20 du méta général (paper + MTGO)
            └── paper.csv       top 20 du méta papier
```

| Fichier | Rôle dans l'import | Lu | Écrit |
|---|---|---|---|
| `data/oppos.yaml` | noms de référence et variantes des oppos | ✅ | nouveaux oppos ajoutés à la fin |
| `meta/<date du jour>/general.csv` | top 20 du méta général | — | créé, ou remplacé si déjà là aujourd'hui |
| `meta/<date du jour>/paper.csv` | top 20 du méta papier | — | créé, ou remplacé si déjà là aujourd'hui |
| `meta/<autres dates>/` | imports précédents | — | jamais touchés |

## 🌐 La source : MTGTop8

MTGTop8 n'a pas d'API. Sa page de méta Duel Commander (`https://www.mtgtop8.com/format?f=EDH`) charge sa liste en JavaScript,
depuis un **fragment** HTML que l'on peut lire directement, sans navigateur :

```
https://www.mtgtop8.com/cEDH_decks?f=EDH&show=pop&cid=&meta=<période>&gamerid1=&gamerid2=&cEDH_cp=1

1447 decks                                   ← nombre total de decks sur la période
Phelia, Exuberant Shepherd      58.1 ‰       ← un archétype (un commandant) et sa part en ‰
Cloud, Midgar Mercenary         57.4 ‰
Partner WUR                     36.8 ‰       ← les partenaires sont regroupés par couleurs
…                                            (159 archétypes, une seule page)
```

| Méta | Période MTGTop8 | `meta=` | Fichier |
|---|---|---|---|
| général | Last 2 Months (paper + MTGO) | `121` | `general.csv` |
| papier | Paper Last 2 Months | `308` | `paper.csv` |

- **Duel Commander** s'appelle `EDH` chez MTGTop8 (`f=EDH`).
- La page donne le **total** de decks et la **part** de chaque archétype, en ‰. Le poids est donc exact ;
  le nombre de decks d'un archétype, lui, n'est pas affiché : il est **estimé** (part × total).
- Les accents et apostrophes arrivent en entités HTML (`&#039;`, `&iacute;`) : ils sont décodés.
- ⚠️ Un identifiant `meta=` inconnu ne renvoie pas d'erreur mais **toute la base** : les deux identifiants sont fixés dans le code.
- Deux requêtes par import, un User-Agent qui identifie l'outil, un délai d'attente de 20 s.

## ▶️ Lancer l'import

Depuis `src/`, venv activé, **avant** de générer les stats :

```
python -m dcprepa meta relicfest-2026
python -m dcprepa stats relicfest-2026
```

Issues possibles :

```
✅ meta/2026-09-24/ écrit : général 20 oppos (1447 decks), papier 20 oppos (1309 decks).
📝 20 oppo(s) ajouté(s) à data/oppos.yaml : Phelia, Cloud, Brigid, Aragorn, Slimefoot And Squee, …
```

```
✅ meta/2026-09-24/ écrit (remplace l'import du jour) : général 20 oppos (1447 decks), papier 20 oppos (1309 decks).
```

```
❌ Import du méta annulé, aucun fichier modifié. Erreurs à corriger :
  - méta papier : MTGTop8 ne répond pas (délai de 20 s dépassé)
```

| Code de sortie | Signification |
|---|---|
| `0` | méta écrit |
| `1` | erreurs : aucun fichier modifié |
| `2` | mauvaise utilisation (module ou tournoi inconnu) |

⚠️ `data/oppos.yaml` est **commun à tous les tournois** : les oppos ajoutés servent partout, quel que soit le tournoi importé.

## ⚙️ Ce qui se passe, étape par étape

`dcprepa/__main__.py` retrouve le dossier du tournoi, appelle le service `import_meta()`
(`services/import_meta.py`), puis affiche le bilan qu'il renvoie. Tout le travail est dans le service :

```
python -m dcprepa meta <tournoi>
        │
  1. Lire data/oppos.yaml           noms de référence et variantes               📖
        │
  2. Télécharger les 2 pages        général (121), papier (308)                  🌐
        │
  3. Lire chaque page               total + (nom, ‰) par archétype               🔍
        │
  4. Une erreur quelque part ?
        │
        ├── oui ──  rien n'est écrit                                             🚫
        │
        └── non ──  5. Construire     noms, fusion, poids, top 20, nouveaux oppos  🧮
                          │
                    6. Écrire          meta/<date>/general.csv + paper.csv,       💾
                                       PUIS les nouveaux oppos dans oppos.yaml

  Dans tous les cas : bilan affiché   ✅ écrit   📝 oppos ajoutés   ❌ erreurs
```

### 1. Lire `data/oppos.yaml`

`load_oppos()` lit le fichier, `build_oppo_index()` en fait une table « forme souple → nom de référence »
(majuscules et espaces ignorés). Un fichier absent ou incohérent (une variante rattachée à deux oppos) arrête tout,
**avant** toute requête au site.

### 2. Télécharger les deux pages

`fetch_meta_page()` (`storage/mtgtop8.py`) est le **seul** endroit du logiciel qui touche au réseau. Elle ne lève jamais
d'exception : chaque problème devient un message, préfixé du méta concerné.

| Problème | Message |
|---|---|
| pas de connexion | `méta général : MTGTop8 injoignable (…) : vérifier la connexion internet` |
| site trop lent | `méta papier : MTGTop8 ne répond pas (délai de 20 s dépassé)` |
| erreur du site | `méta général : MTGTop8 : réponse HTTP 503 pour https://…` |
| réponse vide | `méta papier : MTGTop8 : page vide pour https://…` |

### 3. Lire chaque page

`parse_meta_page()` (`domain/mtgtop8.py`) renvoie un `MetaPage(total, entries)`. Une page qui ne ressemble pas à ce qu'on attend
n'est **jamais** lue comme un méta vide :

| Contrôle | Refusé si… |
|---|---|
| total | « N decks » introuvable (page de maintenance, site modifié) |
| archétypes | aucun trouvé, ou un archétype sans nom ou sans part |
| somme | la somme des ‰ s'écarte de plus de 20 ‰ de 1000 (arrondis du site : ± 1 ‰) |

### 4. Une erreur quelque part ?

Tout a été lu. S'il y a **au moins une erreur**, le service s'arrête : ni `meta/` ni `oppos.yaml` n'ont été touchés.

### 5. Construire le méta

`build_meta()` (`domain/meta.py`) transforme chaque page en lignes `oppo,decks,poids` :

```
MTGTop8 (1447 decks)                              general.csv
Phelia, Exuberant Shepherd   58.1 ‰   ──nom──>    Phelia,84,5.81
Tymna Thrasios               15.0 ‰   ─┐
Partner WUBG                 35.0 ‰   ─┴fusion─>  Tymna/Thrasios,72,5
…                                                 …  (20 lignes au plus)
```

| Règle | Détail |
|---|---|
| nom | ramené au nom de référence de `oppos.yaml` (comparaison souple) |
| fusion | plusieurs archétypes du même oppo : leurs ‰ s'additionnent |
| poids | ‰ / 10, à 2 décimales : 58.1 ‰ → `5.81` (exact) |
| decks | ‰ × total / 1000, arrondi : 58.1 × 1447 / 1000 → `84` (estimé) |
| tri | poids ↓, puis nom |
| top 20 | seules les 20 premières lignes sont gardées, avec leur poids réel (le top 20 fait environ 63 %) |

Les oppos du top 20 absents de `oppos.yaml` passent par `propose_oppos()` (voir « Les noms » ci-dessous) ; le méta est
ensuite **reconstruit** avec ces nouveaux noms, pour que `general.csv` et `paper.csv` contiennent les noms courts.

### 6. Écrire

1. `write_meta()` écrit `meta/<date>/general.csv` puis `paper.csv` (dossier créé si besoin, remplacé s'il existe déjà aujourd'hui).
2. `append_oppos()` ajoute les nouveaux oppos à la fin de `data/oppos.yaml`.

Chaque fichier passe par un fichier `.tmp` renommé d'un coup : une coupure pendant l'écriture ne laisse jamais un fichier à moitié écrit.

## 🔤 Les noms et `data/oppos.yaml`

Les noms MTGTop8 sont longs (« Phelia, Exuberant Shepherd ») ; ceux de `games.csv` sont courts (« Phelia »). Pour que les rapports
rapprochent les deux, **chaque oppo du méta doit avoir un nom de référence**. Les inconnus du top 20 en reçoivent un :

| Nom MTGTop8 | Ajouté dans `oppos.yaml` | Pourquoi |
|---|---|---|
| `Phelia, Exuberant Shepherd` | `Phelia:` avec la variante `- Phelia, Exuberant Shepherd` | nom court = avant la virgule |
| `Tifa Lockhart` | `Tifa Lockhart:` | pas de virgule : nom complet |
| `Partner WUR` | `Partner WUR:` | pas de virgule : nom complet |
| `Kess, Autre Nom` | `Kess, Autre Nom:` | « Kess » déjà pris : nom complet |
| `Ragavan, Nimble Pilferer` | rien | déjà connu (variante de Ragavan) |

Le bloc ajouté, sous un commentaire daté, sans toucher au reste du fichier :

```yaml
# Ajoutés par l'import du méta du 24/09/2026 (top 20 MTGTop8) : à renommer ou regrouper au besoin.
Phelia:
    - Phelia, Exuberant Shepherd
Cloud:
    - Cloud, Midgar Mercenary
Tifa Lockhart:
Partner WUR:
```

Ensuite, à la main, si besoin :

- **Rattacher un « Partner »** à un duo : `Tymna/Thrasios:` avec la variante `- Partner WUBG`. Au prochain import, sa part s'ajoute à celle du duo.
- **Renommer** une référence (`Slimefoot And Squee` → `Slimefoot`) : garder l'ancien nom en variante, puis relancer `meta`
  pour que le dossier du jour prenne le nouveau nom. Les imports précédents gardent l'ancien.

## 📅 L'historique

```
meta/
├── 2026-09-10/      ← gardé tel quel
├── 2026-09-24/      ← le plus récent : lu par les stats
└── README.md
```

- Un import par jour et par dossier : relancer le même jour **remplace** les deux fichiers du jour (le bilan le dit).
- Les autres dates ne sont **jamais** modifiées : on peut comparer deux périodes, ou vérifier d'où venait un chiffre.
- Les stats lisent toujours le dossier à la date la plus récente.

## ❌ Erreurs et ⚠️ avertissements

| | ❌ Erreur |
|---|---|
| Effet | rien n'est écrit : ni `meta/`, ni `oppos.yaml` |
| Exemples | `oppos.yaml` absent ou incohérent ; MTGTop8 injoignable, trop lent, en erreur ; page vide ou inattendue |
| Que faire | corriger `oppos.yaml`, ou relancer plus tard |

Un oppo inconnu n'est ni une erreur ni un avertissement : il est ajouté à `oppos.yaml`, et le bilan le liste (📝).

## 🛡️ Protection des données

- **Tout est préparé avant la moindre écriture** : une seule erreur suffit à tout annuler.
- **Ordre d'écriture** : le méta d'abord, `oppos.yaml` ensuite. Relancer après une coupure refait le même import sans doublon :
  les oppos déjà ajoutés sont connus et ne sont pas rajoutés.
- **Écriture en deux temps** : fichier `.tmp`, puis renommage d'un coup par-dessus l'original.
- **`oppos.yaml` n'est jamais réécrit** : les ajouts vont à la fin, les commentaires et entrées existantes restent tels quels.
- **Pas de page gardée** : le HTML de MTGTop8 reste en mémoire ; seuls les CSV sont écrits.
- **Tests sans réseau** : deux vraies pages sont enregistrées dans `src/tests/fixtures/`, et le téléchargement est remplacé dans les tests.

## 🧱 Organisation du code

Même architecture que l'import de l'inbox et les stats : chaque couche n'utilise que celles du dessous.

```
src/dcprepa/
├── __main__.py             point d'entrée : module « meta », affiche le bilan
├── services/
│   └── import_meta.py      import_meta, MetaReport, META_LABELS : enchaîne toutes les étapes
├── domain/                 règles pures, sans fichier ni réseau
│   ├── mtgtop8.py          parse_meta_page, MetaPage : HTML → total + parts en ‰
│   ├── meta.py             build_meta, MetaRow, propose_oppos, META_TOP : noms, fusion, poids, top 20
│   └── oppos.py            build_oppo_index (comparaison souple)
└── storage/                seuls accès aux fichiers de data/ et au réseau
    ├── mtgtop8.py          fetch_meta_page, meta_url, META_IDS : téléchargement
    ├── meta.py             write_meta, read_meta, load_latest_meta, META_FILES
    └── oppos.py            load_oppos, append_oppos
```

- Les fonctions de `domain/` et `storage/` renvoient `(résultat, erreurs)` au lieu d'afficher ou d'arrêter le programme.
- `fetch_meta_page()` reçoit la fonction de téléchargement en paramètre, et `import_meta()` reçoit `fetch` : les tests les remplacent.
- Le service renvoie un `MetaReport` (dossier, remplacé ou non, oppos et decks de chaque méta, oppos ajoutés, erreurs) :
  la ligne de commande et l'interface graphique l'affichent chacune à leur façon.
- Chaque fichier a ses tests dans `src/tests/`, rangés de la même façon (`python -m pytest` depuis `src/`).
