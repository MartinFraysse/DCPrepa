# src

Logiciel DCPrepa : importe les games saisies dans l'inbox vers `games.csv` et génère les rapports de stats d'un tournoi (CLI d'abord, interface graphique plus tard).

## Stack

| Élément                  | Choix |
|--------------------------|-------|
| Langage et version       | Python 3.13 |
| Dépendances principales  | PyYAML ; développement : pytest |
| Gestion des dépendances  | pip + venv (`.venv/` à la racine), `src/requirements.txt` (exécution), `src/requirements-dev.txt` (développement) |

## Organisation

```
src/
├── dcprepa/
│   ├── domain/      # règles métier pures : aucun fichier lu, rien d'affiché
│   ├── storage/     # seul endroit qui lit / écrit dans data/ (YAML, CSV)
│   ├── services/    # cas d'usage : enchaîne domain + storage, renvoie un rapport
│   └── interfaces/  # GUI (à venir) : seule couche qui affiche
└── tests/           # même arborescence que dcprepa/
    └── fixtures/    # pages web enregistrées (MTGTop8) : tests sans réseau
```

Point d'entrée : `dcprepa/__main__.py` (lancement minimal, gardé pour dépanner ; pas de CLI complète prévue, la GUI sera la seule interface).

## Commandes

```bash
# installer les dépendances (PowerShell ; sous Linux : source .venv/bin/activate)
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r src/requirements-dev.txt   # dépendances d'exécution + pytest
# lancer un module (depuis src/) ; liste des modules : python -m dcprepa --help ; options : python -m dcprepa <module> --help
python -m dcprepa import relicfest-2026
python -m dcprepa meta relicfest-2026     # méta MTGTop8 (général + papier) → meta/AAAA-MM-JJ/, complète data/oppos.yaml
python -m dcprepa stats relicfest-2026    # écrit stats/<deck>.md pour chaque fiche deck + stats/synthese.md
# saisie sans ouvrir de fichier (tout ou rien, mêmes contrôles que l'import)
python -m dcprepa tournament-create "RelicFest 2026" --date 31/10/2026      # aussi : tournament-edit
python -m dcprepa deck-create relicfest-2026 "Kinnan Combo" --liste kinnan.txt  # aussi : deck-version, deck-status, deck-edit, deck-alias
python -m dcprepa game-add relicfest-2026 --source paper --deck Terra --version v1 --oppo Ragavan --games "OTP W, OTD L, OTP W"
python -m dcprepa game-edit relicfest-2026 02/10/2026-01 2 --resultat W   # aussi : bo-edit, game-delete, bo-delete
python -m dcprepa oppo-add Ragavn --variant-of Ragavan
# tester (depuis src/)
python -m pytest
# linter / formater
```

## Configuration

<!-- Variables d'environnement utilisées : nom → rôle → valeur par défaut.
     Les valeurs réelles vont dans `.env` (ignoré par git) ; un `.env.example` liste les variables sans leurs valeurs. -->

## Conventions

- Un « module » lançable = un service de `services/`, déclaré dans la table `MODULES` de `__main__.py` (nom → fonction d'affichage) ;
  la future GUI appellera directement les services.
- Découpage en couches : `interfaces` → `services` → `domain` et `storage`. Une couche n'importe que celles du dessous.
- `domain/` et `services/` ne font jamais de `print`, `input` ni `sys.exit` : ils renvoient des données ou lèvent une erreur avec un message clair.
- Code en anglais : noms de fichiers, modules, fonctions, variables, constantes. Les clés des fichiers de `data/` (`games`, `resultat`…) restent telles quelles ; les messages affichés à l'utilisateur sont en français.
- Chaque dossier de code contient un `__init__.py` (vide) pour être importable.
- Un dossier n'est créé qu'avec son premier fichier ; les tests reproduisent l'arborescence de `dcprepa/`.

## Idée d'ajout

<!-- Tenue par Claude : sections ou informations qui manquent à ce README.
     Une idée par puce : quoi ajouter → pourquoi. L'utilisateur approuve, puis l'idée est intégrée et retirée d'ici. -->
