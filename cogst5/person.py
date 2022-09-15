from cogst5.base import *
from cogst5.calendar import *

import bisect


class BbwPerson(BbwObj):
    class Role:
        def __init__(self, role, salary, capacity, luggage=0):
            self.role = role
            self.salary = salary
            self.capacity = capacity
            self.luggage = luggage

    _std_roles = {
        "high": Role("high", 0, 1, 0.1),
        "middle": Role("middle", 0, 1, 0.01),
        "basic": Role("basic", 0, 0.5),
        "low": Role("low", 0, 1),
        "crew: working": Role("crew: working", 0, 0.5),
        "crew: pilot": Role("crew: pilot", -6000, 0.5),
        "crew: astrogator": Role("crew: astrogator", -5000, 0.5),
        "crew: engineer": Role("crew: engineer", -4000, 0.5),
        "crew: steward": Role("crew: steward", -2000, 0.5),
        "crew: medic": Role("crew: medic", -3000, 0.5),
        "crew: gunner": Role("crew: gunner", -1000, 0.5),
        "crew: marine": Role("crew: marine", -1000, 0.5),
        "crew: other": Role("crew: other", -2000, 0.5),
    }
    _soc_2_life_expenses = [
        [2, 4, 5, 6, 7, 8, 10, 12, 14, 15],
        [400, 800, 1000, 1200, 1500, 2000, 2500, 5000, 12000, 20000],
    ]
    _stat_2_mod = [["0", "2", "5", "8", "B", "E", "Z"], [-3, -2, -1, 0, 1, 2, 3]]

    def __init__(self, role, upp=None, salary_ticket=None, reinvest=False, ranks={}, *args, **kwargs):
        kwargs, salary_ticket = self.set_role(role, salary_ticket, **kwargs)

        self.set_salary_ticket(salary_ticket)
        self.set_upp(upp)
        self.set_reinvest(reinvest)
        self.set_ranks(ranks)

        super().__init__(*args, **kwargs)

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
        test_geq("rank value", v, 0)
        self._ranks[k] = v

    def ranks(self):
        return self._ranks

    def salary_ticket(self):
        return self._salary_ticket * self.count()

    def reinvest(self):
        return self._reinvest

    def set_reinvest(self, v):
        self._reinvest = bool(int(v))

    def role(self):
        return self._role

    def is_crew(self):
        return "crew" in self.role()

    def luggage(self):
        return self._std_roles[self.role()].luggage * self.count()

    def set_role(self, v, salary_ticket, **kwargs):
        _, v = get_item(v, self._std_roles)
        self._role = str(v.role)
        if salary_ticket is None:
            salary_ticket = v.salary

        if "capacity" not in kwargs or kwargs["capacity"] is None:
            kwargs["capacity"] = v.capacity

        return kwargs, salary_ticket

    def set_salary_ticket(self, v):
        """v < 0 means salary. Otherwise, ticket"""

        v = float(v)

        if self.is_crew():
            test_leq("salary/ticket", v, 0.0)
        else:
            test_geq("salary/ticket", v, 0.0)

        self._salary_ticket = v

    def upp(self):
        return self._upp

    def STR(self):
        if self.upp() is None:
            return None

        return self.upp()[0], get_modifier(self.upp()[0], BbwPerson._stat_2_mod)

    def DEX(self):
        if self.upp() is None:
            return None

        return self.upp()[1], get_modifier(self.upp()[1], BbwPerson._stat_2_mod)

    def END(self):
        if self.upp() is None:
            return None

        return self.upp()[2], get_modifier(self.upp()[2], BbwPerson._stat_2_mod)

    def INT(self):
        if self.upp() is None:
            return None

        return self.upp()[3], get_modifier(self.upp()[3], BbwPerson._stat_2_mod)

    def EDU(self):
        if self.upp() is None:
            return None
        return self.upp()[4], get_modifier(self.upp()[4], BbwPerson._stat_2_mod)

    def SOC(self):
        if self.upp() is None:
            return None
        return self.upp()[5], get_modifier(self.upp()[5], BbwPerson._stat_2_mod)

    def PSI(self):
        if self.upp() is None:
            return None

        if len(self.upp()) < 7:
            return None

        return self.upp()[6], get_modifier(self.upp()[6], BbwPerson._stat_2_mod)

    def set_upp(self, v):
        if v is None:
            self._upp = v
            return

        v = v.replace("-", "")

        test_hexstr("upp", v, [6, 7])
        self._upp = v

    def life_expenses(self):
        if self.SOC() is None:
            return None

        return self._soc_2_life_expenses[1][bisect.bisect_left(self._soc_2_life_expenses[0], int(self.SOC()[0], 36))]

    def trip_payback(self, t):
        t = int(t)
        test_geq("trip time", t, 0)

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

        return ans, get_modifier(ans, BbwPerson._stat_2_mod)

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
                self.role(),
                self.upp(),
                self.ranks(),
                self.salary_ticket(),
                self.capacity(),
                self.reinvest(),
                self.luggage(),
            ]

    def __str__(self, is_compact=True):
        return print_table(self._str_table(is_compact), headers=self._header(is_compact))

    @staticmethod
    def _header(is_compact=True):
        if is_compact:
            return ["count", "name"]
        else:
            return [
                "count",
                "name",
                "role",
                "upp",
                "ranks",
                "salary (<0)/ticket (>=0)",
                "capacity",
                "reinvest",
                "luggage",
            ]
