from .starship import Starship

from ..models.errors import *


class SessionData:
    def __init__(self):
        self.fleet = {}
        self.starship_current = ""

    def __to_json__(self):
        return self.__dict__

    @classmethod
    def __from_dict__(cls, d):
        c = cls()
        c.fleet = {k: Starship.__from_dict__(v) for k, v in d["fleet"].items()}
        c.starship_current = d["starship_current"]
        return c

    def get_current_starship(self):
        if not self.starship_current:
            raise InvalidArgument("Current starship not set!")

        return self.fleet[self.starship_current]
