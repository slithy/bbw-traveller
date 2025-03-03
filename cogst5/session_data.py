from cogst5.vehicle import *
from cogst5.base import *
from cogst5.company import *
from cogst5.calendar import *
from cogst5.wishlist import *
from cogst5.log import *

from .models.errors import *


@BbwUtils.for_all_methods(BbwUtils.type_sanitizer_decor)
class BbwSessionData(BbwObj):
    def __init__(self):
        self._fleet = BbwObj(name="fleet", capacity="inf", size=0)
        self._wishlist = BbwWishlist(name="wishlist", capacity="inf", size=0)
        self._charted_space = BbwObj(name="charted space", capacity="inf", size=0)

        self._world_curr = ""
        self._ship_curr = ""
        self._company = BbwCompany()
        self._calendar = BbwCalendar()
        self.set_log()

    def set_ship_curr(self, v: str = ""):
        if v == "":
            self._ship_curr = ""
            return

        res = self.fleet().get_objs(name=v, only_one=True)
        self._ship_curr = res.objs()[0][0].name()

    @BbwUtils.set_if_not_present_decor
    def ship_curr(self):
        return self._ship_curr

    def get_ship_curr(self):
        if not self.ship_curr():
            raise InvalidArgument("curr ship not set!")

        return self.fleet().get_objs(name=self.ship_curr(), only_one=True)[0]

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

    def get_world(self, name=None):
        if name is None or name == "":
            name = self.world_curr()

        return self.charted_space().get_objs(name=name, only_one=True, recursive=False)[0]

    def get_worlds(self, w_to_name, w_from_name=None):
        if w_from_name is None:
            w0 = self.get_world()
        else:
            w0 = self.charted_space().get_objs(name=w_from_name, only_one=True).objs()[0][0]
        w1 = self.charted_space().get_objs(name=w_to_name, only_one=True).objs()[0][0]
        return w0, w1

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

    def set_log(self):
        self._log = BbwLog()

    def log(self):
        if not hasattr(self, "_log"):
            self.set_log()
        return self._log

    def add_log_entry(self, description, value=0):
        self.log().add_entry(description=description, value=value, t=self.calendar().t())
        self.company().add_money(value)
