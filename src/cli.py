"""Command line interface for administration and Task Scheduler usage."""
from pathlib import Path

import typer

from src.core.config import settings
from src.core.logging_config import configure_logging
from src.db.connection import init_database
from src.etl.pipeline import run_etl
from src.etl.source_copy import update_source_copy
from src.services.analytics import get_status

app = typer.Typer(help="RKI Health Data Monitor administration CLI")


@app.command("init-db")
def init_db_command() -> None:
    init_database()
    typer.echo(f"SQLite database ready: {settings.database_file}")


@app.command("refresh")
def refresh_command(force: bool = typer.Option(False, "--force")) -> None:
    configure_logging()
    result = run_etl(force=force)
    typer.echo(result)


@app.command("update-source-copy")
def update_source_copy_command() -> None:
    """Refresh the offline copy of the RKI GitHub page (README, licence, metadata). Needs internet access."""
    manifest = update_source_copy()
    typer.echo(f"Saved {len(manifest['entries'])} entries of {manifest['repository']} ({manifest['retrieved_at']})")


@app.command("load-test-file")
def load_test_file(path: Path) -> None:
    """Developer/test helper. The dashboard's refresh button never uses this command."""
    configure_logging()
    result = run_etl(force=True, local_file=path)
    typer.echo(result)


@app.command("status")
def status_command() -> None:
    init_database()
    typer.echo(get_status())


@app.command("reset-db")
def reset_db(yes: bool = typer.Option(False, "--yes")) -> None:
    if not yes:
        typer.echo("Aborted. Use --yes to delete the local SQLite database.")
        raise typer.Exit(code=1)
    if settings.database_file.exists():
        settings.database_file.unlink()
        typer.echo(f"Deleted: {settings.database_file}")
    init_database()
    typer.echo("Empty SQLite database recreated.")


if __name__ == "__main__":
    app()
