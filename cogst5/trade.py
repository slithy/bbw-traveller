from cogst5.person import *
from cogst5.item import *
from cogst5.world import *


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
        max_steward, _ = BbwPerson.max_skill(crew, "steward")

        n_sectors = BbwWorld.distance(w0, w1)

        kind = BbwUtils.get_objs(raw_list=BbwPerson._std_tickets.keys(), name=kind, only_one=True)[0]

        r = d20.roll("2d6").total + carouse_or_broker_or_streetwise_mod + SOC_mod + max_steward - 8

        if "high" in kind:
            r -= 4

        if "low" in kind:
            r += 1

        for w in [w0, w1]:
            r += BbwUtils.get_modifier(w.POP()[1], BbwTrade._passenger_wp_table)
            r += BbwUtils.get_modifier(w.SP()[1], BbwTrade._passenger_starport_table)
            r += BbwTrade._passenger_zone_dict[w.zone()]

        r -= n_sectors - 1

        nd = BbwUtils.get_modifier(r, BbwTrade._passenger_traffic_table)

        return (
            BbwPerson.factory(name=kind, n_sectors=n_sectors, count=d20.roll(f"{nd}d6").total, only_std=True),
            n_sectors,
        )

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

        kind = BbwUtils.get_objs(raw_list=BbwItem._freight_lot_ton_multi_dict.keys(), name=kind, only_one=True)[0]

        r = d20.roll("2d6").total + brocker_or_streetwise_mod + SOC_mod - 8

        if kind == "freight, major":
            r -= 4

        if kind == "freight, incidental":
            r += 2

        for w in [w0, w1]:
            r += BbwUtils.get_modifier(w.POP()[1], BbwTrade._freight_wp_table)
            r += BbwUtils.get_modifier(w.SP()[1], BbwTrade._freight_starport_table)
            r += BbwUtils.get_modifier(w.TL()[1], BbwTrade._freight_TL_table)
            r += BbwTrade._freight_zone_dict[w.zone()]

        r -= n_sectors - 1

        return r, BbwUtils.get_modifier(r, BbwTrade._freight_traffic_table), n_sectors

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
        max_naval_or_scout_rank = max(BbwPerson.max_rank(crew, "navy")[0], BbwPerson.max_rank(crew, "scout")[0])

        max_SOC_mod = BbwUtils.get_modifier(BbwPerson.max_stat(crew, "SOC")[0], BbwPerson._stat_2_mod)

        nd, _, n_sectors = BbwTrade._freight_traffic_table_roll(brocker_or_streetwise_mod, SOC_mod, "mail", w0, w1)
        r = (
            BbwUtils.get_modifier(nd, BbwTrade._freight_traffic_table_2_mail_table)
            + max_naval_or_scout_rank
            + max_SOC_mod
            + d20.roll(f"2d6").total
        )
        for w in [w0, w1]:
            r += BbwUtils.get_modifier(w.TL()[1], BbwTrade._mail_TL_table)

        if cs.is_armed():
            r += 2

        if r < 12:
            return None, n_sectors

        n_canisters = d20.roll("1d6").total
        return BbwItem.factory(name="mail", count=n_canisters, only_std=True), n_sectors

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
        n_sectors = BbwWorld.distance(w0, w1)

        _, nd, n_sectors = BbwTrade._freight_traffic_table_roll(brocker_or_streetwise_mod, SOC_mod, kind, w0, w1)

        print(nd)

        return BbwItem.factory(name=kind, count=d20.roll(f"{nd}d6").total, only_std=True), n_sectors


# w0 = BbwWorld(name="feri", uwp="B384879-B", zone="normal", hex="2005")
# w1 = BbwWorld(name="boughene", uwp="A788899-C", zone="normal", hex="1904")
# freight = BbwTrade.find_mail(2, 3, "major", w0, w1)
# print(freight[0])
# exit()
