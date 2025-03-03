import copy

from cogst5.models.errors import *

import math
import d20

from cogst5.base import BbwObj
from cogst5.person import *
from cogst5.item import *
from cogst5.utils import *
from cogst5.world import *

import bisect


@BbwUtils.for_all_methods(BbwUtils.type_sanitizer_decor)
class BbwVehicle(BbwObj):
    def __init__(
        self,
        type="",
        TL=0,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.set_type(type)
        self.set_TL(TL)
        self.set_HP()

    def armour(self):
        return BbwUtils.secondary_armour(self)

    def armor(self):
        return self.armour()

    def set_type(self, v: str):
        self._type = v

    def set_TL(self, v: int):
        BbwUtils.test_geq("TL", v, 0)
        BbwUtils.test_leq("TL", v, 30)
        self._TL = v

    @BbwUtils.set_if_not_present_decor
    def type(self):
        return self._type

    @BbwUtils.set_if_not_present_decor
    def TL(self):
        return self._TL

    def max_HP(self):
        return self.capacity() / 2.5

    def set_HP(self, v: float = None):
        if v is None:
            v = self.max_HP()

        v = min(self.max_HP(), v)
        v = max(0, v)
        self._HP = v

    @BbwUtils.set_if_not_present_decor
    def HP(self):
        return self._HP

    def hull(self):
        return f"({BbwUtils.pf(self.HP())}/{BbwUtils.pf(self.max_HP())})"

    @staticmethod
    def _header(is_compact=True):
        s = ["name", "HP", "type", "TL", "armour", "status", "info"]
        return s

    def _str_table(self, is_compact=True):
        s = [
            str(i)
            for i in [
                self.name(),
                self.hull(),
                self.type(),
                self.TL(),
                self.armour(),
                self.status(),
                self.info(),
            ]
        ]

        return s

    def __str__(self, detail_lvl: int = 0):
        s = ""
        s += BbwUtils.print_table(
            self._str_table(detail_lvl=detail_lvl),
            headers=BbwVehicle._header(detail_lvl=detail_lvl),
            detail_lvl=detail_lvl,
        )
        if detail_lvl == 0:
            return s

        for i in self.get_children():
            s += i.__str__(detail_lvl=detail_lvl)

        return s


@BbwUtils.for_all_methods(BbwUtils.type_sanitizer_decor)
class BbwSpaceShip(BbwVehicle):
    _require_fuel_scoop = {"gas giant": 1, "planet": 1, "world": 1, "refined": 0, "unrefined": 0}

    def __init__(
        self,
        capacity: float = 200,
        size: float = 0.0,
        m_drive=1,
        j_drive=2,
        power_plant=105,
        fuel_refiner_speed=40,
        is_streamlined=True,
        has_fuel_scoop=True,
        has_cargo_scoop=True,
        has_cargo_crane=True,
        *args,
        **kwargs,
    ):
        self.set_m_drive(m_drive)
        self.set_j_drive(j_drive)
        self.set_power_plant(power_plant)
        self.set_fuel_refiner_speed(fuel_refiner_speed)
        self.set_is_streamlined(is_streamlined)
        self.set_has_fuel_scoop(has_fuel_scoop)
        self.set_has_cargo_scoop(has_cargo_scoop)
        self.set_has_cargo_crane(has_cargo_crane)
        super().__init__(capacity=capacity, size=size, *args, **kwargs)
        self.dist_obj(BbwObj("fuel tank", 41, size=0))
        self.dist_obj(BbwObj("cargo0, main", 30, size=0))
        self.dist_obj(BbwObj("stateroom, main", 44, size=0))

    def flight_time_m_drive(self, d_km: int):
        """
        We suppose that we start from 0 speed and we reach the destination with 0 speed. d is the distance we want to cover.
        the time to cover half of the distance follows the equation: 1/2 * a * t**2 = d/2 -> t = sqrt(d/a). The time to cover
        the distance is twice as much: t = 2 * sqrt(d/a). Other factors are added to convert units.

        return: flight time to cover that distance with the m drive in days
        """
        if type(d_km) is str:
            d_km = float(d_km)

        BbwUtils.test_geq("d_km", d_km, 0)

        return 2 * math.sqrt(1000 * d_km / (self.m_drive() * 10)) / (60 * 60 * 24)

    @staticmethod
    def j_drive_required_time(n_jumps=1):
        """
        jump drive does not depend on the distance but on the number of jumps. Returns flight time in days
        """
        if type(n_jumps) is str:
            n_jumps = float(n_jumps)
        BbwUtils.test_geq("n_jumps", n_jumps, 0)

        return (148 * n_jumps + d20.roll(f"{6*n_jumps}d6").total) / 24

    @staticmethod
    def j_drive_required_fuel(n_sectors):
        return 20 * n_sectors

    def ck_j_drive(self, w0, w1):
        n_sectors = BbwWorld.distance(w0, w1)
        ans = []
        if n_sectors > self.j_drive():
            ans.append(
                f"ship's j drive (`{self.j_drive()}`) < distance (`{n_sectors}`) between `{w1.name()}` and"
                f" `{w0.name()}`. Too far!"
            )
        res = self.get_objs(name="fuel, refined", cont="fuel tank")

        rs = BbwSpaceShip.j_drive_required_fuel(n_sectors)
        if res.count() < rs:
            ans.append(f"currently the ship holds `{res.count()}` tons of refined fuel. {rs} required for this jump!")

        return "\n".join(ans)

    def add_fuel(self, source, count=float("inf")):
        count = float(count)
        BbwUtils.test_geq("fuel tons", count, 0)
        if count == 0:
            return BbwRes()

        source, require_scoop = BbwUtils.get_objs(
            raw_list=BbwSpaceShip._require_fuel_scoop.items(), name=source, only_one=True
        )[0]

        if require_scoop and not self.has_fuel_scoop():
            raise InvalidArgument(f"the spaceship cannot scoop fuel from a {source} without a fuel scoop!")

        fuel_name = "fuel, refined" if source == "refined" else "fuel, unrefined"
        fuel_obj = BbwItemFactory.make(name=fuel_name, count=1)
        base_price = fuel_obj.value()
        fuel_obj.set_count(count)

        res = self.dist_obj(obj=fuel_obj, cont="fuel tank")

        price = 0 if require_scoop == 1 else res.count() * base_price

        return res, price

    def consume_fuel(self, count: int):
        BbwUtils.test_geq("count", count, 0)
        if count == 0:
            return BbwRes()

        res = self.get_objs(name="fuel, refined", cont="fuel tank")
        if res.count() < count:
            raise NotAllowed(f"not enough refined fuel! In tanks: `{res.count()}` < requested: `{count}`")
        return self.del_obj(name="fuel, refined", count=count, cont="fuel tank")

    def refine_fuel(self):
        res = self.del_obj(name="fuel, unrefined", cont="fuel tank")
        total_time = res.count() / self.fuel_refiner_speed()
        new_fuel = BbwItemFactory.make(name="fuel, refined", count=res.count())
        if new_fuel is None:
            return BbwRes(), 0

        self.dist_obj(obj=new_fuel, cont="fuel tank")
        return res, total_time

    def set_has_cargo_crane(self, v):
        v = bool(int(v))
        self._has_cargo_crane = v

    def has_cargo_crane(self):
        return self._has_cargo_crane

    def set_has_cargo_scoop(self, v):
        v = bool(int(v))
        self._has_cargo_scoop = v

    def has_cargo_scoop(self):
        return self._has_cargo_scoop

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

    def set_fuel_refiner_speed(self, v):
        v = int(v)
        BbwUtils.test_geq("fuel refiner speed", v, 0)
        self._fuel_refiner_speed = v

    def fuel_refiner_speed(self):
        return self._fuel_refiner_speed

    def set_m_drive(self, v):
        v = int(v)
        BbwUtils.test_geq("drive m", v, 0)
        self._m_drive = v

    def m_drive(self):
        return self._m_drive

    def set_j_drive(self, v):
        v = int(v)
        BbwUtils.test_geq("drive j", v, 0)
        self._j_drive = v

    def j_drive(self):
        return self._j_drive

    def set_power_plant(self, v):
        v = int(v)
        BbwUtils.test_geq("power plant", v, 0)
        self._power_plant = v

    def power_plant(self):
        return self._power_plant

    def var_life_support(self, t):
        t = int(t)
        BbwUtils.test_geq("trip time", t, 0)

        res = self.get_objs(type0=BbwPerson)

        return res, round(1000 * res.count() * t / 28)

    def is_armed(self):
        return self.get_objs(with_all_tags={"weapon"}, type0=BbwItem).count() > 0

    @staticmethod
    def _header(detail_lvl=0):
        s = BbwVehicle._header(detail_lvl)

        return s

    def _str_table(self, detail_lvl=0):
        s = [
            str(i)
            for i in [
                *super()._str_table(detail_lvl != 2),
            ]
        ]

        return s

    def __str__(self, detail_lvl=1):
        s = ""
        s += BbwUtils.print_table(
            self._str_table(detail_lvl), headers=BbwSpaceShip._header(detail_lvl), detail_lvl=detail_lvl
        )

        if detail_lvl == 0:
            return s
        h = [
            "drive m",
            "drive j",
            "power",
            "refiner (tons/day)",
            "streamlined",
            "f. scoop",
            "c. scoop",
            "c. crane",
            "armed",
        ]
        tab = [
            str(i)
            for i in [
                self.m_drive(),
                self.j_drive(),
                self.power_plant(),
                self.fuel_refiner_speed(),
                self.is_streamlined(),
                self.has_fuel_scoop(),
                self.has_cargo_scoop(),
                self.has_cargo_crane(),
                self.is_armed(),
            ]
        ]
        s += BbwUtils.print_table(tab, headers=h, detail_lvl=detail_lvl)

        if detail_lvl == 1:
            return s

        s += super(BbwVehicle, self).__str__(detail_lvl=-1)

        return s
