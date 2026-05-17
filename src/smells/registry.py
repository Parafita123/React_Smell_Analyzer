from src.smells.no_package_lock import NoPackageLockDetector
from src.smells.pinned_dependency import PinnedDependencyDetector
from src.smells.url_dependency import UrlDependencyDetector
from src.smells.restrictive_constraint import RestrictiveConstraintDetector
from src.smells.permissive_constraint import PermissiveConstraintDetector
from src.smells.duplicate_versions import DuplicateVersionsDetector
from src.smells.unused_dependency import UnusedDependencyDetector
from src.smells.missing_dependency import MissingDependencyDetector
from src.smells.deprecated_dependency import DeprecatedDependencyDetector
from src.smells.no_source_code_link import NoSourceCodeLinkDetector
from src.smells.no_source_code_sha import NoSourceCodeShaDetector
from src.smells.depends_on_fork import DependsOnForkDetector
from src.smells.no_build_attestation import NoBuildAttestationDetector
from src.smells.no_invalid_code_signature import NoInvalidCodeSignatureDetector
from src.smells.aliased_packages import AliasedPackagesDetector
from src.smells.installation_scripts import InstallationScriptsDetector
from src.smells.unmaintained_package import UnmaintainedPackageDetector

SMELL_REGISTRY = {
    "no-package-lock": NoPackageLockDetector(),
    "pinned-dependency": PinnedDependencyDetector(),
    "url-dependency": UrlDependencyDetector(),
    "restrictive-constraint": RestrictiveConstraintDetector(),
    "permissive-constraint": PermissiveConstraintDetector(),
    "duplicate-versions": DuplicateVersionsDetector(),
    "unused-dependency": UnusedDependencyDetector(),
    "missing-dependency": MissingDependencyDetector(),
    "deprecated-dependency": DeprecatedDependencyDetector(),
    "no-source-code-link": NoSourceCodeLinkDetector(),
    "no-source-code-sha": NoSourceCodeShaDetector(),
    "depends-on-fork": DependsOnForkDetector(),
    "no-build-attestation": NoBuildAttestationDetector(),
    "no-invalid-code-signature": NoInvalidCodeSignatureDetector(),
    "aliased-packages": AliasedPackagesDetector(),
    "installation-scripts": InstallationScriptsDetector(),
    "unmaintained-package": UnmaintainedPackageDetector(),
}