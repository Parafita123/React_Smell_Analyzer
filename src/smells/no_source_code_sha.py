from src.smells.base import SmellDetector
from src.smells.dirty_waters_common import run_dirty_waters_smell


class NoSourceCodeShaDetector(SmellDetector):
    smell_name = "no-source-code-sha"

    def detect(self, **kwargs):
        return run_dirty_waters_smell(self.smell_name, **kwargs)
    
    