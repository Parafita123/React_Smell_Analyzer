import json
from datetime import datetime, timezone
from urllib.parse import quote
from urllib.request import urlopen

from src.models import Finding
from src.smells.base import SmellDetector


DEFAULT_UNMAINTAINED_MONTHS = 24


def _parse_iso_datetime(value: str) -> datetime | None:
    if not value:
        return None

    try:
        if value.endswith("Z"):
            value = value.replace("Z", "+00:00")
        return datetime.fromisoformat(value)
    except Exception:
        return None


def _months_since(dt: datetime) -> int:
    now = datetime.now(timezone.utc)
    return (now.year - dt.year) * 12 + (now.month - dt.month)


def _fetch_npm_package_metadata(package_name: str) -> dict:
    encoded_name = quote(package_name, safe="@/")
    url = f"https://registry.npmjs.org/{encoded_name}"

    with urlopen(url, timeout=15) as response:
        return json.load(response)


class UnmaintainedPackageDetector(SmellDetector):
    smell_name = "unmaintained-package"

    def detect(self, **kwargs):
        package_json = kwargs.get("package_json")
        if not package_json:
            raise RuntimeError("Missing package.json data for unmaintained-package detection.")

        threshold_months = kwargs.get("unmaintained_threshold_months", DEFAULT_UNMAINTAINED_MONTHS)

        dependencies = package_json.get("dependencies", {})
        dev_dependencies = package_json.get("devDependencies", {})

        direct_packages = {}
        direct_packages.update(dependencies)
        direct_packages.update(dev_dependencies)

        findings: list[Finding] = []

        for package_name, declared_version in direct_packages.items():
            try:
                metadata = _fetch_npm_package_metadata(package_name)
            except Exception as exc:
                continue

            time_info = metadata.get("time", {})
            modified_str = time_info.get("modified")

            modified_dt = _parse_iso_datetime(modified_str)
            if modified_dt is None:
                continue

            months_old = _months_since(modified_dt)

            if months_old < threshold_months:
                continue

            findings.append(
                Finding(
                    smell=self.smell_name,
                    dependency=package_name,
                    severity="low",
                    evidence={
                        "declared_version": declared_version,
                        "last_modified": modified_str,
                        "months_since_last_modified": months_old,
                        "threshold_months": threshold_months,
                        "reported_by": "npm-registry",
                    },
                    message=(
                        f"Dependency '{package_name}' appears potentially unmaintained: "
                        f"last registry modification was {months_old} month(s) ago."
                    ),
                )
            )

        return findings