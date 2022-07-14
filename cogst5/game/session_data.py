from .starship import Starship

from ..models.errors import *


class SessionData:
    def __init__(self):
        self.fleet = {}
        self.starship_current = ""

    def get_current_starship(self):
        if not self.starship_current:
            raise InvalidArgument("Current starship not set!")

        return self.fleet[self.starship_current]
