from cogst5.base import *
from cogst5.utils import *


class WorldCodes:
    def __init__(self, name, description, restrictions):
        self._name = name
        self._description = description
        self._restrictions = restrictions

    def __eq__(self, other):
        for k, v in self.restrictions().items():
            if getattr(other, k)()[1] not in v:
                return False

        return True

    def restrictions(self):
        return self._restrictions

    def name(self):
        return self._name

    def description(self):
        return self._description

    def __str__(self, detail_lvl=0):
        if detail_lvl == 0:
            return self.name
        return f"{self.description()} (`{self.name()}`)"

@BbwUtils.for_all_methods(BbwUtils.type_sanitizer_decor)
class BbwWorld(BbwObj):
    _zones = ["normal", "amber", "red"]
    _trade_code_table = BbwUtils.gen_dict(
        [
            WorldCodes(
                "Ag", "agricultural", {"ATM": list(range(4, 10)), "HYDRO": list(range(4, 9)), "POP": list(range(5, 8))}
            ),
            WorldCodes("As", "asteroid", {"SIZE": [0], "ATM": [0], "HYDRO": [0]}),
            WorldCodes("Ba", "barren", {"GOV": [0], "POP": [0], "LAW": [0]}),
            WorldCodes("De", "desert", {"ATM": list(range(2, 10)), "HYDRO": [0]}),
            WorldCodes("Fl", "fluid oceans", {"ATM": list(range(10, 37)), "HYDRO": list(range(1, 37))}),
            WorldCodes("Ga", "garden", {"SIZE": list(range(6, 9)), "ATM": [5, 6, 8], "HYDRO": list(range(5, 8))}),
            WorldCodes(
                "Hi",
                "high population",
                {
                    "POP": list(range(9, 37)),
                },
            ),
            WorldCodes(
                "Ht",
                "high technology",
                {
                    "TL": list(range(12, 37)),
                },
            ),
            WorldCodes("Ic", "ice-capped", {"ATM": [0, 1], "HYDRO": list(range(1, 37))}),
            WorldCodes("In", "industrial", {"ATM": [0, 1, 2, 4, 7, 9, 10, 11, 12], "POP": list(range(9, 37))}),
            WorldCodes(
                "Ln",
                "low population",
                {
                    "POP": [1, 2, 3],
                },
            ),
            WorldCodes("Lt", "low technology", {"POP": list(range(1, 37)), "TL": list(range(0, 6))}),
            WorldCodes(
                "Na",
                "non-agricultural",
                {"ATM": list(range(0, 4)), "HYDRO": list(range(0, 4)), "POP": list(range(6, 37))},
            ),
            WorldCodes("Ni", "non-industrial", {"POP": list(range(4, 7))}),
            WorldCodes("Po", "poor", {"ATM": list(range(2, 6)), "HYDRO": list(range(0, 4))}),
            WorldCodes(
                "Ri",
                "rich",
                {
                    "ATM": [6, 8],
                    "POP": [6, 7, 8],
                    "GOV": list(range(4, 10)),
                },
            ),
            WorldCodes("Va", "vacuum", {"ATM": [0]}),
            WorldCodes("Wa", "waterworld", {"HYDRO": list(range(10, 37)), "ATM": [*range(3, 10), *range(13, 37)]}),
        ]
    )

    _SP_table = [
        "excellent, fuel: refined, shipyard: (all), repair",
        "good, fuel: refined, shipyard: (spacecraft), repair",
        "routine, fuel: unrefined, shipyard: (small craft), repair",
        "poor, fuel: unrefined, limited repair",
        "frontier, fuel: none",
        "no starport, fuel: none",
    ]

    _SP_docking_fee_table = [1000, 500, 100, 10, 0]
    _SIZE_d_table = [1000, 1600, 3200, 4800, 6400, 8000, 9600, 11200, 12800, 14400, 16000]
    _SIZE_G_table = [0, 0.05, 0.15, 0.25, 0.35, 0.45, 0.7, 0.9, 1, 1.25, 1.4]
    _ATM_table = [
        "none, 0 Atm, vacc. suit req.",
        "trace, 0.001-0.009 Atm, vacc suit req.",
        "very thin, tainted, 0.1-0.42 Atm,respirator and filter req.",
        "very thin, 0.1-0.42 Atm,respirator req.",
        "thin, tainted , 0.43-0.7 Atm, filter req.",
        "thin, 0.43-0.7 Atm",
        "standard, 0.7-1.49 Atm",
        "standard, tainted, 0.7-1.49 Atm, filter req.",
        "dense, 1.5-2.49 Atm",
        "dense, tainted, 1.5-2.49 Atm, filter req.",
        "exotic, air supply req.",
        "corrosive, vacc suit req.",
        "insidious, vacc suit req.",
        "very dense, > 2.5 Atm",
        "low, <= 0.5 Atm",
        "unusual",
    ]
    _HYDRO_table = [
        "0%-5%",
        "6%-15%",
        "16%-25%",
        "26%-35%",
        "36%-45%",
        "46%-55%",
        "56%-65%",
        "66%-75%",
        "76%-85%",
        "86%-95%",
        "96%-100%",
    ]
    _GOV_table = [
        "none",
        "corporation",
        "participating democracy",
        "self-perpetuating oligarchy",
        "representative democracy",
        "feudal technocracy",
        "captive government",
        "balkanization",
        "civil service bureaucracy",
        "impersonal bureaucracy",
        "charismatic dictator",
        "non-charismatic leader",
        "charismatic oligarchy",
        "religious dictatorship",
        "religious autocracy",
        "totalitarian oligarchy",
    ]
    _LAW_table = [
        "no restrictions",
        "poison gas, explosives, undetectable weapons, WMD, battle dress",
        "portable energy weapons, combat armour",
        "military weapons, flak",
        "light assault weapons , submachine guns, cloth",
        "personal concealable weapons, mesh",
        "all firearms except shotguns and stunners, carring weapons discouraged",
        "shotguns",
        "all bladed weapons, stunners, all visible armour",
        "all weapons, all armour",
    ]

    def __init__(self, uwp, zone, hex, sector, *args, **kwargs):
        self.set_uwp(uwp)
        self.set_zone(zone)
        self.set_hex(hex)
        self.set_sector(sector)
        self.set_people()
        self.set_trade_codes()
        self.set_suppliers()
        self.set_docking_fee()

        super().__init__(*args, **kwargs)

    def set_suppliers(self):
        self._suppliers = BbwContainer(name="suppliers")

    def set_supply(self, bbwtrade, t, names=""):
        obj = [i for i, _ in self.suppliers().get_objs(name=names).objs()]
        for i in obj:
            i.set_supply(bbwtrade, self, t)


    @BbwUtils.set_if_not_present_decor
    def suppliers(self):
        return self._suppliers

    def set_people(self):
        self._people = BbwContainer(name="people")

    @BbwUtils.set_if_not_present_decor
    def people(self):
        return self._people

    def uwp(self):
        return self._uwp

    def set_trade_codes(self, d=None):
        if d is not None:
            if type(d) is not set:
                d = eval(d)

            self._trade_codes = set()
            for k in d:
                self.set_trade_code(k, 1)
            return

        self._trade_codes = set()
        for k, v in self._trade_code_table.items():
            if v == self:
                self.set_trade_code(k, 1)

    def set_trade_code(self, name, value=None):
        if value is None:
            name, value = eval(name)

        if name not in BbwWorld._trade_code_table:
            raise InvalidArgument(
                f"Unknown trade code `{name}`. Possible options: `{', '.join(BbwWorld._trade_code_table.keys())}`"
            )
        if value is None:
            self.trade_codes().discard(name)
            return

        self.trade_codes().add(name)

    def trade_codes(self):
        if not hasattr(self, "_trade_codes"):
            self.set_trade_codes()
        return self._trade_codes

    def sector(self):
        return self._sector

    def set_sector(self, v: tuple):
        self._sector = v

    def set_uwp(self, v: str):
        v = str(v)
        v = v.replace("-", "")
        BbwUtils.test_hexstr("uwp", v, [8])
        self._uwp = v

    def zone(self):
        return self._zone

    def set_zone(self, v):
        v = str(v)
        v = BbwUtils.get_objs(self._zones, v, only_one=True)[0]
        self._zone = v

    def d_km(self):
        return self.SIZE()[3]

    def set_hex(self, v):
        v = str(v)
        if len(v) != 4:
            raise AttributeError(f"the hex location {v} must be 4 digits long!")

        col = int(v[0:2])
        row = int(v[2:4])
        self._hex = v

    def hex(self):
        return self._hex

    def hex_x(self):
        return int(self._hex[0:2])

    def hex_y(self):
        return int(self._hex[2:4])

    def sec_x(self):
        return self.sector()[0]

    def sec_y(self):
        return self.sector()[1]

    def _get_SP_table_entry(self, table):
        idx = ord(self.uwp()[0]) - ord("A")
        idx = min(idx, len(table) - 1)
        return table[idx]

    def set_docking_fee(self, v=None):
        if v is None:
            v = self._get_SP_table_entry(BbwWorld._SP_docking_fee_table) * d20.roll("1d6").total

        v = int(v)
        self._docking_fee = v

    @BbwUtils.set_if_not_present_decor
    def docking_fee(self):
        return self._docking_fee

    def SP(self):
        idx = ord(self.uwp()[0])-ord("A")
        lett = self.uwp()[0]

        desc = self._get_SP_table_entry(BbwWorld._SP_table)
        return lett, idx, desc

    def SIZE(self):
        idx = int(self.uwp()[1], 36)
        affix = "" if idx > 0 else "< "
        return (
            self.uwp()[1],
            idx,
            f"{affix}{BbwWorld._SIZE_d_table[idx]} Km, {BbwWorld._SIZE_G_table[idx]} G",
            BbwWorld._SIZE_d_table[idx],
        )

    def ATM(self):
        idx = int(self.uwp()[2], 36)
        return self.uwp()[2], idx, BbwWorld._ATM_table[idx]

    def HYDRO(self):
        idx = int(self.uwp()[3], 36)
        return self.uwp()[3], idx, BbwWorld._HYDRO_table[min(idx, len(BbwWorld._HYDRO_table) - 1)]

    def POP(self):
        idx = int(self.uwp()[4], 36)
        if idx == 0:
            desc = "0"
        elif idx == 1:
            desc = "1-99"
        else:
            desc = f"{10**idx:,}-{(10**(idx+1))-1:,}"

        return self.uwp()[4], int(self.uwp()[4], 36), desc

    def GOV(self):
        idx = int(self.uwp()[5], 36)
        return self.uwp()[5], idx, BbwWorld._GOV_table[idx]

    def LAW(self):
        idx = int(self.uwp()[6], 36)
        return self.uwp()[6], idx, BbwWorld._LAW_table[min(idx, len(BbwWorld._LAW_table) - 1)]

    def TL(self):
        return self.uwp()[7], int(self.uwp()[7], 36)

    @staticmethod
    def distance(w0, w1):
        x0, y0, xs0, ys0, x1, y1, xs1, ys1 = (
            w0.hex_x(),
            w0.hex_y(),
            w0.sec_x(),
            w0.sec_y(),
            w1.hex_x(),
            w1.hex_y(),
            w1.sec_x(),
            w1.sec_y(),
        )
        return BbwUtils.distance(
            *BbwUtils.hex_2_cube(*BbwUtils.local_2_global(x0, y0, xs0, ys0)),
            *BbwUtils.hex_2_cube(*BbwUtils.local_2_global(x1, y1, xs1, ys1)),
        )

    def _str_table(self, detail_lvl=0):
        if detail_lvl == 0:
            return [self.name(), self.uwp()]
        else:
            return [self.name(), self.uwp(), self.d_km(), self.zone(), self.hex(), str(self.sector())]

    def __str__(self, detail_lvl=0):
        s = BbwUtils.print_table(self._str_table(detail_lvl), headers=self._header(detail_lvl), detail_lvl=detail_lvl)
        if detail_lvl == 0:
            return s

        h = ["category", "code", "description"]
        t = [
            ["starport", BbwUtils.print_code(self.SP()[0]), f"{self.SP()[2]}, docking fee: {self.docking_fee()} Cr"],
            ["size", BbwUtils.print_code(self.SIZE()[0]), self.SIZE()[2]],
            ["atm", BbwUtils.print_code(self.ATM()[0]), self.ATM()[2]],
            ["hydro", BbwUtils.print_code(self.HYDRO()[0]), self.HYDRO()[2]],
            ["pop", BbwUtils.print_code(self.POP()[0]), self.POP()[2]],
            ["gov", BbwUtils.print_code(self.GOV()[0]), self.GOV()[2]],
            ["law", BbwUtils.print_code(self.LAW()[0]), self.LAW()[2]],
            [
                "TL",
                BbwUtils.print_code(self.TL()[0]),
            ],
        ]
        s += BbwUtils.print_table(t, headers=h, detail_lvl=1)

        if len(self.people()):
            s += self.people().__str__(1)

        s += f"trade codes: " + ", ".join([BbwWorld._trade_code_table[i].__str__(1) for i in self.trade_codes()])
        s += "\n"
        for v in self.suppliers().values():
            s += f"supplier: `{v.name()}`\n"
            s += v.print_supply()

        return s

    @staticmethod
    def _header(detail_lvl=0):
        if detail_lvl == 0:
            return ["name", "uwp"]
        else:
            return ["name", "uwp", "d_km", "zone", "hex", "sector"]
