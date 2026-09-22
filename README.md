# DCPrepa

Suivie de préparation de gros tournois DC, entrainement analyse méta winrate etc...

## Organisation du dépôt

```
.
├── .claude/
│   ├── CLAUDE.md          # consignes de Claude Code (rôle, règles, journal)
│   ├── SESSION_LOG.md     # journal des sessions (mémoire entre sessions)
│   └── settings.json      # hook SessionStart : charge le journal au démarrage
├── docs/
│   ├── .claude_doc.md     # notes de Claude, tenues en temps réel (hors PDF et hors ~/work)
│   └── README.md          # règles de la documentation
├── src/
│   └── README.md          # stack, organisation et commandes du code
├── .editorconfig          # style commun à tous les éditeurs
├── .git.md                # aide-mémoire des commandes git du projet
├── .gitignore             # fichiers exclus de git (secrets, dépendances, builds)
├── .init.md               # aide-mémoire pour initialiser un projet
└── README.md
```

Les fichiers de la racine s'appliquent à tout le dépôt ; le code vit dans `src/`, la documentation dans `docs/`.

## Stratégie de branches : trunk-based development

- `main` est la **seule branche permanente**. Elle doit toujours rester stable.
- Tout travail se fait sur une **branche courte** (quelques heures, 2 jours maximum), créée depuis `main`.
- Une branche courte revient dans `main` **uniquement via une Pull Request**.
- Exception : les branches de release figées (`release/<version>`), qui ne reçoivent que des correctifs par cherry-pick.

## Convention de nommage des branches

Format : `<type>/<description>`

| Type       | Usage                                           | Exemple                   |
|------------|-------------------------------------------------|---------------------------|
| `feat`     | Nouvelle fonctionnalité                         | `feat/page-connexion`     |
| `fix`      | Correction de bug                               | `fix/crash-au-demarrage`  |
| `docs`     | Documentation uniquement                        | `docs/guide-contribution` |
| `chore`    | Maintenance, configuration, outillage           | `chore/update-gitignore`  |
| `refactor` | Restructuration sans changement de comportement | `refactor/module-auth`    |
| `test`     | Ajout ou correction de tests                    | `test/api-utilisateurs`   |
| `ci`       | Pipeline d'intégration continue                 | `ci/github-actions`       |

Règles : minuscules, mots séparés par des tirets, pas d'espaces ni d'accents.

Les messages de commit suivent le même vocabulaire ([Conventional Commits](https://www.conventionalcommits.org/fr/)) :
`<type>(<scope>): <description>` — par exemple `feat(auth): ajoute la connexion`.

## Règle de merge

- **Aucun push direct sur `main`** : uniquement des Pull Request.
- La PR doit être à jour avec `main` et passer les vérifications avant d'être fusionnée.
- Mode de merge : **Squash and merge**.
- La branche est **supprimée après le merge**.

## Workflow type

```bash
git switch main && git pull              # partir d'un main à jour
git switch -c feat/ma-fonctionnalite     # créer une branche courte
# ... travailler, committer ...
git push -u origin feat/ma-fonctionnalite
# ouvrir la Pull Request sur GitHub, puis Squash and merge
git switch main && git pull              # récupérer le résultat
git branch -D feat/ma-fonctionnalite     # nettoyer la branche locale (-D : le squash crée un nouveau commit)
```
