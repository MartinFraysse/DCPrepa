from pathlib import Path


def write_report(path: Path, text: str) -> None:
    """Écrit un rapport de stats (stats/<deck>.md), en remplaçant l'ancien.

    Le dossier est créé s'il manque. L'écriture passe par un fichier temporaire remplacé d'un coup :
    le rapport n'est jamais écrit à moitié.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as file:
        file.write(text)
    temporary.replace(path)
