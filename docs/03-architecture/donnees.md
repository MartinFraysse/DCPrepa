# Organisation des données

> Comment le dossier `data/` est rangé, à quoi sert chaque fichier, et pourquoi ces formats et ces conventions.
> Pour préparer un nouveau tournoi, modifier un fichier à la main ou faire évoluer le logiciel sans casser les données.

## Contexte

DCPrepa n'a pas de base de données : **toutes les données sont des fichiers texte**, rangés dans `data/` et versionnés avec git.

- ✍️ **Éditables à la main**, depuis l'ordinateur ou le téléphone (via GitHub), sans logiciel particulier.
- 🔍 **Lisibles et comparables** : chaque modification apparaît dans l'historique git, ligne par ligne.
- 💾 **Sauvegardées** avec le dépôt : un `git push` suffit.
- 🧩 **Le logiciel n'est qu'un outil** : il lit et écrit ces fichiers, mais les données restent lisibles et modifiables sans lui.

## Vue d'ensemble

```
data/
├── oppos.yaml                        decks adverses, commun à tous      🌍
├── templates/
│   └── tournament/                   modèle d'un dossier de tournoi     📋
└── tournaments/
    ├── mon-tournoi/                  un dossier par tournoi préparé     🏆
    │   ├── tournament.yaml           fiche du tournoi
    │   ├── decks/                    mes decks et leurs versions
    │   │   ├── terra-5c.yaml
    │   │   ├── tymna-thrasios.yaml
    │   │   └── _alias.yaml           appellations acceptées des decks
    │   ├── inbox.yaml                saisies à importer                 📥
    │   ├── games.csv                 games jouées, 1 ligne par game     📊
    │   ├── meta/                     instantanés du méta (MTGTop8)      🌍
    │   │   └── 2027-01-15/           un dossier par import
    │   │       ├── general.csv
    │   │       └── paper.csv
    │   └── stats/                    rapports générés                   📈
    │       ├── synthese.md
    │       └── terra-5c.md
    └── autre-tournoi/
        └── ...
```

## 🌍 Commun ou par tournoi ?

Chaque donnée est rangée au niveau où elle a du sens :

| Donnée | Niveau | Pourquoi |
|---|---|---|
| decks adverses et leurs appellations (`oppos.yaml`) | **commun** | Ragavan reste Ragavan d'un tournoi à l'autre : on ne ressaisit pas les noms |
| mes decks et leurs versions (`decks/`) | par tournoi | les decks envisagés changent selon le tournoi et la banlist |
| games jouées (`games.csv`) | par tournoi | on prépare un tournoi précis ; les stats restent séparées |
| méta (`meta/`) | par tournoi | le méta change d'un tournoi à l'autre (date, région, banlist) |
| rapports (`stats/`) | par tournoi | ils décrivent la préparation d'un tournoi |

Le nom du dossier d'un tournoi (son **slug**, ex. `mon-tournoi`) est en minuscules, sans espace ni accent.
C'est lui qu'on donne aux commandes : `python -m dcprepa import mon-tournoi`.

## 📋 Le modèle de tournoi

`data/templates/tournament/` contient un dossier de tournoi **vide mais complet** : tous les fichiers,
avec leurs en-têtes et leurs commentaires d'aide, sans aucune donnée.

**Son utilité** : créer un tournoi se fait en une copie, sans oublier de fichier ni se tromper de format.
Le logiciel ne lit jamais ce dossier.

```
data/templates/tournament/                      data/tournaments/mon-tournoi/
├── README.md          mode d'emploi                 (supprimé après la copie)
├── tournament.yaml    champs vides     ──copie──>   à remplir
├── decks/
│   ├── _modele.yaml   fiche deck vierge   ──>       copié en terra-5c.yaml, ...
│   └── _alias.yaml    exemple commenté              à compléter au besoin
├── inbox.yaml         en-tête d'aide                prêt, rien à modifier
├── games.csv          en-tête seul                  prêt, rien à modifier
├── meta/README.md     format des fichiers           prêt
└── stats/
    ├── README.md          conventions des rapports
    ├── synthese.md        rapport-modèle
    └── _modele-deck.md    rapport-modèle d'un deck
```

Créer un tournoi :

```
cp -r data/templates/tournament data/tournaments/mon-tournoi
```

Puis : remplir `tournament.yaml`, créer une fiche par deck à partir de `decks/_modele.yaml`, et supprimer le `README.md` copié.

## 📄 Les fichiers, un par un

Deux familles de fichiers :

| Famille | Fichiers | Rempli par |
|---|---|---|
| ✍️ **Saisie** | `tournament.yaml`, `decks/`, `oppos.yaml`, `inbox.yaml` | le logiciel ou à la main, au choix |
| 🧩 **Produits** | `games.csv`, `meta/*/*.csv`, `stats/*.md` | le logiciel uniquement, jamais modifiés à la main |

Les fichiers produits découlent des fichiers de saisie : les retoucher à la main les désynchroniserait.

### `tournament.yaml` : la fiche du tournoi

```yaml
name: Mon Tournoi 2027        # nom affiché
slug: mon-tournoi             # = nom du dossier
format: Duel Commander
date: 15/01/2027              # JJ/MM/AAAA
location: Lyon
banlist:                      # date ou lien de la banlist en vigueur
notes:
```

Pas de liste des decks ici : le dossier `decks/` et le champ `statut` de chaque fiche suffisent.

### `decks/<deck>.yaml` : une fiche par deck

```yaml
name: Terra 5C
commandant: Terra, Magical Adept     # nom exact de la carte (face avant si double face)
statut: envisage                     # envisage | retenu | ecarte
versions:
    -   version: v1
        liste: |                     # export MTGO / Moxfield, 100 cartes
                1 Abrupt Decay
                1 Arcane Signet
    -   version: v2
        in:
            - Swords to Plowshares
        out:
            - Arcane Signet
        notes: Plus de removal contre l'aggro.
```

- Le **nom du fichier** (`terra-5c`) est l'identifiant du deck : c'est lui qu'on retrouve dans `games.csv`.
- Les versions vont de la plus ancienne à la plus récente. La `v1` porte la liste complète ;
  les suivantes peuvent ne décrire que la différence (`in` / `out`).
- Pas de date sur les versions, et pas de sideboard (il n'y en a pas en Duel Commander).

### `decks/_alias.yaml` : les appellations des decks

```yaml
terra-5c:
    - Terra
    - Terra mid
```

Facultatif. Il permet d'écrire « terra mid » dans l'inbox. Le nom du fichier et le champ `name` sont déjà reconnus sans lui.

### `oppos.yaml` : les decks adverses

```yaml
Ragavan:
    - Ragavan, Nimble Pilferer
    - raga
Tymna/Thrasios:
    - Tymna Thrasios
```

Nom de référence (le nom court du commandant, `/` entre deux partenaires) puis ses variantes.
C'est le nom de référence qui est écrit dans `games.csv` et dans `meta/`, pour qu'un même deck adverse n'ait qu'un nom partout.

Le fichier se remplit aussi tout seul : à chaque import du méta (commande `meta`), les oppos du top 20 qui n'y sont pas
encore sont **ajoutés à la fin**, sous un commentaire daté, sans toucher au reste :

```yaml
# Ajoutés par l'import du méta du 24/09/2026 (top 20 MTGTop8) : à renommer ou regrouper au besoin.
Phelia:
    - Phelia, Exuberant Shepherd
Partner WUR:
```

Nom court (avant la virgule) en référence et nom complet MTGTop8 en variante ; sans virgule, ou si le nom court est déjà pris,
le nom complet seul. On peut ensuite les renommer, ou rattacher un « Partner » à un duo en l'ajoutant comme variante (voir [Import du méta](import-meta.md)).

### `inbox.yaml` : la boîte de réception

Les sessions saisies loin de l'ordinateur, un bloc par session, en attente d'import.
Son fonctionnement complet est décrit dans la page [Import de l'inbox](import-inbox.md).

### `games.csv` : les games jouées

Une ligne par **game** ; toutes les games d'un même BO partagent un `match_id`.

```
date,match_id,game,source,deck,version,oppo,position,resultat,note/ressenti
15/01/2027,15/01/2027-01,1,paper,terra-5c,v2,Ragavan,OTP,W,Matchup jouable
15/01/2027,15/01/2027-01,2,paper,terra-5c,v2,Ragavan,OTD,W,Matchup jouable
15/01/2027,15/01/2027-02,1,mtgo,terra-5c,v2,Tymna/Thrasios,OTD,L,
```

| Colonne | Contenu |
|---|---|
| `date` | jour de la session, JJ/MM/AAAA |
| `match_id` | identifiant du BO : `JJ/MM/AAAA-NN`, numéroté dans l'ordre de saisie |
| `game` | numéro de la game dans le BO (1, 2, 3) |
| `source` | `paper`, `mtgo` ou `cockatrice` |
| `deck`, `version` | mon deck (nom de sa fiche) et la version jouée |
| `oppo` | nom de référence du deck adverse, ou `deck@version` en self-play |
| `position` | `OTP` (je commence) ou `OTD` |
| `resultat` | `W` ou `L` : une game n'est jamais nulle, seul un BO peut l'être (1-1) |
| `note/ressenti` | commentaire de la session, recopié sur chacune de ses lignes |

Une ligne par game plutôt qu'une ligne par BO : chaque stat (OTP/OTD, par game, par BO) se calcule directement,
et une ligne se suffit à elle-même dans un tableur.

### `meta/` : le méta du tournoi

Un dossier par import depuis MTGTop8, nommé d'après sa date ; les imports précédents sont gardés. Les stats utilisent le plus récent.

```
meta/
├── 2027-01-01/              import précédent, gardé pour vérifier
│   ├── general.csv
│   └── paper.csv
└── 2027-01-15/              le plus récent : lu par les stats
    ├── general.csv          méta général des 2 derniers mois (paper + MTGO)
    └── paper.csv            méta papier des 2 derniers mois
```

Les deux fichiers ont le même format, les 20 oppos les plus joués de chaque méta :

```
oppo,decks,poids
Phelia,84,5.81
Cloud,83,5.74
```

`oppo` est ramené au nom de référence de `oppos.yaml`, `decks` estime les listes sur la période,
`poids` est la part réelle du méta en % (le top 20 ne fait donc pas 100 %). Voir [Import du méta](import-meta.md).

### `stats/` : les rapports

Des fichiers Markdown **générés** à partir de `games.csv`, `decks/`, `meta/` et `oppos.yaml`,
lisibles directement sur GitHub. Ils sont réécrits à chaque génération : on ne les modifie pas.

- `synthese.md` : tous les decks côte à côte, poids des oppos dans le méta, winrate attendu, matchups peu testés.
- `<deck>.md` : le détail d'un deck (général, versions, OTP/OTD, sources, matchups, self-play à part).

Leurs règles de calcul sont dans `stats/README.md`.

## 🗂️ Choix des formats

Chaque format a été choisi selon **qui** écrit le fichier et **comment** il grandit :

| Format | Utilisé pour | Pourquoi |
|---|---|---|
| **YAML** | fiches, `inbox.yaml`, `oppos.yaml`, `_alias.yaml` | écrit à la main : lisible, commentable (`#`), pas de guillemets ni d'accolades à gérer, facile à taper au téléphone |
| **CSV** | `games.csv`, `meta/` | données en tableau, une ligne par enregistrement : s'ouvre dans un tableur, s'allonge par simple ajout de lignes, facile à lire pour le logiciel |
| **Markdown** | `stats/`, README | rapports à lire : tableaux et titres affichés proprement sur GitHub |

## 📏 Conventions

| Règle | Exemple | Pourquoi |
|---|---|---|
| Dates au format **JJ/MM/AAAA**, partout où une date est saisie ou lue | `15/01/2027`, `15/01/2027-01` | un seul format à retenir |
| Exception : dossiers de `meta/` en **AAAA-MM-JJ** | `2027-01-15/` | le `/` est interdit dans un nom de dossier, et cet ordre trie les imports par date |
| Identifiants (dossiers, fichiers) en **minuscules**, avec des tirets | `mon-tournoi`, `terra-5c` | pas d'espace ni d'accent : sans risque dans les commandes et les chemins |
| Versions préfixées par **v** | `v1`, `v2` | sans le `v`, YAML lirait `1.10` comme le nombre `1.1` |
| Valeurs fixes **sans accent** | `envisage`, `ecarte` | comparées telles quelles par le logiciel |
| Self-play noté **`deck@version`** | `tymna-thrasios@v1` | un oppo qui est l'un de mes decks, exclu des stats générales |
| Fichier qui commence par **`_`** : pas une donnée ordinaire | `_modele.yaml`, `_alias.yaml` | le logiciel ne le prend pas pour une fiche deck |
| Fichiers en **UTF-8** | — | accents et caractères spéciaux lus correctement partout |

Les fins de ligne (Windows ou Linux) de chaque fichier sont conservées par le logiciel quand il y écrit.

## 🔄 Le trajet des données

Les données passent par deux étapes : on range d'abord ce qui est saisi, puis on calcule les stats.

**Étape 1 : ranger les données** (commandes `import` et `meta`)

```
 inbox.yaml          ──import──>   games.csv     les games saisies
 MTGTop8 (site web)  ──meta────>   meta/<date>/  le méta du moment (+ nouveaux oppos dans oppos.yaml)
```

**Étape 2 : calculer les stats** (commande `stats`)

```
 games.csv    ─┐
 meta/<date>/ ─┤
 decks/       ─┼──stats──>   stats/*.md   les rapports à lire
 oppos.yaml   ─┘
```

- ✍️ **Fichiers de saisie** : `inbox.yaml`, `decks/` et `oppos.yaml`. Ils sont remplis par le logiciel ou à la main.
- 🧩 **Fichiers produits** : `games.csv`, `meta/` et `stats/`. Ils découlent des précédents et ne se modifient jamais à la main.
