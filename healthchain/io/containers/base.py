import json
from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class BaseDocument:
    """
    Base container for document data flowing through a pipeline.

    Holds the original input in ``data`` and a text view in ``text``. Serialization
    helpers skip private (``_``-prefixed) attributes so pipeline-internal state
    (e.g. the spaCy doc) is never emitted.

    Attributes:
        data (Any): The original input supplied (raw text, FHIR Bundle, resource, or list).
        text (str): Text view of the document, derived from ``data``.
    """

    data: Any
    text: str = field(init=False)

    def __post_init__(self):
        self.text = self.data

    def char_count(self) -> int:
        return len(self.text)

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BaseDocument":
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> "BaseDocument":
        return cls.from_dict(json.loads(json_str))
