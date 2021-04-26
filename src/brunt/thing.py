"""Class for thing objects."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

# state: {'TIMESTAMP': '1619179952875', 'NAME': 'Blind', 'SERIAL': '00140d6f1950f166', 'MODEL': 'BEAKR1601', 'requestPosition': '100', 'currentPosition': '100', 'moveState': '0', 'setLoad': '2418', 'currentLoad': '5', 'FW_VERSION': '1.361', 'overStatus': '0', 'Duration': '1000', 'ICON': 'b-icon-curtain_01', 'delay': 3810}
# things: [{'TIMESTAMP': '1619179952875', 'NAME': 'Blind', 'SERIAL': '00140d6f1950f166', 'MODEL': 'BEAKR1601', 'requestPosition': '100', 'currentPosition': '100', 'moveState': '0', 'setLoad': '2418', 'currentLoad': '5', 'FW_VERSION': '1.361', 'overStatus': '0', 'Duration': '1000', 'ICON': 'b-icon-curtain_01', 'thingUri': '/hub/00140d6f1950f166', 'PERMISSION_TYPE': '"ownership"', 'delay': 2594}]


@dataclass
class Thing:
    """Class for representing Things."""

    TIMESTAMP: int
    NAME: str
    SERIAL: str
    MODEL: str
    requestPosition: str
    currentPosition: str
    moveState: str
    setLoad: str
    currentLoad: str
    FW_VERSION: str
    overStatus: str
    Duration: str
    ICON: str
    delay: str
    thingUri: Optional[str] = None
    PERMISSION_TYPE: Optional[str] = None
    datetime: Optional[datetime] = None

    def __post_init__(self) -> None:
        """Do post init work."""
        self.datetime = datetime.utcfromtimestamp(int(self.TIMESTAMP) / 1000)

    def compare_string(self, string: str) -> bool:
        """Compare to string."""
        return self.NAME == string
