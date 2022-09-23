from cogst5.person import *
from cogst5.item import *
from cogst5.world import *


class BbwExpr:
    def __init__(self, l=[]):
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

    def __int__(self):
        print(self._l)
        return sum(i for _, i in self._l)

    def __str__(self):
        def affix(idx, v, i):
            print(type(i))
            s = " " if idx else ""
            if idx and v >= 0:
                s += "+ "
            if type(i) is d20.dice.RollResult:
                s += i.__str__()
            else:
                s += f"`{v}` [" + i + "]"
            return s

        s = "".join([f"{affix(idx, v, i)}" for idx, (i, v) in enumerate(self._l)])
        if len(self._l) == 1 and type(self._l[0][0]) is d20.dice.RollResult:
            return s

        return s + f" = `{int(self)}`"


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

        crew = [i for i, _ in cs.containers().get_objs(name="crew", type0=BbwPerson).objs()]
        max_steward = BbwPerson.max_skill(crew, "steward")[0][1]

        n_sectors = BbwWorld.distance(w0, w1)
        BbwUtils.test_geq("sectors", n_sectors, 1)

        kind = BbwUtils.get_objs(raw_list=BbwPerson._std_tickets.keys(), name=kind, only_one=True)[0]

        r = BbwExpr()
        r += d20.roll("2d6-8 [avg. ck]")

        if "high" in kind:
            r += ("base", -4)

        if "low" in kind:
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

        return (BbwPerson.factory(name=kind, n_sectors=n_sectors, count=int(nd), only_std=True), n_sectors, r, nd)

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

        kind = BbwUtils.get_objs(raw_list=BbwItem._freight_lot_ton_multi_dict.keys(), name=kind, only_one=True)[0]

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
        return BbwItem.factory(name="mail", count=int(nd), only_std=True), n_sectors, r, nd, rft

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

        return BbwItem.factory(name=kind, count=int(nd), only_std=True), n_sectors, r, nd


# w0 = BbwWorld(name="feri", uwp="B384879-B", zone="normal", hex="2005")
# w1 = BbwWorld(name="boughene", uwp="A788899-C", zone="normal", hex="1904")
# freight = BbwTrade.find_mail(2, 3, "major", w0, w1)
# print(freight[0])
# exit()
