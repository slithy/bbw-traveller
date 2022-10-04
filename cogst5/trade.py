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

    def __str__(self):
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
            return s

        s = "".join([f"{affix(idx, v, i)}" for idx, (i, v) in enumerate(self._l)])
        if len(self._l) == 1:
            return s

        return s + f" = {int(self)}"


class Good:
    def __init__(self, name, tons, buy_mods, sell_mods):
        self._name = name
        self._tons = tons
        self._buy_mods = buy_mods
        self._sell_mods = sell_mods

    def name(self):
        return self._name

    def tons(self):
        return self._tons

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
        Good("common electronics", "2d6*10", {"In": 2, "Ht": 3, "Ri": 1}, {"Ni": 2, "Lt": 1, "Po": 1}),
        Good("common industrial goods", "2d6*10", {"Na": 2, "In": 5}, {"Ni": 2, "Ag": 2}),
        Good("common manufactured goods", "2d6*10", {"Na": 2, "In": 5}, {"Ni": 3, "Hi": 2}),
        Good("common raw materials", "2d6*20", {"Ag": 3, "Ga": 2}, {"In": 2, "Po": 2}),
        Good(
            "common consumables",
            "2d6*20",
            {"Ag": 3, "Wa": 2, "Ga": 1, "As": -4},
            {"As": 1, "Fl": 1, "Ic": 1, "Hi": 1},
        ),
        Good("common ore", "2d6*20", {"As": 4}, {"In": 3, "Ni": 1}),
        Good("advanced electronics", "1d6*5", {"In": 2, "Ht": 3}, {"Ni": 1, "Ri": 2, "As": 3}),
        Good("advanced machine parts", "1d6*5", {"In": 2, "Ht": 1}, {"Ni": 1, "As": 2}),
        Good("advanced manufactured goods", "1d6*5", {"In": 1}, {"Hi": 1, "Ri": 2}),
        Good("advanced weapons", "1d6*5", {"Ht": 2}, {"Po": 1, "amber": 2, "red": 4}),
        Good("advanced vehicles", "1d6*5", {"Ht": 2}, {"As": 2, "Ri": 2}),
        Good("biochemicals", "1d6*5", {"Ag": 1, "Wa": 2}, {"In": 2}),
        Good("crystals and gems", "1d6*5", {"As": 2, "De": 1, "Ic": 1}, {"In": 3, "Ri": 2}),
        Good("cybernetics", "1d6", {"Ht": 1}, {"As": 1, "Ic": 1, "Ri": 2}),
        Good("live animals", "1d6*10", {"Ag": 2}, {"Ln": 3}),
        Good("luxury consumables", "1d6*10", {"Ag": 2, "Wa": 1}, {"Ri": 2, "Hi": 2}),
        Good("luxury goods", "1d6", {"Hi": 1}, {"Ri": 4}),
        Good("medical supplies", "1d6*5", {"Hi": 2}, {"In": 2, "Po": 1, "Ri": 1}),
        Good("petrochemicals", "1d6*10", {"De": 2}, {"In": 2, "Ag": 1, "Lt": 2}),
        Good("pharmaceuticals", "1d6", {"As": 2, "Hi": 1}, {"Ri": 2, "Lt": 1}),
        Good("polymers", "1d6*10", {"In": 1}, {"Ri": 2, "Ni": 1}),
        Good("precious metals", "1d6", {"As": 3, "De": 1, "Ic": 2}, {"Ri": 3, "In": 2, "Ht": 1}),
        Good("radioactives", "1d6", {"As": 2, "Ln": 2}, {"In": 3, "Ht": 1, "Ni": -2, "Ag": -3}),
        Good("robots", "1d6*5", {"In": 1}, {"Ag": 2, "Ht": 1}),
        Good("spices", "1d6*10", {"De": 2}, {"Hi": 2, "Ri": 3, "Poor": 3}),
        Good("textiles", "1d6*20", {"Ag": 7}, {"Hi": 3, "Na": 2}),
        Good("uncommon ore", "1d6*20", {"As": 4}, {"In": 3, "Ni": 1}),
        Good("uncommon raw materials", "1d6*10", {"Ag": 2, "Wa": 1}, {"In": 2, "Ht": 1}),
        Good("wood", "1d6*20", {"Ag": 6}, {"Ri": 2, "In": 1}),
        Good("vehicles", "1d6*10", {"In": 2, "Ht": 1}, {"Ni": 2, "Hi": 1}),
        Good("biochemicals, illegal", "1d6*5", {"Wa": 2}, {"In": 6}),
        Good("cybernetics, illegal", "1d6", {"Ht": 1}, {"As": 4, "Ic": 4, "Ri": 8, "amber": 6, "red": 6}),
        Good("drugs, illegal", "1d6", {"As": 1, "De": 1, "Ga": 1, "Wa": 1}, {"Ri": 6, "Hi": 6}),
        Good("luxuries, illegal", "1d6", {"Ag": 2, "Wa": 1}, {"Ri": 6, "Hi": 4}),
        Good("weapons, illegal", "1d6*5", {"Ht": 2}, {"Po": 6, "amber": 8, "red": 10}),
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

    def buy_speculative_trading(self, name, count, multi):
        count = int(count)
        BbwUtils.test_g("count", count, 0)
        try:
            multi = int(multi)
            BbwUtils.get_modifier(multi, BbwTrade._speculative_trading_modified_price_buy_table)
        except ValueError:
            multi = int(multi)

        item = BbwItem.factory(name, count)

    @staticmethod
    def optimize_speculative_trading(w0, w1, cs):
        def evaluate_good(v):
            def get_mod(m, w):
                ans = BbwExpr()
                for k, v in m.items():
                    if k in w.trade_codes() or k in w.zone():
                        ans = max(ans, BbwExpr(f"{k}", v))

                return ans

            crew = cs.crew()
            max_broker = BbwPerson.max_skill(crew, "broker")[0][1]

            buy_mods = get_mod(v.buy_mods(), w0) - get_mod(v.sell_mods(), w0)
            buy_multi = BbwUtils.get_modifier(
                max_broker + int(buy_mods) + 9.5, BbwTrade._speculative_trading_modified_price_buy_table
            )
            sell_mods = get_mod(v.sell_mods(), w1) - get_mod(v.buy_mods(), w1)
            sell_multi = BbwUtils.get_modifier(
                max_broker + int(sell_mods) + 9.5, BbwTrade._speculative_trading_modified_price_sell_table
            )

            avg_t, _, max_t = BbwUtils.avg_min_max(v.tons())

            avg_diff = sell_multi - buy_multi
            base_price = BbwItemFactory.make(name=v.name()).value(is_per_obj=True)
            profit_per_ton = base_price * avg_diff

            return [
                v.name().replace(" ", "\n"),
                f"{buy_mods}",
                f"{sell_mods}",
                base_price,
                avg_diff,
                profit_per_ton,
                f"{avg_t} ({max_t})",
            ]

        l = [evaluate_good(v) for v in BbwTrade._speculative_trading_table]

        h = [
            "goods",
            f"buy DMs\n({w0.name()})",
            f"sell DMs\n({w1.name()})",
            "base price/ton",
            "profit/cr",
            "avg. profit/ton",
            "tons avg (max)",
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


# print(BbwUtils.get_modifier(24, BbwTrade._speculative_trading_modified_price_sell_table))
#
# # print("\n".join([f"{k}: {v}" for k, v in BbwTrade._speculative_mods({"In", "Lt"})]))
# exit()


# w0 = BbwWorld(name="beck's world", uwp="D88349D-4", zone="normal", hex="2204", sector=(-4, 1))
# w1 = BbwWorld(name="enope", uwp="C411988-7", zone="normal", hex="2205", sector=(-4, 1))
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
