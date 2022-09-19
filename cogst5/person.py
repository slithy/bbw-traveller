from cogst5.base import *
from cogst5.calendar import *

import bisect


class BbwPerson(BbwObj):
    _soc_2_life_expenses = [
        [2, 4, 5, 6, 7, 8, 10, 12, 14, 15],
        [400, 800, 1000, 1200, 1500, 2000, 2500, 5000, 12000, 20000],
    ]
    _stat_2_mod = [["0", "2", "5", "8", "B", "E", "Z"], [-3, -2, -1, 0, 1, 2, 3]]

    def __init__(self, upp=None, salary_ticket=0.0, reinvest=False, ranks={}, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_salary_ticket(salary_ticket)
        self.set_upp(upp)
        self.set_reinvest(reinvest)
        self.set_ranks(ranks)

    def set_ranks(self, ranks):
        if type(ranks) is str:
            ranks = eval(ranks)
        if type(ranks) is not dict:
            raise InvalidArgument(f"{ranks}: must be a dict!")

        self._ranks = {}
        for k, v in ranks.items():
            self.add_rank(k, v)

    def add_rank(self, k, v):
        k = str(k)
        v = int(v)
        BbwUtils.test_geq("rank value", v, 0)
        self._ranks[k] = v

    def ranks(self):
        return self._ranks

    def salary_ticket(self):
        return self._salary_ticket * self.count()

    def reinvest(self):
        return self._reinvest

    def set_reinvest(self, v):
        self._reinvest = bool(int(v))

    def set_salary_ticket(self, v):
        """v < 0 means salary. Otherwise, ticket"""

        v = float(v)

        self._salary_ticket = v

    def upp(self):
        return self._upp

    def STR(self):
        if self.upp() is None:
            return None

        return self.upp()[0], BbwUtils.get_modifier(self.upp()[0], BbwPerson._stat_2_mod)

    def DEX(self):
        if self.upp() is None:
            return None

        return self.upp()[1], BbwUtils.get_modifier(self.upp()[1], BbwPerson._stat_2_mod)

    def END(self):
        if self.upp() is None:
            return None

        return self.upp()[2], BbwUtils.get_modifier(self.upp()[2], BbwPerson._stat_2_mod)

    def INT(self):
        if self.upp() is None:
            return None

        return self.upp()[3], BbwUtils.get_modifier(self.upp()[3], BbwPerson._stat_2_mod)

    def EDU(self):
        if self.upp() is None:
            return None
        return self.upp()[4], BbwUtils.get_modifier(self.upp()[4], BbwPerson._stat_2_mod)

    def SOC(self):
        if self.upp() is None:
            return None
        return self.upp()[5], BbwUtils.get_modifier(self.upp()[5], BbwPerson._stat_2_mod)

    def PSI(self):
        if self.upp() is None:
            return None

        if len(self.upp()) < 7:
            return None

        return self.upp()[6], BbwUtils.get_modifier(self.upp()[6], BbwPerson._stat_2_mod)

    def set_upp(self, v):
        if v is None:
            self._upp = v
            return

        v = v.replace("-", "")

        BbwUtils.test_hexstr("upp", v, [6, 7])
        self._upp = v

    def life_expenses(self):
        if self.SOC() is None:
            return None

        return self._soc_2_life_expenses[1][bisect.bisect_left(self._soc_2_life_expenses[0], int(self.SOC()[0], 36))]

    def trip_payback(self, t):
        t = int(t)
        BbwUtils.test_geq("trip time", t, 0)

        if self.life_expenses() is None:
            return None
        return round(self.life_expenses() * t / 28)

    @staticmethod
    def max_stat(people, stat):
        ans = "0"
        for i in people:
            v = getattr(i, stat)()
            if v is not None:
                v = v[0]
                ans = max(ans, v)

        return ans, BbwUtils.get_modifier(ans, BbwPerson._stat_2_mod)

    @staticmethod
    def max_rank(people, profession):
        ans = 0
        for i in people:
            if profession in i.ranks():
                v = i.ranks()[profession]
                ans = max(ans, v)

        return ans

    def _str_table(self, is_compact=True):
        if is_compact:
            return [self.count(), self.name()]
        else:
            return [
                self.count(),
                self.name(),
                self.upp(),
                tabulate([[f"{k}:", str(v)] for k, v in sorted(self.ranks().items())], tablefmt="plain"),
                self.salary_ticket(),
                self.capacity(),
                self.reinvest(),
            ]

    def __str__(self, is_compact=True):
        return BbwUtils.print_table(self._str_table(is_compact), headers=self._header(is_compact))

    @staticmethod
    def _header(is_compact=True):
        if is_compact:
            return ["count", "name"]
        else:
            return [
                "count",
                "name",
                "upp",
                "ranks",
                "salary (<0)/ticket (>=0)",
                "capacity",
                "reinvest",
            ]

    _std_tickets = {
        "passenger, high": [
            9000,
            14000,
            21000,
            34000,
            60000,
            210000,
        ],
        "passenger, middle": [6500, 10000, 14000, 23000, 40000, 130000],
        "passenger, basic": [2000, 3000, 5000, 8000, 14000, 55000],
        "passenger, low": [700, 1300, 2200, 3900, 7200, 27000],
    }

    @staticmethod
    def factory(name, n_sectors, count, only_std=False):
        if count == 0:
            return None

        _std_passengers = [
            BbwPerson(name="passenger, high", capacity=1),
            BbwPerson(name="passenger, middle", capacity=1),
            BbwPerson(name="passenger, basic", capacity=0.5),
            BbwPerson(name="passenger, low", capacity=1),
            BbwPerson(name="crew, pilot", capacity=0.5),
            BbwPerson(name="crew, astrogator", capacity=0.5),
            BbwPerson(name="crew, engineer", capacity=0.5),
            BbwPerson(name="crew, steward", capacity=0.5),
            BbwPerson(name="crew, medic", capacity=0.5),
            BbwPerson(name="crew, gunner", capacity=0.5),
            BbwPerson(name="crew, marine", capacity=0.5),
            BbwPerson(name="crew, other", capacity=0.5),
        ]

        n_sectors = int(n_sectors)
        try:
            p = BbwUtils.get_objs(raw_list=_std_passengers, name=name, only_one=True)
        except SelectionException:
            return BbwPerson(name=name, count=count, capacity=0.5) if not only_std else None

        p = copy.deepcopy(p[0])
        p.set_count(count)
        if p.name() in BbwPerson._std_tickets:
            p.set_salary_ticket(BbwPerson._std_tickets[p.name()][n_sectors - 1])
            p.set_name(f"{p.name()} (ns: {n_sectors})")

        return p
