from cogst5.base import *
from cogst5.planet import *

from .models.errors import *


class BbwGalaxy(BbwObj):
    def __init__(self):
        self._planets = BbwContainer(name="planets", capacity=None)

        self._planet_curr = ""
