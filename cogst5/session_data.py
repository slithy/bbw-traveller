from cogst5.vehicle import *
from cogst5.base import *
from cogst5.company import *
from cogst5.calendar import *
from cogst5.wishlist import *

from .models.errors import *


class BbwSessionData(BbwObj):
    def __init__(self):
        self._fleet = BbwContainer(name="fleet")
        self._wishlist = BbwWishlist(name="wishlist")
        self._charted_space = BbwContainer(name="charted space")

        self._world_curr = ""
        self._ship_curr = ""
        self._company = BbwCompany()
        self._calendar = BbwCalendar()

    def set_ship_curr(self, v):
        v = str(v)
        if v == "":
            self._ship_curr = ""
            return

        res = self.fleet().get_objs(name=v, only_one=True)
        self._ship_curr = res.objs()[0][0].name()

    def ship_curr(self):
        return self._ship_curr

    def get_ship_curr(self):
        if not self.ship_curr():
            raise InvalidArgument("curr ship not set!")

        return self.fleet().get_objs(name=self.ship_curr(), only_one=True).objs()[0][0]

    def charted_space(self):
        return self._charted_space

    def set_world_curr(self, v):
        v = str(v)
        if v == "":
            self._world_curr = ""
            return

        res = self.charted_space().get_objs(name=v, only_one=True)
        self._world_curr = res.objs()[0][0].name()

    def world_curr(self):
        return self._world_curr

    def get_world_curr(self):
        if self.world_curr() == "":
            raise InvalidArgument("curr world not set!")

        return self.charted_space().get_objs(name=self.world_curr(), only_one=True).objs()[0][0]

    def charted_space(self):
        return self._charted_space

    def company(self):
        return self._company

    def calendar(self):
        return self._calendar

    def wishlist(self):
        return self._wishlist

    def fleet(self):
        return self._fleet
