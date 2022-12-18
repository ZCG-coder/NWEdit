from typing import List

import json5rw as json

from src.constants import APPDIR


class HelpFiles():
    def __init__(self) -> None:
        with open("Config/default/helpfiles.json") as f:
            self.helpfiles = json.load(f)
        with open("Config/helpfiles.json") as f:
            self.helpfiles |= json.load(f)

    def get_name(self) -> List[str]:
        if self.helpfiles is None:
            return []
        names: List[str] = list(self.helpfiles.keys())
        names.remove("[default]")
        return names

    def get_file(self, name) -> str:
        if self.helpfiles is None:
            raise ValueError("No help files found")
        elif name == "[default]":
            raise Warning("Use the get_default() method instead")
        return f"{APPDIR}/../docs/{self.helpfiles[name]}"

    @property
    def get_default(self) -> str:
        if self.helpfiles is None:
            raise ValueError("No help files found")
        return f"{APPDIR}/../docs/{self.helpfiles['[default]']}"