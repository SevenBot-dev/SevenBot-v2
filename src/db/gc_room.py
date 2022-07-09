from dataclasses import dataclass
from typing import Union

from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class GlobalChatRoom:
    id: str
    name: str
    channels: list[int]
    owner: int
    password: Union[str, None]
    mute: list[int]
    rule: dict[str, str]
    slow: int
    description: str
    antispam: bool

    def except_channel(self, *channels: int) -> bool:
        tmp_channels = self.channels.copy()
        for channel in channels:
            if channel in tmp_channels:
                tmp_channels.remove(channel)
        return tmp_channels
