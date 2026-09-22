# Documentation

Ce dossier contient toute la documentation du projet, et ce fichier explique comment elle est organisée.

## Principe

Une seule source, deux formats.

```
docs/*.md  (source, versionnée)
   │
   ├──▶ PDF général      : tout le projet en un seul document, généré, jamais édité à la main
   │
   └──▶ arborescence .md : copiée telle quelle dans la documentation locale (~/work)
```

- **Le Markdown est la source de vérité.** On écrit et on corrige uniquement les fichiers `.md`.
- **Le PDF est un export.** Il assemble tous les chapitres, dans l'ordre de leur numéro.
- **L'arborescence est autonome.** Liens relatifs et images locales : elle se lit et se copie sans dépendre du reste du dépôt.
- **Les fichiers cachés restent privés.** Tout fichier de `docs/` dont le nom commence par un point (`.claude_doc.md`) est exclu du PDF et de la copie vers `~/work`.

### `.claude_doc.md` : les notes de Claude

Claude y tient en temps réel, sans demander, une description de l'état actuel du projet (voir `.claude/CLAUDE.md`).
C'est un brouillon de travail, pas de la documentation officielle : il n'est **ni dans le PDF, ni dans `~/work`**.
Quand une information mérite d'être publiée, elle est réécrite proprement dans le chapitre concerné, sur demande.

## Arborescence

Le modèle s'inspire de [Diátaxis](https://diataxis.fr/) : chaque page répond à **un seul** besoin
(apprendre, faire, chercher une information, comprendre).

```
docs/
├── README.md                   # ce fichier : règles de la documentation
├── .claude_doc.md              # notes de Claude (privé : hors PDF, hors ~/work)
├── 01-presentation/            # comprendre QUOI et POURQUOI
│   ├── index.md                #   contexte, objectifs, périmètre, non-objectifs
│   └── glossaire.md            #   vocabulaire du projet
├── 02-guides/                  # FAIRE une tâche, pas à pas
│   ├── index.md                #   liste des guides
│   ├── installation.md
│   └── utilisation.md
├── 03-architecture/            # comprendre COMMENT c'est construit
│   ├── index.md                #   vue d'ensemble, composants, flux
│   └── decisions/              #   décisions d'architecture (ADR)
│       └── 0001-<titre>.md
├── 04-reference/               # CHERCHER une information précise
│   ├── index.md
│   ├── configuration.md        #   variables, fichiers de config
│   └── commandes.md            #   CLI, scripts, API
├── 05-exploitation/            # FAIRE TOURNER le projet
│   ├── index.md
│   ├── deploiement.md
│   ├── securite.md
│   └── depannage.md            #   problèmes connus et solutions
├── assets/                     # images et schémas, rangés par chapitre
│   └── 03-architecture/
└── pdf/
    └── <projet>.pdf            # PDF général généré
```

Tous les chapitres ne sont pas obligatoires : on crée un dossier quand il a du contenu, en gardant son numéro.
On ajoute un chapitre en prenant le numéro suivant (`06-...`) ; on ne renumérote jamais les chapitres existants.

### Quel chapitre choisir ?

| Je veux…                                   | Chapitre           |
|--------------------------------------------|--------------------|
| Expliquer ce qu'est le projet et à quoi il sert | `01-presentation` |
| Montrer comment réaliser une tâche          | `02-guides`        |
| Décrire les composants et justifier un choix | `03-architecture` |
| Lister des options, commandes, paramètres    | `04-reference`     |
| Déployer, sécuriser, dépanner                | `05-exploitation`  |

## Conventions

- **Noms :** minuscules, tirets, sans accents ni espaces (`guide-installation.md`).
- **Numéros :** `NN-` sur les dossiers de chapitre uniquement ; ils fixent l'ordre dans le PDF.
- **`index.md` :** chaque chapitre en a un. Il présente le chapitre et renvoie vers ses pages.
- **Titres :** un seul `#` par page (le titre), puis `##` et `###`. Le PDF construit sa table des matières à partir de ces niveaux.
- **Liens :** toujours relatifs (`../04-reference/commandes.md`), jamais de chemin absolu ni de lien vers `~/work`.
- **Images :** dans `assets/<chapitre>/`, référencées en relatif, avec un texte alternatif.
- **Schémas :** ASCII ou Mermaid dans le Markdown quand c'est possible, pour rester lisibles et comparables dans git.
- **Langue :** français. Les termes techniques courants restent en anglais (commit, branche, hook).

## Modèle de page

```markdown
# Titre de la page

> Résumé en une phrase : ce que la page apporte et à qui.

## Contexte
Pourquoi cette page existe.

## Contenu
Le cœur de la page.

## Voir aussi
- [Page liée](../04-reference/commandes.md)
```

## Décisions d'architecture (ADR)

Chaque choix important (outil, structure, compromis) a sa fiche dans `03-architecture/decisions/`,
numérotée dans l'ordre (`0001-choix-du-langage.md`). Une fiche n'est jamais réécrite :
si la décision change, on crée une nouvelle fiche qui remplace l'ancienne.

```markdown
# 0001 — Titre de la décision

- **Date :** AAAA-MM-JJ
- **Statut :** proposée | acceptée | remplacée par 000X

## Contexte
Le problème à résoudre.

## Décision
Ce qui a été choisi.

## Conséquences
Ce que ça implique, en bien comme en mal.
```

## Le PDF général

- Il assemble les chapitres dans l'ordre : `index.md` d'abord, puis les autres pages du dossier.
- Il commence par une page de garde (nom du projet, date, version) et une table des matières.
- Il est régénéré à chaque version publiée, pas à chaque modification.
- On ne le modifie jamais directement : on corrige le `.md`, puis on régénère.

## Qui écrit la documentation

- Les pages de `docs/` sont écrites par l'utilisateur, ou par Claude **uniquement sur demande**.
- Claude n'écrit seul que dans `.claude_doc.md`, ses notes privées.

## Quand mettre la documentation à jour

- Un comportement change → la page concernée change dans le même commit (`docs:` si la doc seule change).
- Un choix important est fait → une nouvelle fiche ADR.
- Une nouvelle version est publiée → le PDF est régénéré.

La documentation du projet (`docs/`) est distincte du journal de travail avec Claude (`.claude/SESSION_LOG.md`).
