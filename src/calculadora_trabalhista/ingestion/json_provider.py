from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

from ..models import ProcessFacts


class ProcessFactsProvider(Protocol):
    def load(self) -> ProcessFacts: ...


class JsonProcessFactsProvider:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def load(self) -> ProcessFacts:
        data = json.loads(self.path.read_text(encoding="utf-8"))
        return ProcessFacts.model_validate(data)
