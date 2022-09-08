from cogst5.models.errors import *

import math
import d20

from cogst5.base import *
from cogst5.person import *
from cogst5.utils import *


class BbwVehicle(BbwObj):
    def __init__(
        self,
        type="",
        TL=0,
        armour=0,
        containers={"cargo": 0.0, "seats": 0.0, "fuel tank": 0.0},
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.set_type(type)
        self.set_TL(TL)
        self.set_armour(armour)
        self._containers = {
            c_name: BbwContainer(name=c_name, capacity=c_capacity) for c_name, c_capacity in containers.items()
        }

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

    def containers(self):
        return self._containers

    def get_container(self, name):
        return get_item(name, self.containers())

    @staticmethod
    def _header(is_compact=True):
        s = ["name", "hull", "containers"]
        if is_compact:
            return s

        s = [*s, "type", "TL", "armour"]
        return s

    def _str_table(self, is_compact=True):
        s = [
            str(i)
            for i in [
                self.name(),
                self.hull(),
                "\n".join([f"{k}: {v.status()}" for k, v in self.containers().items()]),
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

        for i in self.containers():
            s += "\n"
            s += i.__str__(is_compact=False)

        return s


class BbwSpaceShip(BbwVehicle):
    def __init__(
        self,
        drive_m=0,
        drive_j=0,
        power_plant=0,
        fuel_refiner_speed=40,
        is_streamlined=True,
        has_fuel_scoop=True,
        has_cargo_crane=True,
        *args,
        **kwargs,
    ):
        self.set_drive_m(drive_m)
        self.set_drive_j(drive_j)
        self.set_power_plant(power_plant)
        self.set_fuel_refiner_speed(fuel_refiner_speed)
        self.set_is_streamlined(is_streamlined)
        self.set_has_fuel_scoop(has_fuel_scoop)
        self.set_has_cargo_crane(has_cargo_crane)
        super().__init__(*args, **kwargs)

    def sector_jump_time(self, diam_beg_km, diam_end_km):
        diam_beg_km = float(diam_beg_km)
        diam_end_km = float(diam_end_km)
        t1 = self._100diam_time_days(diam_beg_km)
        t2 = (148 + d20.roll("6d6").total) / 24
        t3 = self._100diam_time_days(diam_end_km)

        return conv_days_2_time(t1 + t2 + t3)

    def _100diam_time_days(self, diam_km):
        """
        We suppose that we start from 0 speed and we reach the destination with 0 speed. d is the distance we want to cover.
        the time to cover half of the distance follows the equation: 1/2 * a * t**2 = d/2 -> t = sqrt(d/a). The time to cover
        the distance is twice as much: t = 2 * sqrt(d/a). Other factors are added to convert units.
        """
        return 2 * math.sqrt(100 * 1000 * diam_km / (self.drive_j() * 10)) / (60 * 60 * 24)

    def set_has_cargo_crane(self, v):
        v = bool(int(v))
        self._has_cargo_crane = v

    def has_cargo_crane(self):
        return self._has_cargo_crane

    def set_has_fuel_scoop(self, v):
        v = bool(int(v))
        self._has_fuel_scoop = v

    def has_fuel_scoop(self):
        return self._has_fuel_scoop

    def set_is_streamlined(self, v):
        v = bool(int(v))
        self._is_streamlined = v

    def is_streamlined(self):
        return self._is_streamlined

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
        s = BbwVehicle._header(is_compact)

        if is_compact:
            return s

        s = [
            *s,
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
                *super()._str_table(is_compact),
            ]
        ]

        if is_compact:
            return s

        s2 = [
            str(i)
            for i in [
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

        for i in self.containers().values():
            s += "\n"
            s += i.__str__(is_compact=False)

        return s
