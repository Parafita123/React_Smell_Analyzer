import json
import os
import shutil
import subprocess
from pathlib import Path

from src.models import Finding


def _find_knip_command(project_path: str) -> list[str] | None:
    project_dir = Path(project_path)

    if os.name == "nt":
        local_knip_cmd = project_dir / "node_modules" / ".bin" / "knip.cmd"
        if local_knip_cmd.exists():
            return ["cmd", "/c", str(local_knip_cmd)]

        global_knip = shutil.which("knip.cmd") or shutil.which("knip")
        if global_knip:
            return ["cmd", "/c", global_knip]

        global_npx = shutil.which("npx.cmd") or shutil.which("npx")
        if global_npx:
            return ["cmd", "/c", global_npx, "-y", "knip"]

        return None

    local_knip = project_dir / "node_modules" / ".bin" / "knip"
    if local_knip.exists():
        return [str(local_knip)]

    if shutil.which("knip"):
        return ["knip"]

    if shutil.which("npx"):
        return ["npx", "-y", "knip"]

    return None


def run_knip_dependency_analysis(project_path: str) -> tuple[list[Finding], list[str]]:
    findings: list[Finding] = []
    errors: list[str] = []

    cmd = _find_knip_command(project_path)
    if cmd is None:
        errors.append("Knip is not available in the target project or on PATH.")
        return findings, errors

    full_cmd = cmd + ["--dependencies", "--reporter", "json"]

    try:
        result = subprocess.run(
            full_cmd,
            cwd=project_path,
            capture_output=True,
            text=True,
            check=False,
        )
    except Exception as exc:
        errors.append(f"Failed to execute Knip: {exc}")
        return findings, errors

    if result.returncode not in (0, 1):
        stderr = result.stderr.strip()
        errors.append(
            f"Knip returned exit code {result.returncode}: {stderr if stderr else 'no stderr output'}"
        )
        return findings, errors

    stdout = result.stdout.strip()
    if not stdout:
        stderr = result.stderr.strip()
        if stderr:
            errors.append(f"Knip returned no JSON output. stderr: {stderr}")
        else:
            errors.append("Knip returned no JSON output.")
        return findings, errors

    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError as exc:
        errors.append(f"Failed to parse Knip JSON output: {exc}")
        return findings, errors

    for issue in payload.get("issues", []):
        file_path = issue.get("file", "unknown")

        for dep in issue.get("dependencies", []):
            findings.append(
                Finding(
                    smell="unused-dependency",
                    dependency=dep.get("name"),
                    severity="medium",
                    evidence={
                        "file": file_path,
                        "line": dep.get("line"),
                        "column": dep.get("col"),
                        "reported_by": "knip",
                        "issue_type": "dependencies",
                    },
                    message=(
                        f"Dependency '{dep.get('name')}' appears to be unused "
                        f"according to Knip."
                    ),
                )
            )

        for dep in issue.get("devDependencies", []):
            findings.append(
                Finding(
                    smell="unused-dependency",
                    dependency=dep.get("name"),
                    severity="medium",
                    evidence={
                        "file": file_path,
                        "line": dep.get("line"),
                        "column": dep.get("col"),
                        "reported_by": "knip",
                        "issue_type": "devDependencies",
                    },
                    message=(
                        f"Dev dependency '{dep.get('name')}' appears to be unused "
                        f"according to Knip."
                    ),
                )
            )

        for dep in issue.get("unlisted", []):
            findings.append(
                Finding(
                    smell="missing-dependency",
                    dependency=dep.get("name"),
                    severity="high",
                    evidence={
                        "file": file_path,
                        "line": dep.get("line"),
                        "column": dep.get("col"),
                        "reported_by": "knip",
                        "issue_type": "unlisted",
                    },
                    message=(
                        f"Dependency '{dep.get('name')}' appears to be used but is "
                        f"not listed in package.json according to Knip."
                    ),
                )
            )

    return findings, errors