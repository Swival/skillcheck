"""CLI."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click

from .models import Diagnostic, Level, ValidationResult
from .validator import validate

LEVEL_SYMBOLS = {
    Level.ERROR: "\u2717",  # ✗
    Level.WARNING: "\u26a0",  # ⚠
    Level.INFO: "\u2139",  # ℹ
}

LEVEL_COLORS = {
    Level.ERROR: "red",
    Level.WARNING: "yellow",
    Level.INFO: "blue",
}


@click.command()
@click.argument(
    "directory", type=click.Path(exists=True, file_okay=False, resolve_path=True)
)
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format.",
)
@click.option("--strict", is_flag=True, help="Treat warnings as errors (exit 1).")
@click.option(
    "--agents",
    "agent_names",
    default=None,
    help="Comma-separated agent adapters to run (or 'all'). Auto-detects if omitted.",
)
@click.option(
    "--check",
    "check_names",
    default=None,
    help="Comma-separated check categories: spec, quality, disclosure, agents.",
)
def main(
    directory: str,
    fmt: str,
    strict: bool,
    agent_names: str | None,
    check_names: str | None,
) -> None:
    """Validate agent skills in DIRECTORY against the agentskills.io specification."""
    root = Path(directory)

    agents_list = agent_names.split(",") if agent_names else None
    checks_list = check_names.split(",") if check_names else None

    result = validate(root, agent_names=agents_list, checks=checks_list)

    if fmt == "json":
        click.echo(json.dumps(result.to_dict(), indent=2))
    else:
        _print_text(result)

    sys.exit(result.exit_code(strict))


def _print_text(result: ValidationResult) -> None:
    for skill_name, sd in sorted(result.skills.items()):
        if skill_name == "_cross-skill":
            continue
        click.echo()
        click.secho(f"skills/{skill_name}", bold=True)
        _print_diags(sd.all())

    cross = result.skills.get("_cross-skill")
    if cross and cross.all():
        click.echo()
        click.secho("cross-skill", bold=True)
        _print_diags(cross.all())

    for agent_name, diags in sorted(result.agents.items()):
        click.echo()
        click.secho(f"agents/{agent_name}", bold=True)
        _print_diags(diags)

    click.echo()
    c = result.counts()
    parts = [f"{c['skills']} skills"]
    if c["errors"]:
        parts.append(click.style(f"{c['errors']} errors", fg="red"))
    else:
        parts.append("0 errors")
    if c["warnings"]:
        parts.append(click.style(f"{c['warnings']} warnings", fg="yellow"))
    else:
        parts.append("0 warnings")
    if c["info"]:
        parts.append(f"{c['info']} info")
    click.echo(f"summary: {', '.join(parts)}")


def _print_diags(diags: list[Diagnostic]) -> None:
    for d in diags:
        sym = LEVEL_SYMBOLS[d.level]
        color = LEVEL_COLORS[d.level]
        click.echo(f"  {click.style(sym, fg=color)} [{d.check}] {d.message}")
