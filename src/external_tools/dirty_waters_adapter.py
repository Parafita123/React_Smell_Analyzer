import os
import re
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class DirtyWatersResult:
    stdout: str
    report_path: str | None
    report_text: str | None
    user_report_location: str | None = None
    note: str | None = None


def _windows_to_wsl_path(path: str) -> str:
    path = str(Path(path).resolve())
    drive = path[0].lower()
    rest = path[2:].replace("\\", "/")
    return f"/mnt/{drive}{rest}"


def _extract_report_path(stdout_text: str) -> str | None:
    match = re.search(
        r"Report from static analysis generated at (.+)",
        stdout_text,
    )
    if not match:
        return None
    return match.group(1).strip()


def _linux_path_to_wsl_unc(linux_path: str, distro: str) -> str:
    linux_path = linux_path.strip().replace("/", "\\")
    if not linux_path.startswith("\\"):
        linux_path = "\\" + linux_path
    return f"\\\\wsl.localhost\\{distro}{linux_path}"


def _resolve_absolute_report_path(
    relative_report_path: str,
    dirty_waters_root: str,
) -> str:
    relative_report_path = relative_report_path.strip()

    if relative_report_path.startswith("/"):
        return relative_report_path

    dirty_waters_root = dirty_waters_root.rstrip("/")
    return f"{dirty_waters_root}/tool/{relative_report_path}"


def run_dirty_waters_check(
    repo_name: str,
    package_manager: str,
    check_flags: list[str],
    backend: str = "disabled",
    wsl_distro: str = "Ubuntu",
    dirty_waters_root: str = "/home/parafita/dirty-waters",
) -> tuple[DirtyWatersResult | None, list[str]]:
    errors: list[str] = []

    if backend != "wsl":
        errors.append("Dirty-Waters backend is disabled.")
        return None, errors

    github_token = os.getenv("GITHUB_API_TOKEN", "").strip()
    if not github_token:
        errors.append("GITHUB_API_TOKEN is not set in the Windows environment.")
        return None, errors

    repo_name_q = shlex.quote(repo_name)
    package_manager_q = shlex.quote(package_manager)
    dirty_waters_root_q = shlex.quote(dirty_waters_root)
    flags_q = " ".join(shlex.quote(flag) for flag in check_flags)

    windows_debug_dir = Path.cwd() / "dirty_waters_debug"
    windows_debug_dir.mkdir(exist_ok=True)

    windows_stdout = windows_debug_dir / "dirty_waters_stdout.txt"
    windows_stderr = windows_debug_dir / "dirty_waters_stderr.txt"
    windows_report = windows_debug_dir / "dirty_waters_report.md"

    wsl_stdout = _windows_to_wsl_path(windows_stdout)
    wsl_stderr = _windows_to_wsl_path(windows_stderr)
    wsl_report = _windows_to_wsl_path(windows_report)

    shell_script = f"""
set -o pipefail
export GITHUB_API_TOKEN={shlex.quote(github_token)}
cd {dirty_waters_root_q}/tool || exit 2
source ../venv/bin/activate || exit 3

python main.py -p {repo_name_q} -pm {package_manager_q} --gradual-report false --debug {flags_q} > {shlex.quote(wsl_stdout)} 2> {shlex.quote(wsl_stderr)}
cmd_status=$?

report_path=$(grep 'Report from static analysis generated at ' {shlex.quote(wsl_stdout)} | tail -n 1 | sed 's/^Report from static analysis generated at //')

if [ -n "$report_path" ]; then
  abs_report_path="{dirty_waters_root}/tool/$report_path"
  if [ -f "$abs_report_path" ]; then
    cp "$abs_report_path" {shlex.quote(wsl_report)} 2>/dev/null || true
  fi
fi

exit $cmd_status
"""

    try:
        result = subprocess.run(
            ["wsl", "-d", wsl_distro, "bash", "-lc", shell_script],
            capture_output=True,
            text=True,
            check=False,
        )
    except Exception as exc:
        errors.append(f"Failed to execute Dirty-Waters through WSL: {exc}")
        return None, errors

    stdout_text = windows_stdout.read_text(encoding="utf-8", errors="replace") if windows_stdout.exists() else ""
    stderr_text = windows_stderr.read_text(encoding="utf-8", errors="replace") if windows_stderr.exists() else ""
    copied_report_text = windows_report.read_text(encoding="utf-8", errors="replace") if windows_report.exists() else None

    if result.returncode != 0:
        errors.append(
            f"Dirty-Waters failed in WSL with exit code {result.returncode}. "
            f"stdout: {stdout_text[-2000:] if stdout_text else 'empty'} | "
            f"stderr: {stderr_text[-2000:] if stderr_text else 'empty'}"
        )
        return None, errors

    relative_report_path = _extract_report_path(stdout_text)
    absolute_linux_report_path = None
    user_report_location = None
    note = None

    if relative_report_path:
        absolute_linux_report_path = _resolve_absolute_report_path(
            relative_report_path,
            dirty_waters_root,
        )
        user_report_location = _linux_path_to_wsl_unc(
            absolute_linux_report_path,
            wsl_distro,
        )

    if copied_report_text:
        note = "Dirty-Waters analysis completed successfully and the report was copied back to the local debug folder."
        return DirtyWatersResult(
            stdout=stdout_text,
            report_path=absolute_linux_report_path,
            report_text=copied_report_text,
            user_report_location=user_report_location,
            note=note,
        ), errors

    # IMPORTANT:
    # If execution succeeded but the report was not copied back,
    # we still treat the analysis as successful as long as we know where the report is.
    if absolute_linux_report_path:
        note = (
            "Dirty-Waters analysis completed successfully. "
            "The report was generated inside WSL but was not copied back to the local debug folder. "
            f"Open it here: {user_report_location}"
        )
        return DirtyWatersResult(
            stdout=stdout_text,
            report_path=absolute_linux_report_path,
            report_text=None,
            user_report_location=user_report_location,
            note=note,
        ), errors

    errors.append(
        "Dirty-Waters execution succeeded, but the report path could not be determined from stdout. "
        f"Check: {windows_debug_dir}"
    )
    return None, errors