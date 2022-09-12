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

    std_roles = {
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
    soc_2_life_expenses = [
        [2, 4, 5, 6, 7, 8, 10, 12, 14, 15],
        [400, 800, 1000, 1200, 1500, 2000, 2500, 5000, 12000, 20000],
    ]

    def __init__(self, role, upp=None, salary_ticket=None, reinvest=False, *args, **kwargs):
        kwargs, salary_ticket = self.set_role(role, salary_ticket, **kwargs)

        self.set_salary_ticket(salary_ticket)
        self.set_upp(upp)
        self.set_reinvest(reinvest)

        super().__init__(*args, **kwargs)

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
        return self.std_roles[self.role()].luggage * self.count()

    def set_role(self, v, salary_ticket, **kwargs):
        _, v = get_item(v, self.std_roles)
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

    def set_upp(self, v):
        if v is None:
            self._upp = v
            return

        test_hexstr("upp", v, 6)
        self._upp = v

    def life_expenses(self):
        if self.upp() is None:
            return None

        idx = int(self._upp[5], 16)
        return self.soc_2_life_expenses[1][bisect.bisect_left(self.soc_2_life_expenses[0], idx)]

    def trip_payback(self, t):
        t = int(t)
        test_geq("trip time", t, 0)

        if self.life_expenses() is None:
            return None
        return round(self.life_expenses() * t / 28)

    def _str_table(self, is_compact=True):
        if is_compact:
            return [self.count(), self.name()]
        else:
            return [
                self.count(),
                self.name(),
                self.role(),
                self.upp(),
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
            return ["count", "name", "role", "upp", "salary (<0)/ticket (>=0)", "capacity", "reinvest", "luggage"]


# a = BbwPerson(name="aaa", capacity=None, role="high", salary_ticket=0, upp=None)
# print(a.__str__(False))
# #
# print(a.capacity())
#
# exit()
