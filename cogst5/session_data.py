from cogst5.vehicle import *
from cogst5.base import *
from cogst5.company import *
from cogst5.calendar import *
from cogst5.wishlist import *

from .models.errors import *


class BbwSessionData(BbwObj):
    def __init__(self):
        self._fleet = BbwContainer(name="fleet", capacity=None)
        self._wishlist = BbwWishlist(name="wishlist", capacity=None)

        self._ship_curr = ""
        self._company = BbwCompany()
        self._calendar = BbwCalendar()

    def set_ship_curr(self, v):
        v = str(v)
        self._ship_curr = v

    def ship_curr(self):
        return self._ship_curr

    def get_ship_curr(self):
        if not self.ship_curr():
            raise InvalidArgument("curr ship not set!")

        return self.fleet().get_item(self.ship_curr())

    def fleet(self):
        return self._fleet

    def company(self):
        return self._company

    def calendar(self):
        return self._calendar

    def wishlist(self):
        return self._wishlist
