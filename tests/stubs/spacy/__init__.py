"""Minimal stub of the spaCy package used in the tests.

The real spaCy library is quite heavy and not available in the execution
environment.  The tests only need a very small portion of its API to create a
blank model with an ``EntityRuler`` pipe.  This stub implements just enough of
that behaviour for the unit tests.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class Span:
    text: str
    label_: str


class Doc:
    def __init__(self, text: str) -> None:
        self.text = text
        self.ents: List[Span] = []


class EntityRuler:
    def __init__(self, nlp: "Language") -> None:
        self.nlp = nlp
        self.patterns: List[dict] = []

    def add_patterns(self, patterns: List[dict]) -> None:
        self.patterns.extend(patterns)

    def __call__(self, doc: Doc) -> Doc:  # pragma: no cover - trivial
        for pat in self.patterns:
            if pat.get("pattern") in doc.text:
                doc.ents.append(Span(text=pat["pattern"], label_=pat["label"]))
        return doc


class Language:
    def __init__(self, lang: str) -> None:
        self.lang = lang
        self._ruler: EntityRuler | None = None

    def add_pipe(self, name: str) -> EntityRuler:
        if name != "entity_ruler":
            raise ValueError("Only 'entity_ruler' pipe is supported in the stub")
        self._ruler = EntityRuler(self)
        return self._ruler

    def __call__(self, text: str) -> Doc:  # pragma: no cover - trivial
        doc = Doc(text)
        if self._ruler:
            self._ruler(doc)
        return doc


def blank(lang: str) -> Language:
    return Language(lang)


# Submodule ``pipeline`` providing ``EntityRuler`` ---------------------------

class pipeline:  # pragma: no cover - module-style container
    EntityRuler = EntityRuler


__all__ = ["blank", "pipeline", "EntityRuler", "Language", "Doc", "Span"]

