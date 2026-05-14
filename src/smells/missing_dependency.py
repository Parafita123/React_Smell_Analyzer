from src.external_tools.knip_adapter import run_knip_dependency_analysis
from src.smells.base import SmellDetector


class MissingDependencyDetector(SmellDetector):
    smell_name = "missing-dependency"

    def detect(self, **kwargs):
        project_path = kwargs["project_path"]
        findings, errors = run_knip_dependency_analysis(project_path)

        if errors:
            raise RuntimeError(" | ".join(errors))

        return [f for f in findings if f.smell == self.smell_name]