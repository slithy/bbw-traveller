from cogst5.vehicle import *
from cogst5.bbw_objects import *

from .models.errors import *


class BbwSessionData(BbwObj):
    def __init__(self):
        self.fleet = BbwContainer(name="fleet", capacity=None)
        self._ship_curr = ""

    def set_ship_curr(self, v):
        v = str(v)
        self._ship_curr = v

    def ship_curr(self):
        return self._ship_curr

    def get_ship_curr(self):
        if not self.ship_curr():
            raise InvalidArgument("curr ship not set!")

        return self.fleet.get_item(self.ship_curr())

    def set_spaceship(self, name, capacity, type, TL, cargo_capacity, seat_capacity, fuel_tank_capacity):
        if name in self.fleet:
            raise InvalidArgument(
                f"A ship with that name: {name} already exists! If you really want to replace it " f"delete it first"
            )

        s = BbwSpaceShip(
            name=name,
            type=type,
            TL=TL,
            capacity=capacity,
            cargo_capacity=cargo_capacity,
            seat_capacity=seat_capacity,
            fuel_tank_capacity=fuel_tank_capacity,
        )
        self.fleet.set_item(s.name(), s)

    def del_ship(self, name):
        self.fleet.del_item(name)
