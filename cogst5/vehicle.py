from cogst5.models.errors import *

from cogst5.base import *
from cogst5.person import *
from cogst5.utils import *


class BbwVehicle(BbwObj):
    def __init__(
        self,
        type="",
        TL=0,
        armour=0,
        cargo_capacity=0.0,
        seat_capacity=0.0,
        fuel_tank_capacity=0.0,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.set_type(type)
        self.set_TL(TL)
        self.set_armour(armour)
        self._cargo = BbwContainer(name="cargo", capacity=cargo_capacity)
        self._seats = BbwContainer(name="seats", capacity=seat_capacity)
        self._fuel_tank = BbwObj(name="fuel_tank", size=0, capacity=fuel_tank_capacity)

    def set_type(self, v):
        v = str(v)
        self._type = v

    def set_TL(self, v):
        v = int(v)
        test_geq("TL", v, 0)
        test_leq("TL", v, 30)
        self._TL = v

    def type(self):
        return self._type

    def TL(self):
        return self._TL

    def hull(self):
        return self.capacity()

    def add_fuel(self, v):
        v = float(v)
        self.fuel_tank().set_size(self.fuel_tank().size() + v)

    def crew_size(self):
        return sum([v.capacity() for v in self.seats().values() if v.is_crew()])

    def computer(self):
        return self._computer

    def cargo(self):
        return self._cargo

    def seats(self):
        return self._seats

    def fuel_tank(self):
        return self._fuel_tank

    @staticmethod
    def _header(is_compact=True):
        s = ["name", "cargo", "seats (crew)", "fuel tank", "status"]
        if is_compact:
            return s

        s = [*s, "type", "TL", "armour"]
        return s

    def _str_table(self, is_compact=True):
        s = [
            str(i)
            for i in [
                self.name(),
                self.cargo().status(),
                self.seats().status() + f" ({self.crew_size()})",
                self.fuel_tank().status(),
                self.status(),
            ]
        ]

        if is_compact:
            return s

        s2 = [
            str(i)
            for i in [
                self.type(),
                self.TL(),
                self.armour(),
            ]
        ]

        return [*s, *s2]

    def __str__(self, is_compact=True):
        s = ""
        s += print_table(self._str_table(is_compact), headers=self._header(is_compact))

        s += "\n"

        if is_compact:
            return s

        s += self.seats().__str__(is_compact=False)
        s += "\n"
        s += self.cargo().__str__(is_compact=False)
        return s


class BbwSpaceShip(BbwVehicle):
    def __init__(
        self,
        drive_m=0,
        drive_j=0,
        power_plant=0,
        fuel_refiner_speed=40,
        is_fuel_refined=True,
        is_streamlined=True,
        has_fuel_scoop=True,
        has_cargo_crane=True,
        computer_capacity=0.0,
        *args,
        **kwargs,
    ):
        self.set_drive_m(drive_m)
        self.set_drive_j(drive_j)
        self.set_power_plant(power_plant)
        self.set_fuel_refiner_speed(fuel_refiner_speed)
        self.set_is_fuel_refined(is_fuel_refined)
        self.set_is_streamlined(is_streamlined)
        self.set_has_fuel_scoop(has_fuel_scoop)
        self.set_has_cargo_crane(has_cargo_crane)
        self._computer = BbwContainer(name="computer", capacity=computer_capacity)
        super().__init__(*args, **kwargs)

    def set_has_cargo_crane(self, v):
        v = bool(v)
        self._has_cargo_crane = v

    def has_cargo_crane(self):
        return self._has_cargo_crane

    def set_has_fuel_scoop(self, v):
        v = bool(v)
        self._has_fuel_scoop = v

    def has_fuel_scoop(self):
        return self._has_fuel_scoop

    def set_is_streamlined(self, v):
        v = bool(v)
        self._is_streamlined = v

    def is_streamlined(self):
        return self._is_streamlined

    def set_is_fuel_refined(self, v):
        v = bool(v)
        self._is_fuel_refined = v

    def is_fuel_refined(self):
        return self._is_fuel_refined

    def set_armour(self, v):
        v = int(v)
        test_geq("armour", v, 0)
        self._armour = v

    def armour(self):
        return self._armour

    def set_fuel_refiner_speed(self, v):
        v = int(v)
        test_geq("fuel refiner speed", v, 0)
        self._fuel_refiner_speed = v

    def fuel_refiner_speed(self):
        return self._fuel_refiner_speed

    def set_drive_m(self, v):
        v = int(v)
        test_geq("drive m", v, 0)
        self._drive_m = v

    def drive_m(self):
        return self._drive_m

    def set_drive_j(self, v):
        v = int(v)
        test_geq("drive j", v, 0)
        self._drive_j = v

    def drive_j(self):
        return self._drive_j

    def set_power_plant(self, v):
        v = int(v)
        test_geq("power plant", v, 0)
        self._power_plant = v

    def power_plant(self):
        return self._power_plant

    @staticmethod
    def _header(is_compact=True):
        s = ["name", "cargo", "seats (crew)", "fuel tank", "computer"]
        if is_compact:
            return s

        s = [
            *s,
            "status",
            "type",
            "TL",
            "armour",
            "drive m",
            "drive j",
            "power plant",
            "fuel refiner speed",
            "streamlined",
            "scoop",
            "c. crane",
        ]
        return s

    def _str_table(self, is_compact=True):
        s = [
            str(i)
            for i in [
                self.name(),
                self.cargo().status(),
                self.seats().status() + f" ({self.crew_size()})",
                self.fuel_tank().status(),
                self.computer().status(),
            ]
        ]

        if is_compact:
            return s

        s2 = [
            str(i)
            for i in [
                self.status(),
                self.type(),
                self.TL(),
                self.armour(),
                self.drive_m(),
                self.drive_j(),
                self.power_plant(),
                self.fuel_refiner_speed(),
                self.is_streamlined(),
                self.has_fuel_scoop(),
                self.has_cargo_crane(),
            ]
        ]

        return [*s, *s2]

    def __str__(self, is_compact=True):
        s = ""
        s += print_table(self._str_table(is_compact), headers=self._header(is_compact))

        s += "\n"

        if is_compact:
            return s

        s += self.seats().__str__(is_compact=False)
        s += "\n"
        s += self.cargo().__str__(is_compact=False)
        s += "\n"
        s += self.computer().__str__(is_compact=False)
        return s
