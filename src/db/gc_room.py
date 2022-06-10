from dataclasses import dataclass
from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class GlobalChatRoom:
    id: str
    name: str
    channels: list[int]
    owner: int
    password: str | None
    mute: list[int]
    rule: dict[str, str]
    slow: int
    description: str
    antispam: bool
