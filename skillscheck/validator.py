"""Top-level validate() that ties everything together."""

from __future__ import annotations

from pathlib import Path

from .agents import cross_agent_check, get_adapters
from .checks import spec, quality, disclosure
from .models import ValidationResult
from .parser import discover_skills, parse_skill


def validate(
    root: Path,
    agent_names: list[str] | None = None,
    checks: list[str] | None = None,
) -> ValidationResult:
    result = ValidationResult()
    run_checks = set(checks) if checks else {"spec", "quality", "disclosure", "agents"}

    skill_dirs = discover_skills(root)
    skills = [parse_skill(d) for d in skill_dirs]

    adapters = get_adapters(agent_names, root) if "agents" in run_checks else []
    extension_fields: set[str] = set()
    adapters_authorizing_list_tools: bool = False
    for adapter in adapters:
        fields = adapter.known_frontmatter_fields()
        extension_fields |= fields
        if adapter.allows_tools_list_syntax():
            adapters_authorizing_list_tools = True

    for skill in skills:
        result.ensure_skill(skill.dir_name)
        if "spec" in run_checks:
            for d in spec.check_skill(
                skill, extension_fields, adapters_authorizing_list_tools
            ):
                result.add_skill(skill.dir_name, "spec", d)

        if "quality" in run_checks:
            for d in quality.check_skill(skill):
                result.add_skill(skill.dir_name, "quality", d)

        if "disclosure" in run_checks:
            for d in disclosure.check_skill(skill):
                result.add_skill(skill.dir_name, "disclosure", d)

    if "spec" in run_checks:
        for d in spec.check_cross_skill(skills):
            result.add_skill("_cross-skill", "spec", d)

    if "agents" in run_checks:
        for adapter in adapters:
            for d in adapter.check(root, skills):
                result.add_agent(adapter.name, d)

        cross_diags = cross_agent_check(root, adapters)
        for d in cross_diags:
            result.add_agent("cross-agent", d)

    return result
