from src.smells.base import SmellDetector
from src.smells.dirty_waters_common import run_dirty_waters_smell


class AliasedPackagesDetector(SmellDetector):
    smell_name = "aliased-packages"

    def detect(self, **kwargs):
        return run_dirty_waters_smell(self.smell_name, **kwargs)