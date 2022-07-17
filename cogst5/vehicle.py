from cogst5.models.errors import *

from cogst5.bbw_objects import *

from cogst5.utils import *


class BbwVehicle(BbwObj):
    def __init__(
        self,
        type="",
        TL=0,
        cargo_capacity=0.0,
        crew_size=0.0,
        passenger_size=0.0,
        seat_capacity=0.0,
        fuel_tank_size=0.0,
        fuel_tank_capacity=0.0,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.set_type(type)
        self.set_TL(TL)
        self.cargo = BbwContainer(name="cargo", capacity=cargo_capacity)
        self.seats = BbwObj(name="seats", size=passenger_size + crew_size, capacity=seat_capacity)
        self._crew_size = 0
        self.set_crew_size(crew_size)
        self.fuel_tank = BbwObj(name="fuel_tank", size=fuel_tank_size, capacity=fuel_tank_capacity)

    def set_type(self, v):
        v = str(v)
        self._type = v

    def set_TL(self, v):
        v = int(v)
        test_geq("TL", v, 0.0)
        test_leq("TL", v, 30.0)
        self._TL = v

    def set_crew_size(self, v):
        v = float(v)
        test_geq("crew size", v, 0)
        new_seat_size = v + self.passenger_size()
        self.seats.set_size(new_seat_size)
        self._crew_size = v

    def set_passenger_size(self, v):
        v = float(v)
        test_geq("passenger size", v, 0)
        new_seat_size = v + self.crew_size()
        self.seats.set_size(new_seat_size)

    def crew_size(self):
        return self._crew_size

    def passenger_size(self):
        return self.seats.size() - self.crew_size()

    def type(self):
        return self._type

    def TL(self):
        return self._TL

    def hull(self):
        return self.capacity()

    def add_fuel(self, v):
        v = float(v)
        self.fuel_tank.set_size(self.fuel_tank.size() + v)

    def add_passenger(self, v):
        v = float(v)
        self.set_passenger_size(self.passenger_size() + v)

    def add_crew(self, v):
        v = float(v)
        self.set_crew_size(self.crew_size() + v)

    def add_cargo(self, item):
        self.cargo.add_item(item)

    def del_cargo(self, name, count=1):
        item = self.cargo.get_item(name)
        self.cargo.del_item(item.name(), count)

    @staticmethod
    def _header(is_compact=True):
        return ["name", "type", "TL", "hull", "cargo", "seats (crew)", "fuel tank"]

    def _str_table(self, is_compact=True):
        return [
            str(i)
            for i in [
                self.name(),
                self.type(),
                self.TL(),
                self.hull(),
                self.cargo.status(),
                self.seats.status() + f" ({self.crew_size()})",
                self.fuel_tank.status(),
            ]
        ]

    def __str__(self, is_compact=True):
        s = ""
        s += print_table(self._str_table(is_compact), headers=self._header(is_compact))

        s += "\n"

        if is_compact:
            return s

        s += self.cargo.__str__(is_compact=False)
        return s


class BbwSpaceShip(BbwVehicle):
    pass

