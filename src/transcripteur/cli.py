"""Interface en ligne de commande pour Transcripteur."""

from typing import Optional

import typer

app = typer.Typer(help="Transcrire des vidéos et fichiers audio en français avec Whisper.")

__version__ = "0.1.0"


def format_timestamp(seconds: float) -> str:
    """Formater un timestamp simple HH:MM:SS.mmm à partir d'un float de secondes."""

    total_ms = int(seconds * 1000)
    total_s, ms = divmod(total_ms, 1000)
    h, rem = divmod(total_s, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


@app.command(name="version")
def version_command() -> None:
    """Afficher la version du package."""
    typer.echo(f"Transcripteur v{__version__}")


# Enregistrement des commandes depuis les sous-modules
import transcripteur.commands.doctor  # noqa: E402, F401
import transcripteur.commands.benchmark  # noqa: E402, F401
import transcripteur.commands.mic  # noqa: E402, F401
import transcripteur.commands.transcribe  # noqa: E402, F401


def main(argv: "list[str] | None" = None) -> None:
    """Point d'entrée principal."""
    app(prog_name="transcripteur", args=argv)
