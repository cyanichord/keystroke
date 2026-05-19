"""
flow_manager.py
Manages loading, saving and validating keystroke flow JSON files.

JSON schema:
{
  "spacing": 0.05,
  "steps": [
    {"key": "ctrl+1",    "duration": 0.1},
        {"key": "a",         "duration": 0.05}
  ]
}
"""
import json
import os
from typing import Any


DEFAULT_FLOW: dict[str, Any] = {
    "spacing": 0.05,
    "steps": [
        {"key": "ctrl+1", "duration": 0.1},
        {"key": "a",      "duration": 0.05},
    ],
}


class FlowManager:
    REQUIRED_STEP_KEYS = {"key", "duration"}
    OPTIONAL_STEP_KEYS = {"spacing"}

    def __init__(self) -> None:
        self._flow: dict[str, Any] = dict(DEFAULT_FLOW)

    @property
    def flow(self) -> dict[str, Any]:
        return self._flow

    def load(self, path: str) -> None:
        if not os.path.isfile(path):
            raise FileNotFoundError(f"Flow file not found: {path}")
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        self._validate(data)
        self._flow = data

    def save(self, path: str, data: dict[str, Any] | None = None) -> None:
        payload = data if data is not None else self._flow
        self._validate(payload)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, ensure_ascii=False)
        self._flow = payload

    def from_text(self, text: str) -> None:
        data = json.loads(text)
        self._validate(data)
        self._flow = data

    def to_text(self) -> str:
        return json.dumps(self._flow, indent=2, ensure_ascii=False)

    def default_text(self) -> str:
        return json.dumps(DEFAULT_FLOW, indent=2, ensure_ascii=False)

    @staticmethod
    def _validate(data: dict[str, Any]) -> None:
        if not isinstance(data, dict):
            raise ValueError("Flow must be a JSON object.")
        if "steps" not in data or not isinstance(data["steps"], list):
            raise ValueError("Flow must contain a 'steps' list.")
        if "spacing" not in data:
            data["spacing"] = 0.05
        for i, step in enumerate(data["steps"]):
            missing = FlowManager.REQUIRED_STEP_KEYS - step.keys()
            if missing:
                raise ValueError(f"Step {i} missing fields: {missing}")
            if not isinstance(step["duration"], (int, float)):
                raise ValueError(f"Step {i} 'duration' must be a number.")
            if "spacing" in step and not isinstance(step["spacing"], (int, float)):
                raise ValueError(f"Step {i} 'spacing' must be a number.")
