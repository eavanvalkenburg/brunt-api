"""Class for thing objects."""
from __future__ import annotations

import logging
from dataclasses import dataclass, fields
from datetime import datetime
from typing import Any

# state: {'TIMESTAMP': '1619179952875', 'NAME': 'Blind', 'SERIAL': '00140d6f1950f166', 'MODEL': 'BEAKR1601', 'requestPosition': '100', 'currentPosition': '100', 'moveState': '0', 'setLoad': '2418', 'currentLoad': '5', 'FW_VERSION': '1.361', 'overStatus': '0', 'Duration': '1000', 'ICON': 'b-icon-curtain_01', 'delay': 3810}
# things: [{'TIMESTAMP': '1619179952875', 'NAME': 'Blind', 'SERIAL': '00140d6f1950f166', 'MODEL': 'BEAKR1601', 'requestPosition': '100', 'currentPosition': '100', 'moveState': '0', 'setLoad': '2418', 'currentLoad': '5', 'FW_VERSION': '1.361', 'overStatus': '0', 'Duration': '1000', 'ICON': 'b-icon-curtain_01', 'thingUri': '/hub/00140d6f1950f166', 'PERMISSION_TYPE': '"ownership"', 'delay': 2594}]

_LOGGER = logging.getLogger(__name__)

MAPPING = {
    "NAME": "name",
    "thingUri": "thing_uri",
    "MODEL": "model",
    "FW_VERSION": "fw_version",
    "requestPosition": "request_position",
    "TIMESTAMP": "timestamp",
    "SERIAL": "serial",
    "currentPosition": "current_position",
    "moveState": "move_state",
    "setLoad": "set_load",
    "currentLoad": "current_load",
    "overStatus": "over_status",
    "Duration": "duration",
    "ICON": "icon",
    "delay": "delay",
    "PERMISSION_TYPE": "permission_type",
    "resave": "resave",
    "resaveflag": "resave_flag",
    "buttonControl": "button_control",
}


@dataclass
class Thing:
    """Class for representing Things."""

    name: str
    model: str
    fw_version: str
    thing_uri: str | None = None
    request_position: int = 0
    current_position: int = 0
    move_state: int = 0
    timestamp: int | None = None
    serial: str | None = None
    set_load: int | None = None
    current_load: int | None = None
    over_status: int | None = None
    duration: int | None = None
    icon: str | None = None
    delay: int | None = None
    permission_type: str | None = None
    datetime: datetime | None = None
    resave: str | None = None
    resave_flag: str | None = None
    button_control: str | None = None

    @classmethod
    def create_from_dict(cls, input_dict: dict[str, Any]) -> Thing:
        """Create a Thing from a dict."""
        _LOGGER.debug("Creating Thing from dict: %s", input_dict)
        class_fields = {f.name: f.type for f in fields(cls)}
        thing = {}
        for key, value in input_dict.items():
            new_key = MAPPING.get(key)
            if new_key is None:
                _LOGGER.info("%s not in Thing mapping fields", key)
                continue
            if new_key not in class_fields:
                _LOGGER.info("%s not in Thing class fields", key)
                continue
            if class_fields[new_key] in ("int", "int | None"):
                try:
                    value = int(value)
                except ValueError:
                    _LOGGER.warning("%s not an int, value was: %s", key, value)
                    continue
            thing[new_key] = value
        return Thing(**thing)

    def __post_init__(self) -> None:
        """Do post init work."""
        if self.timestamp is not None:
            self.datetime = datetime.utcfromtimestamp(self.timestamp / 1000)
        if self.thing_uri is None and self.serial is not None:
            self.thing_uri = f"/hub/{self.serial}"

    def compare_name(self, name: str) -> bool:
        """Compare name to name."""
        return self.name == name
