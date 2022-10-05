import copy

from cogst5.person import *
from cogst5.item import *
from cogst5.world import *


class BbwExpr:
    def __init__(self, l=[], q=None):
        if q is not None:
            l = [(l, q)]
        self._l = []
        if type(l) is list:
            self._l = l
        else:
            self._l = (BbwExpr() + l)._l

    def __add__(self, o):
        if type(o) is BbwExpr:
            return BbwExpr([*self._l, *o._l])
        if type(o) is tuple:
            return BbwExpr([*self._l, o])
        if type(o) is d20.dice.RollResult:
            return BbwExpr([*self._l, (o, o.total)])
        raise ValueError(f"{o} must be of type tuple, BbwExpr or d20.dice.RollResult")

    def __sub__(self, o):
        return self + (o * -1)

    def __gt__(self, o):
        if type(o) is BbwExpr:
            if len(self._l) == 0:
                return False
            if len(o._l) == 0:
                return True
            return int(self) > int(o)

    def __lt__(self, o):
        if type(o) is BbwExpr:
            if len(self._l) == 0:
                return True
            if len(o._l) == 0:
                return False
            return int(self) < int(o)

    def __mul__(self, o):
        if type(o) is float or type(o) is int:
            return BbwExpr([(d, i * o) for d, i in self._l])

    def __rmul__(self, o):
        return self.__mul__(o)

    def __int__(self):
        return sum(i for _, i in self._l)

    def __str__(self, is_compact=False):
        if len(self._l) == 0:
            return ""

        def affix(idx, v, i):
            s = " " if idx else ""
            if idx and v >= 0:
                s += "+ "
            if type(i) is d20.dice.RollResult:
                s += i.__str__()
            else:
                s += f"{v} [" + i + "]"
            return s if not is_compact else s.replace(" ", "").replace("`", "")

        s = "".join([f"{affix(idx, v, i)}" for idx, (i, v) in enumerate(self._l)])
        if len(self._l) == 1:
            return s if not is_compact else s.replace(" ", "").replace("`", "")

        s += f" = {int(self)}"
        return s if not is_compact else s.replace(" ", "").replace("`", "")


class Good:
    def __init__(self, name, tons, ton_multi, buy_mods, sell_mods, aval_restr=set()):
        self._name = name
        self._tons = tons
        self._ton_multi = ton_multi
        self._buy_mods = buy_mods
        self._sell_mods = sell_mods
        self._aval_restr = aval_restr

    def aval_restr(self):
        return self._aval_restr

    def name(self):
        return self._name

    def ton_multi(self):
        return self._ton_multi

    def tons(self):
        return self._tons

    def roll_tons(self, w):
        s = self.tons()
        avg0, min0, max0 = BbwUtils.avg_min_max(s)
        if w.POP()[1] <= 3:
            s += "-3"
            avg0, min0, max0 = max(avg0 - 3, 0), max(min0 - 3, 0), max(max0 - 3, 0)
        if w.POP()[1] >= 9:
            s += "+3"
            avg0, min0, max0 = avg0 + 3, min0 + 3, max0 + 3

        if self.ton_multi() != 1:
            s = f"({s})*{self.ton_multi()}"

        r = BbwExpr()
        r += d20.roll(s)
        return r, avg0, min0, max0

    def buy_mods(self):
        return self._buy_mods

    def sell_mods(self):
        return self._sell_mods


class BbwTrade:
    _passenger_wp_table = [[1, 5, 7, 16], [-4, 0, 1, 3]]
    _passenger_starport_table = [
        [int("A", 36), int("B", 36), int("D", 36), int("E", 36), int("X", 36)],
        [2, 1, 0, -1, -3],
    ]
    _passenger_traffic_table = [[1, 3, 6, 10, 13, 15, 16, 17, 18, 19, 1000], [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]]
    _passenger_zone_dict = {"normal": 0, "amber": 1, "red": -4}

    _freight_wp_table = [[1, 5, 7, 16], [-4, 0, 2, 4]]
    _freight_starport_table = _passenger_starport_table
    _freight_TL_table = [[6, 8, 1000], [-1, 0, 2]]
    _freight_traffic_table = [[1, 3, 5, 8, 11, 14, 16, 17, 18, 19, 1000], [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]]
    _freight_zone_dict = {"normal": 0, "amber": -2, "red": -6}

    _freight_traffic_table_2_mail_table = [[-10, -5, 4, 9, 1000], [-2, -1, 0, 1, 2]]
    _mail_TL_table = [[5, 1000], [-4, 0]]

    _speculative_trading_table = [
        Good("common electronics", "2d6", 10, {"In": 2, "Ht": 3, "Ri": 1}, {"Ni": 2, "Lt": 1, "Po": 1}),
        Good("common industrial goods", "2d6", 10, {"Na": 2, "In": 5}, {"Ni": 2, "Ag": 2}),
        Good("common manufactured goods", "2d6", 10, {"Na": 2, "In": 5}, {"Ni": 3, "Hi": 2}),
        Good("common raw materials", "2d6", 20, {"Ag": 3, "Ga": 2}, {"In": 2, "Po": 2}),
        Good(
            "common consumables",
            "2d6",
            20,
            {"Ag": 3, "Wa": 2, "Ga": 1, "As": -4},
            {"As": 1, "Fl": 1, "Ic": 1, "Hi": 1},
        ),
        Good("common ore", "2d6", 20, {"As": 4}, {"In": 3, "Ni": 1}),
        Good("advanced electronics", "1d6", 5, {"In": 2, "Ht": 3}, {"Ni": 1, "Ri": 2, "As": 3}, {"In", "Ht"}),
        Good("advanced machine parts", "1d6", 5, {"In": 2, "Ht": 1}, {"Ni": 1, "As": 2}, {"In", "Ht"}),
        Good("advanced manufactured goods", "1d6", 5, {"In": 1}, {"Hi": 1, "Ri": 2}, {"In", "Ht"}),
        Good("advanced weapons", "1d6", 5, {"Ht": 2}, {"Po": 1, "amber": 2, "red": 4}, {"In", "Ht"}),
        Good("advanced vehicles", "1d6", 5, {"Ht": 2}, {"As": 2, "Ri": 2}, {"In", "Ht"}),
        Good("biochemicals", "1d6", 5, {"Ag": 1, "Wa": 2}, {"In": 2}, {"Ag", "Wa"}),
        Good("crystals and gems", "1d6", 5, {"As": 2, "De": 1, "Ic": 1}, {"In": 3, "Ri": 2}, {"As", "De", "Ic"}),
        Good("cybernetics", "1d6", 1, {"Ht": 1}, {"As": 1, "Ic": 1, "Ri": 2}, {"Ht"}),
        Good("live animals", "1d6", 10, {"Ag": 2}, {"Ln": 3}, {"Ag", "Ga"}),
        Good("luxury consumables", "1d6", 10, {"Ag": 2, "Wa": 1}, {"Ri": 2, "Hi": 2}, {"Ag", "Ga", "Wa"}),
        Good("luxury goods", "1d6", 1, {"Hi": 1}, {"Ri": 4}, {"Hi"}),
        Good("medical supplies", "1d6", 5, {"Hi": 2}, {"In": 2, "Po": 1, "Ri": 1}, {"Hi", "Ht"}),
        Good("petrochemicals", "1d6", 10, {"De": 2}, {"In": 2, "Ag": 1, "Lt": 2}, {"De", "Fl", "Ic", "Wa"}),
        Good("pharmaceuticals", "1d6", 1, {"As": 2, "Hi": 1}, {"Ri": 2, "Lt": 1}, {"As", "De", "Hi", "Wa"}),
        Good("polymers", "1d6", 10, {"In": 1}, {"Ri": 2, "Ni": 1}, {"In"}),
        Good(
            "precious metals",
            "1d6",
            1,
            {"As": 3, "De": 1, "Ic": 2},
            {"Ri": 3, "In": 2, "Ht": 1},
            {"As", "De", "Ic", "Wa"},
        ),
        Good("radioactives", "1d6", 1, {"As": 2, "Ln": 2}, {"In": 3, "Ht": 1, "Ni": -2, "Ag": -3}, {"As", "De", "Ln"}),
        Good("robots", "1d6", 5, {"In": 1}, {"Ag": 2, "Ht": 1}, {"In"}),
        Good("spices", "1d6", 10, {"De": 2}, {"Hi": 2, "Ri": 3, "Poor": 3}, {"Ga", "De", "Wa"}),
        Good("textiles", "1d6", 20, {"Ag": 7}, {"Hi": 3, "Na": 2}, {"Ag", "Ni"}),
        Good("uncommon ore", "1d6", 20, {"As": 4}, {"In": 3, "Ni": 1}, {"As", "Ic"}),
        Good("uncommon raw materials", "1d6", 10, {"Ag": 2, "Wa": 1}, {"In": 2, "Ht": 1}, {"Ag", "De", "Wa"}),
        Good("wood", "1d6", 20, {"Ag": 6}, {"Ri": 2, "In": 1}, {"Ag", "Ga"}),
        Good("vehicles", "1d6", 10, {"In": 2, "Ht": 1}, {"Ni": 2, "Hi": 1}, {"In", "Ht"}),
        Good("biochemicals, illegal", "1d6", 5, {"Wa": 2}, {"In": 6}, {"Ag", "Wa"}),
        Good("cybernetics, illegal", "1d6", 1, {"Ht": 1}, {"As": 4, "Ic": 4, "Ri": 8, "amber": 6, "red": 6}, {"Ht"}),
        Good(
            "drugs, illegal",
            "1d6",
            1,
            {"As": 1, "De": 1, "Ga": 1, "Wa": 1},
            {"Ri": 6, "Hi": 6},
            {"As", "De", "Hi", "Wa"},
        ),
        Good("luxuries, illegal", "1d6", 1, {"Ag": 2, "Wa": 1}, {"Ri": 6, "Hi": 4}, {"Ag", "Ga", "Wa"}),
        Good("weapons, illegal", "1d6", 5, {"Ht": 2}, {"Po": 6, "amber": 8, "red": 10}, {"In", "Ht"}),
    ]

    _speculative_trading_modified_price_buy_table = [
        [*range(-3, 25), 1000],
        [3, 2.5, 2, 1.75, 1.5, 1.35, *[i / 100 for i in range(125, 10, -5)]],
    ]

    _speculative_trading_modified_price_sell_table = [
        [*range(-3, 25), 1000],
        [
            *[i / 100 for i in range(10, 50, 10)],
            *[i / 100 for i in range(45, 95, 5)],
            *[i / 100 for i in range(100, 135, 5)],
            *[i / 100 for i in range(140, 170, 10)],
            1.75,
            2,
            2.5,
            3,
            4,
        ],
    ]

    @staticmethod
    def gen_aval_goods(w, is_illegal=False):
        nrolls = w.POP()[1]
        tt = BbwTrade._speculative_trading_table
        rl = [BbwExpr()] * len(tt)

        rmax = len([i for i in tt if ("illegal" in i.name()) is is_illegal])
        offset = len(tt) - rmax if is_illegal else 0
        for i in range(nrolls):
            s = f"1d{rmax}+{offset}"
            idx = d20.roll(s).total - 1
            rl[idx] += tt[idx].roll_tons(w)[0]

        for idx in range(rmax):
            idx += offset
            if len(tt[idx].aval_restr()) == 0 or len(tt[idx].aval_restr().intersection(w.trade_codes())):
                rl[idx] += tt[idx].roll_tons(w)[0]

        return [
            [tt[idx].name(), int(i), str(i).replace(" ", "").replace("`", "")] for idx, i in enumerate(rl) if int(i) > 0
        ]

    @staticmethod
    def _get_mod_st(m, w):
        ans = BbwExpr()
        for k, v in m.items():
            if k in w.trade_codes() or k in w.zone():
                ans = max(ans, BbwExpr(f"{k}", v))

        return ans

    @staticmethod
    def get_deal_st(name, broker, w, roll="3d6"):
        broker = int(broker)

        obj = copy.deepcopy(
            BbwUtils.get_objs(raw_list=BbwTrade._speculative_trading_table, name=name, only_one=True)[0]
        )

        buy_r = BbwExpr()
        buy_r += d20.roll(f"{roll} [base]")

        buy_r += ("broker", broker)
        sell_r = copy.deepcopy(buy_r)

        buy_r += BbwTrade._get_mod_st(obj.buy_mods(), w)
        buy_r -= BbwTrade._get_mod_st(obj.sell_mods(), w)

        buy_multi = BbwUtils.get_modifier(int(buy_r), BbwTrade._speculative_trading_modified_price_buy_table)

        sell_r += BbwTrade._get_mod_st(obj.sell_mods(), w)
        sell_r -= BbwTrade._get_mod_st(obj.buy_mods(), w)

        sell_multi = BbwUtils.get_modifier(int(sell_r), BbwTrade._speculative_trading_modified_price_sell_table)
        return buy_multi, buy_r, sell_multi, sell_r

    @staticmethod
    def _evaluate_good_st(v, w0, w1, max_broker):
        buy_multi, buy_mods, _, _ = BbwTrade.get_deal_st(name=v.name(), broker=max_broker, w=w0, roll=9.5)
        _, _, sell_multi, sell_mods = BbwTrade.get_deal_st(name=v.name(), broker=max_broker, w=w1, roll=9.5)

        _, avg_t_buy, _, max_t_buy = v.roll_tons(w0)
        _, avg_t_sell, _, max_t_sell = v.roll_tons(w1)

        avg_diff = sell_multi - buy_multi
        base_price = BbwItemFactory.make(name=v.name()).value(is_per_obj=True)
        profit_per_ton = base_price * avg_diff

        return [
            v.name().replace(" ", "\n"),
            f"{str(buy_mods).replace(' ', '').replace('`','')}\n{str(sell_mods).replace(' ', '').replace('`','')}",
            base_price,
            avg_diff,
            profit_per_ton,
            f"{avg_t_buy} ({max_t_buy})\n{avg_t_sell} ({max_t_sell})",
        ]

    @staticmethod
    def optimize_st(w0, w1, cs):
        crew = cs.crew()
        max_broker = BbwPerson.max_skill(crew, "broker")[0][1]

        l = [BbwTrade._evaluate_good_st(v, w0, w1, max_broker) for v in BbwTrade._speculative_trading_table]

        h = [
            f"goods ",
            f"buy DMs, \nsell DMs",
            "base price/\nton",
            "profit/\ncr",
            "avg. profit/\nton",
            "tons avg\n(max)",
        ]

        return h, l

    @staticmethod
    def find_passengers(cs, carouse_or_broker_or_streetwise_mod, SOC_mod, kind, w0, w1):
        """
        - carouse_brocker_or_streetwise_mod: carouse or broker or streetwise modifier
        - SOC_mod: SOC modifier
        - n_sectors: distance
        - w0: departure world data (pop, starport, zone)
        - w1: arrival world data (pop, starport, zone)
        """
        carouse_or_broker_or_streetwise_mod, SOC_mod = int(carouse_or_broker_or_streetwise_mod), int(SOC_mod)

        crew = cs.crew()
        max_steward = BbwPerson.max_skill(crew, "steward")[0][1]

        n_sectors = BbwWorld.distance(w0, w1)
        BbwUtils.test_geq("sectors", n_sectors, 1)

        person = BbwPersonFactory.make(name=kind, n_sectors=n_sectors)

        r = BbwExpr()
        r += d20.roll("2d6-8 [avg. ck]")

        if "high" in person.name():
            r += ("base", -4)

        if "low" in person.name():
            r += ("base", 1)

        r += ("streetwise/carouse/broker", carouse_or_broker_or_streetwise_mod)
        r += ("SOC", SOC_mod)
        r += ("max steward", max_steward)

        for w in [w0, w1]:
            r += (f"pop ({w.name()})", BbwUtils.get_modifier(w.POP()[1], BbwTrade._passenger_wp_table))
            r += (f"starpt ({w.name()})", BbwUtils.get_modifier(w.SP()[1], BbwTrade._passenger_starport_table))
            r += (f"zone ({w.name()})", BbwTrade._passenger_zone_dict[w.zone()])

        r += ("dist.", (1 - n_sectors))

        nd = BbwUtils.get_modifier(int(r), BbwTrade._passenger_traffic_table)
        nd = BbwExpr(d20.roll(f"{nd}d6"))

        if int(nd) <= 0:
            return (None, n_sectors, r, nd)

        person.set_count(int(nd))
        return (person, n_sectors, r, nd)

    @staticmethod
    def _freight_traffic_table_roll(brocker_or_streetwise_mod, SOC_mod, kind, w0, w1):
        """
        - brocker_or_streetwise_mod: broker or streetwise modifier
        - SOC_mod: SOC modifier
        - n_sectors: distance in parsec
        - w0: departure world data (pop, starport, TL, zone)
        - w1: arrival world data (pop, starport, TL, zone)
        """
        brocker_or_streetwise_mod, SOC_mod = int(brocker_or_streetwise_mod), int(SOC_mod)

        n_sectors = BbwWorld.distance(w0, w1)
        BbwUtils.test_geq("sectors", n_sectors, 1)

        kind = BbwUtils.get_objs(
            raw_list=["freight, major", "freight, minor", "freight, incidental", "mail"], name=kind, only_one=True
        )[0]

        r = BbwExpr()
        r += d20.roll("2d6-8 [avg. ck]")

        if kind == "freight, major":
            r += ("base", -4)

        if kind == "freight, incidental":
            r += ("base", 2)

        r += ("streetwise/broker", brocker_or_streetwise_mod)
        r += ("SOC", SOC_mod)

        for w in [w0, w1]:
            r += (f"pop ({w.name()})", BbwUtils.get_modifier(w.POP()[1], BbwTrade._freight_wp_table))
            r += (f"starpt ({w.name()})", BbwUtils.get_modifier(w.SP()[1], BbwTrade._freight_starport_table))
            r += (f"zone ({w.name()})", BbwTrade._freight_zone_dict[w.zone()])
            r += (f"TL ({w.name()})", BbwUtils.get_modifier(w.TL()[1], BbwTrade._freight_TL_table))

        r += ("dist.", 1 - n_sectors)

        return n_sectors, r

    @staticmethod
    def find_mail(
        cs,
        brocker_or_streetwise_mod,
        SOC_mod,
        w0,
        w1,
    ):
        """
        - brocker_or_streetwise_mod: broker or streetwise modifier
        - SOC_mod: SOC modifier
        - n_sectors: distance in parsec
        - w0: departure world data (pop, starport, TL, zone)
        - w1: arrival world data (pop, starport, TL, zone)
        """
        crew = [i for i, _ in cs.containers().get_objs(name="crew", type0=BbwPerson).objs()]
        max_naval_or_scout_rank = max(BbwPerson.max_rank(crew, "navy")[0][1], BbwPerson.max_rank(crew, "scout")[0][1])

        max_SOC_mod = BbwUtils.get_modifier(BbwPerson.max_stat(crew, "SOC")[0], BbwPerson._stat_2_mod)

        n_sectors, rft = BbwTrade._freight_traffic_table_roll(brocker_or_streetwise_mod, SOC_mod, "mail", w0, w1)
        r = BbwExpr()
        r += d20.roll("2d6-12 [mail. ck]")
        r += ("freight table", BbwUtils.get_modifier(int(rft), BbwTrade._freight_traffic_table_2_mail_table))
        r += ("max SOC", max_SOC_mod)
        r += ("max navy/scout", max_naval_or_scout_rank)

        for w in [w0, w1]:
            r += (f"TL ({w.name()})", BbwUtils.get_modifier(w.TL()[1], BbwTrade._mail_TL_table))

        if cs.is_armed():
            r += ("armed", 2)

        if int(r) < 0:
            return None, n_sectors, r, 0, rft

        nd = BbwExpr(d20.roll(f"1d6"))
        return BbwItemFactory.make(name="mail", count=int(nd)), n_sectors, r, nd, rft

    @staticmethod
    def find_freight(
        brocker_or_streetwise_mod,
        SOC_mod,
        kind,
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
        n_sectors, r = BbwTrade._freight_traffic_table_roll(brocker_or_streetwise_mod, SOC_mod, kind, w0, w1)
        nd = BbwUtils.get_modifier(int(r), BbwTrade._passenger_traffic_table)
        nd = BbwExpr(d20.roll(f"{nd}d6"))

        return BbwItemFactory.make(name=kind, count=int(nd), n_sectors=n_sectors), n_sectors, r, nd


# w1 = BbwWorld(name="enope", uwp="C411988-7", zone="normal", hex="2205", sector=(-4, 1))
# w0 = BbwWorld(name="boughene", uwp="A8B3531D", zone="normal", hex="1904", sector=(-4, 1))
# print(BbwTrade.gen_aval_goods(w1, is_illegal=False))
# print(w1.__str__(detail_lvl=2))
# exit()


# print(BbwUtils.get_modifier(24, BbwTrade._speculative_trading_modified_price_sell_table))
#
# # print("\n".join([f"{k}: {v}" for k, v in BbwTrade._speculative_mods({"In", "Lt"})]))
# exit()


# # w0.set_trade_code("Ag", 1)
# # w0.set_trade_code("('Ni', None)")
# print(w0.__str__(1))
# print(w1.__str__(1))
#
# print("\n".join([f"{i[0]}, {i[1]}, {i[2]}, {int(i[3])}, {i[4]}, {i[5]}" for i in BbwTrade._speculative_mods(w0, w1, 2)]))
#
# # freight = BbwTrade.find_mail(2, 3, "major", w0, w1)
# # print(freight[0])
# exit()
