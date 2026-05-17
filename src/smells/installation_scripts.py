import json
from pathlib import Path

from src.models import Finding
from src.smells.base import SmellDetector


INSTALL_SCRIPT_NAMES = {"preinstall", "install", "postinstall"}


class InstallationScriptsDetector(SmellDetector):
    smell_name = "installation-scripts"

    def detect(self, **kwargs):
        project_path = kwargs.get("project_path")
        if not project_path:
            raise RuntimeError("Missing project_path for installation-scripts detection.")

        project_dir = Path(project_path)
        node_modules_dir = project_dir / "node_modules"

        if not node_modules_dir.exists():
            raise RuntimeError(
                "installation-scripts detection requires node_modules to be installed locally."
            )

        findings: list[Finding] = []
        visited_paths: set[str] = set()

        for package_json_path in node_modules_dir.rglob("package.json"):
            try:
                resolved_path = str(package_json_path.resolve())
            except Exception:
                resolved_path = str(package_json_path)

            if resolved_path in visited_paths:
                continue
            visited_paths.add(resolved_path)

            try:
                with package_json_path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                continue

            package_name = data.get("name")
            package_version = data.get("version")
            scripts = data.get("scripts", {})

            if not isinstance(scripts, dict):
                continue

            detected_scripts = {
                script_name: script_cmd
                for script_name, script_cmd in scripts.items()
                if script_name in INSTALL_SCRIPT_NAMES
            }

            if not detected_scripts:
                continue

            relative_path = str(package_json_path.relative_to(project_dir))

            findings.append(
                Finding(
                    smell=self.smell_name,
                    dependency=package_name,
                    severity="medium",
                    evidence={
                        "package_version": package_version,
                        "package_json": relative_path,
                        "detected_scripts": detected_scripts,
                    },
                    message=(
                        f"Dependency '{package_name}' defines installation lifecycle "
                        f"script(s): {', '.join(detected_scripts.keys())}."
                    ),
                )
            )

        return findings