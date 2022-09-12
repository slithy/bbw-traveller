from cogst5.models.errors import *

import math
import d20

from cogst5.base import *
from cogst5.person import *
from cogst5.item import *
from cogst5.utils import *

import bisect


class BbwVehicle(BbwObj):
    def __init__(
        self,
        type="",
        TL=0,
        armour=0,
        containers={"cargo": 0.0, "staterooms": 0.0, "fuel tank": 0.0},
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
        return self.status()

    def containers(self):
        return self._containers

    def get_container(self, name):
        _, v = get_item(name, self.containers())
        return v

    def get_people(self):
        return [
            item for container in self.containers().values() for item in container.values() if type(item) is BbwPerson
        ]

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
    _passenger_wp_table = [[1, 5, 7, 16], [-4, 0, 1, 3]]
    _passenger_starport_table = [["A", "B", "D", "E", "X"], [2, 1, 0, -1, -3]]
    _passenger_traffic_table = [[1, 3, 6, 10, 13, 15, 16, 17, 18, 19, 1000], [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]]
    _passenger_zone_dict = {"normal": 0, "amber": 1, "red": -4}

    _cargo_wp_table = [[1, 5, 7, 16], [-4, 0, 2, 4]]
    _cargo_starport_table = _passenger_starport_table
    _cargo_TL_table = [[6, 8, 1000], [-1, 0, 2]]
    _cargo_traffic_table = [[1, 3, 5, 8, 11, 14, 16, 17, 18, 19, 1000], [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]]
    _cargo_zone_dict = {"normal": 0, "amber": -2, "red": -6}
    _cargo_lot_ton_multi_dict = {"major": 10, "minor": 5, "incidental": 1, "mail": 5}

    _ticket_dict = {
        "high": [
            9000,
            14000,
            21000,
            34000,
            60000,
            210000,
        ],
        "middle": [6500, 10000, 14000, 23000, 40000, 130000],
        "basic": [2000, 3000, 5000, 8000, 14000, 55000],
        "low": [700, 1300, 2200, 3900, 7200, 27000],
        "cargo": [1000, 1600, 2600, 4400, 8500, 32000],
    }

    _cargo_traffic_table_2_mail_table = [[-10, -5, 4, 9, 1000], [-2, -1, 0, 1, 2]]
    _mail_TL_table = [[5, 1000], [-4, 0]]

    def __init__(
        self,
        drive_m=0,
        drive_j=0,
        power_plant=0,
        fuel_refiner_speed=40,
        is_streamlined=True,
        has_fuel_scoop=True,
        has_cargo_crane=True,
        info="",
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
        self.set_info(info)
        super().__init__(*args, **kwargs)

    def flight_time_m_drive(self, d_km):
        """
        We suppose that we start from 0 speed and we reach the destination with 0 speed. d is the distance we want to cover.
        the time to cover half of the distance follows the equation: 1/2 * a * t**2 = d/2 -> t = sqrt(d/a). The time to cover
        the distance is twice as much: t = 2 * sqrt(d/a). Other factors are added to convert units.

        return: flight time to cover that distance with the m drive in days
        """
        d_km = float(d_km)
        test_geq("d_km", d_km, 0)

        return 2 * math.sqrt(1000 * d_km / (self.drive_m() * 10)) / (60 * 60 * 24)

    def flight_time_j_drive(self, n_jumps):
        """
        jump drive does not depend on the distance but on the number of jumps. Returns flight time in days
        """

        n_jumps = int(n_jumps)
        test_geq("n_jumps", n_jumps, 0)

        return (148 * n_jumps + d20.roll(f"{6*n_jumps}d6").total) / 24

    def flight_time_planet_2_planet(self, d1_km, d2_km, n_jumps=1):
        d1_km = float(d1_km)
        test_geq("d1_km", d1_km, 0)
        d2_km = float(d2_km)
        test_geq("d2_km", d2_km, 0)

        return (
            self.flight_time_m_drive(d1_km * 100),
            self.flight_time_j_drive(n_jumps),
            self.flight_time_m_drive(d2_km * 100),
        )

    def get_main_stateroom(self):
        _, c = get_item("main stateroom", self.containers())
        return c

    def get_main_cargo(self):
        _, c = get_item("main cargo", self.containers())
        return c

    def get_main_lowberth(self):
        _, c = get_item("main lowberth", self.containers())
        return c

    def get_all_cargo_containers(self):
        return [c for c in self.containers().values() if "cargo" in c.name()]

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

    def info(self):
        return self._info

    def set_info(self, v):
        self._info = str(v)

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

    def var_life_support(self, t):
        t = int(t)
        test_geq("trip time", t, 0)
        return round(1000 * len(self.get_people()) * t / 28)

    def is_armed(self):
        try:
            _, v = get_item("weapon", self.containers())
        except SelectionException:
            return False
        return v.free_space() == v.capacity()

    def find_passengers(self, carouse_or_broker_or_streetwise_mod, SOC_mod, kind, n_sectors, w0, w1):
        """
        - distance: in parsec
        - carouse_brocker_or_streetwise_mod: carouse or broker or streetwise modifier
        - SOC_mod: SOC modifier
        - w0: departure world data (pop, starport, zone)
        - w1: arrival world data (pop, starport, zone)
        """
        carouse_or_broker_or_streetwise_mod, SOC_mod = int(carouse_or_broker_or_streetwise_mod), int(SOC_mod)

        n_sectors = int(n_sectors)
        test_geq("n_sectors", n_sectors, 0)

        kind, _ = get_item(kind, BbwPerson.std_roles)

        r = d20.roll("2d6").total + carouse_or_broker_or_streetwise_mod + SOC_mod - 8

        if kind == "high":
            r -= 4

        if kind == "low":
            r += 1

        for w in [w0, w1]:
            r += get_modifier(w["pop"], self._passenger_wp_table)
            r += get_modifier(w["starport"], self._passenger_starport_table)
            r += self._passenger_zone_dict[w["zone"]]

        r -= n_sectors - 1

        nd = get_modifier(r, self._passenger_traffic_table)

        person = BbwPerson(name=f"{kind} passenger", role=kind, salary_ticket=self._ticket_dict[kind][n_sectors - 1])

        np = d20.roll(f"{nd}d6").total
        try:
            stateroom = self.get_main_stateroom() if kind != "low" else self.get_main_lowberth()
            cargo = self.get_main_cargo()
        except SelectionException:
            return "no space"

        np = min(np, math.floor(stateroom.free_space() / person.capacity()))
        if person.luggage() > 0:
            np = min(np, math.floor(cargo.free_space() / person.luggage()))

        if np == 0:
            return "not qualified"

        person.set_count(np)
        stateroom.add_item(person)
        luggage = BbwItem(name=f"{person.name()} luggage", capacity=person.luggage())
        cargo.add_item(luggage)

        return str(person.count())

    def _cargo_traffic_table_roll(self, brocker_or_streetwise_mod, SOC_mod, kind, n_sectors, w0, w1):
        """
        - n_sectors: distance in parsec
        - brocker_or_streetwise_mod: broker or streetwise modifier
        - SOC_mod: SOC modifier
        - w0: departure world data (pop, starport, TL, zone)
        - w1: arrival world data (pop, starport, TL, zone)
        """
        brocker_or_streetwise_mod, SOC_mod = int(brocker_or_streetwise_mod), int(SOC_mod)

        n_sectors = int(n_sectors)
        test_geq("n_sectors", n_sectors, 0)

        kind, _ = get_item(kind, self._cargo_lot_ton_multi_dict)

        r = d20.roll("2d6").total + brocker_or_streetwise_mod + SOC_mod - 8

        if kind == "major":
            r -= 4

        if kind == "incidental":
            r += 2

        for w in [w0, w1]:
            r += get_modifier(w["pop"], self._cargo_wp_table)
            r += get_modifier(w["starport"], self._cargo_starport_table)
            r += get_modifier(w["TL"], self._cargo_TL_table)
            r += self._cargo_zone_dict[w["zone"]]

        r -= n_sectors - 1

        return r, get_modifier(r, self._passenger_traffic_table)

    def _distribute_cargo(self, item):
        cargos = self.get_all_cargo_containers()
        tot_free_space = 0
        for i in cargos:
            tot_free_space += i.free_space()

        if tot_free_space < item.capacity():
            return None

        main_cargo = self.get_main_cargo()
        self._fill_container(main_cargo, item)
        for i in cargos:
            self._fill_container(i, item)

    def _fill_container(self, c, item):
        if item.size() == 0 or c.free_space() == 0:
            return

        v = min(item.size(), c.free_space())

        new_item = BbwItem(name=item.name(), capacity=v, value=item.value() * v / item.capacity())
        c.add_item(new_item)
        item.set_size(item.size() - v)

    def find_mail(
        self,
        brocker_or_streetwise_mod,
        SOC_mod,
        max_naval_or_scout_rank,
        max_SOC_mod,
        n_sectors,
        w0,
        w1,
    ):
        """
        - n_sectors: distance in parsec
        - brocker_or_streetwise_mod: broker or streetwise modifier
        - SOC_mod: SOC modifier
        - max_naval_or_scout_rank: max naval or scount rank of the crew
        - max_SOC_mod: max SOC modifier of the crew
        - w0: departure world data (pop, starport, TL, zone)
        - w1: arrival world data (pop, starport, TL, zone)
        """
        max_naval_or_scout_rank, max_SOC_mod = int(max_naval_or_scout_rank), int(max_SOC_mod)

        nd, _ = self._cargo_traffic_table_roll(brocker_or_streetwise_mod, SOC_mod, "mail", n_sectors, w0, w1)
        r = (
            get_modifier(nd, self._cargo_traffic_table_2_mail_table)
            + max_naval_or_scout_rank
            + max_SOC_mod
            + d20.roll(f"2d6").total
        )
        for w in [w0, w1]:
            r += get_modifier(w["TL"], self._mail_TL_table)

        if self.is_armed():
            r += 2

        if r < 12:
            return "not qualified"

        n_canisters = d20.roll("1d6").total
        tot_mail = BbwItem(
            name=f"mail cargo",
            capacity=self._cargo_lot_ton_multi_dict["mail"] * n_canisters,
            value=25000 * n_canisters,
            count=1,
        )
        self._distribute_cargo(tot_mail)

        if tot_mail.size() == 0:
            return str(n_canisters)

        return f"no space"

    def find_cargo(
        self,
        brocker_or_streetwise_mod,
        SOC_mod,
        kind,
        n_sectors,
        w0,
        w1,
    ):
        """
        - n_sectors: distance in parsec
        - brocker_or_streetwise_mod: broker or streetwise modifier
        - SOC_mod: SOC modifier
        - w0: departure world data (pop, starport, TL, zone)
        - w1: arrival world data (pop, starport, TL, zone)
        """
        n_sectors = int(n_sectors)

        _, nd = self._cargo_traffic_table_roll(brocker_or_streetwise_mod, SOC_mod, kind, n_sectors, w0, w1)

        if nd == 0:
            return f"not qualified"

        tons_per_lot = d20.roll(f"1d6").total * self._cargo_lot_ton_multi_dict[kind]

        n_lots = d20.roll(f"{nd}d6").total

        for i in range(n_lots):
            tot_cargo = BbwItem(
                name=f"{kind} cargo (lot {i})",
                capacity=tons_per_lot,
                value=self._ticket_dict["cargo"][n_sectors] * tons_per_lot,
                count=1,
            )
            self._distribute_cargo(tot_cargo)
            if tot_cargo.size() != 0:
                return f"{i}/{n_lots} lots"

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
            "info",
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
                self.info(),
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


#

# print(get_modifier('A', BbwSpaceShip._passenger_starport_table))
# exit()

# a = BbwSpaceShip(
#         name="test",
#         drive_m=1,
#         drive_j=2,
#         power_plant=105,
#         fuel_refiner_speed=40,
#         is_streamlined=True,
#         has_fuel_scoop=True,
#         has_cargo_crane=True,
#         info="",
#         capacity=200,
#     size=180,
#     containers={"main cargo": 21, "cargo 2": 8, "cargo 3": 8, "staterooms": 26, "fuel tank": 0.0}
#     )
# b = BbwItem(name="stuff", count=7, capacity=0.1)
# a.get_main_cargo().add_item(b)
# w = {'zone':'normal','starport':'A','pop':7, 'd':12700, 'TL':12}
# a.find_mail(2, 3, 1, 3, 1, w, w)
# for i in ["major", "minor", "incidental"]:
#     a.find_cargo(2, 3, i, 1, w, w)
# print(a.__str__(False))
#
# exit()
