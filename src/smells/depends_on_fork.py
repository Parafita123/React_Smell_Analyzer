from src.smells.base import SmellDetector
from src.smells.dirty_waters_common import run_dirty_waters_smell


class DependsOnForkDetector(SmellDetector):
    smell_name = "depends-on-fork"

    def detect(self, **kwargs):
        return run_dirty_waters_smell(self.smell_name, **kwargs)