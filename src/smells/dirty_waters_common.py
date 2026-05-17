import re
from pathlib import Path

from src.models import Finding
from src.external_tools.dirty_waters_adapter import run_dirty_waters_check


DIRTY_WATERS_SMELL_CONFIG = {
    "deprecated-dependency": {
        "severity": "medium",
        "flags": ["--check-deprecated"],
        "summary_patterns": [
            r"Packages that are deprecated .*:\s*(\d+)",
        ],
        "message": "Dirty-Waters reported deprecated dependencies.",
    },
    "no-source-code-link": {
    "severity": "high",
    "flags": ["--check-source-code"],
    "summary_patterns": [
        r"Packages with no source code URL .*:\s*(\d+)",
        r"Packages with repo URL that is 404 .*:\s*(\d+)",
    ],
    "message": "Dirty-Waters reported dependencies with missing or invalid source code repository links.",
    },
    "no-source-code-sha": {
    "severity": "medium",
    "flags": ["--check-source-code", "--check-source-code-sha"],
    "summary_patterns": [
        r"Packages with inaccessible commit SHA/tag .*:\s*(\d+)",
        r"Packages .*commit SHA.*:\s*(\d+)",
        r"Packages .*release tag.*:\s*(\d+)",
    ],
    "message": "Dirty-Waters reported dependencies without a valid tag or commit SHA for the release.",
    },
    "depends-on-fork": {
        "severity": "low",
        "flags": ["--check-source-code", "--check-forks"],
        "summary_patterns": [
            r"Packages .*fork.*:\s*(\d+)",
        ],
        "message": "Dirty-Waters reported dependencies that depend on forks.",
    },
    "no-build-attestation": {
        "severity": "low",
        "flags": ["--check-provenance"],
        "summary_patterns": [
            r"Packages .*build attestation.*:\s*(\d+)",
            r"Packages .*provenance.*:\s*(\d+)",
        ],
        "message": "Dirty-Waters reported dependencies without build attestation.",
    },
    "no-invalid-code-signature": {
        "severity": "medium",
        "flags": ["--check-code-signature"],
        "summary_patterns": [
            r"Packages .*code signature.*:\s*(\d+)",
        ],
        "message": "Dirty-Waters reported dependencies with missing or invalid code signatures.",
    },
    "aliased-packages": {
        "severity": "low",
        "flags": ["--check-aliased-packages"],
        "summary_patterns": [
            r"Packages .*aliased.*:\s*(\d+)",
        ],
        "message": "Dirty-Waters reported aliased packages.",
    },
}


def _extract_summary_count(report_text: str, patterns: list[str]) -> int | None:
    counts = []

    for pattern in patterns:
        match = re.search(pattern, report_text, re.IGNORECASE)
        if match:
            counts.append(int(match.group(1)))

    if not counts:
        return None

    return sum(counts)


def _try_read_report_from_unc_path(user_report_location: str | None) -> str | None:
    if not user_report_location:
        return None

    try:
        report_path = Path(user_report_location)
        if report_path.exists():
            return report_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return None

    return None


def run_dirty_waters_smell(smell_name: str, **kwargs) -> list[Finding]:
    repo_name = kwargs.get("repo_name")
    backend = kwargs.get("dirty_waters_backend", "disabled")
    wsl_distro = kwargs.get("wsl_distro", "Ubuntu")
    dirty_waters_root = kwargs.get("dirty_waters_root", "/home/parafita/dirty-waters")

    if not repo_name:
        raise RuntimeError("Dirty-Waters-based smells require --repo owner/repo.")

    config = DIRTY_WATERS_SMELL_CONFIG[smell_name]

    result, errors = run_dirty_waters_check(
        repo_name=repo_name,
        package_manager="npm",
        check_flags=config["flags"],
        backend=backend,
        wsl_distro=wsl_distro,
        dirty_waters_root=dirty_waters_root,
    )

    if errors:
        raise RuntimeError(" | ".join(errors))

    report_text = result.report_text or ""

    if not report_text:
        fallback_report_text = _try_read_report_from_unc_path(result.user_report_location)
        if fallback_report_text:
            report_text = fallback_report_text

    count = _extract_summary_count(report_text, config["summary_patterns"])

    if count is None:
        note_suffix = f" Dirty-Waters note: {result.note}" if result.note else ""
        location_suffix = (
            f" Open report at: {result.user_report_location}"
            if result.user_report_location
            else f" See report at: {result.report_path}"
        )
        raise RuntimeError(
            f"Could not parse Dirty-Waters report for '{smell_name}'."
            f"{location_suffix}{note_suffix}"
        )

    if count == 0:
        return []

    message = f"{config['message']} Count reported by Dirty-Waters: {count}."
    if result.note:
        message += f" {result.note}"

    return [
        Finding(
            smell=smell_name,
            dependency=None,
            severity=config["severity"],
            evidence={
                "reported_by": "dirty-waters",
                "repo_name": repo_name,
                "report_path": result.report_path,
                "user_report_location": result.user_report_location,
                "count": count,
                "check_flags": config["flags"],
                "note": result.note,
            },
            message=message,
        )
    ]