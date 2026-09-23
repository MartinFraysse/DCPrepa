# src

Logiciel DCPrepa : importe les parties saisies dans l'inbox vers `games.csv` et génère les rapports de stats d'un tournoi (CLI d'abord, interface graphique plus tard).

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
│   └── interfaces/  # CLI (puis GUI) : seule couche qui affiche
└── tests/           # même arborescence que dcprepa/
```

Point d'entrée : `dcprepa/__main__.py` (lancement minimal, en attendant la vraie CLI dans `interfaces/cli/`).

## Commandes

```bash
# installer les dépendances (PowerShell ; sous Linux : source .venv/bin/activate)
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r src/requirements-dev.txt   # dépendances d'exécution + pytest
# lancer un module sur un tournoi (depuis src/) ; sans argument : liste des modules
python -m dcprepa import relicfest-2026
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
- Code en anglais : noms de fichiers, modules, fonctions, variables, constantes. Les clés des fichiers de `data/` (`parties`, `resultat`…) restent telles quelles ; les messages affichés à l'utilisateur sont en français.
- Chaque dossier de code contient un `__init__.py` (vide) pour être importable.
- Un dossier n'est créé qu'avec son premier fichier ; les tests reproduisent l'arborescence de `dcprepa/`.

## Idée d'ajout

<!-- Tenue par Claude : sections ou informations qui manquent à ce README.
     Une idée par puce : quoi ajouter → pourquoi. L'utilisateur approuve, puis l'idée est intégrée et retirée d'ici. -->
