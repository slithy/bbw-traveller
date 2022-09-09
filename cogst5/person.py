from cogst5.base import *


class BbwPerson(BbwObj):
    class Role:
        def __init__(self, role, salary, capacity):
            self.role = role
            self.salary = salary
            self.capacity = capacity

    std_roles = {
        "high": Role("high", 0, 1),
        "middle": Role("middle", 0, 1),
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

    def __init__(self, role, salary_ticket, *args, **kwargs):
        kwargs, salary_ticket = self.set_role(role, salary_ticket, **kwargs)

        self.set_salary_ticket(salary_ticket)

        super().__init__(*args, **kwargs)

    def salary_ticket(self):
        return self._salary_ticket

    def role(self):
        return self._role

    def is_crew(self):
        return "crew" in self.role()

    def set_role(self, v, salary_ticket, **kwargs):
        _, v = get_item(v, self.std_roles)
        self._role = str(v.role)
        if salary_ticket is None:
            salary_ticket = v.salary

        if "capacity" in kwargs and kwargs["capacity"] is None:
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

    def _str_table(self, is_compact=True):
        if is_compact:
            return [self.count(), self.name()]
        else:
            return [self.count(), self.name(), self.role(), self.salary_ticket(), self.capacity()]

    def __str__(self, is_compact=True):
        return print_table(self._str_table(is_compact), headers=self._header(is_compact))

    @staticmethod
    def _header(is_compact=True):
        if is_compact:
            return ["count", "name"]
        else:
            return ["count", "name", "role", "salary (<0)/ticket (>=0)", "capacity"]


#
# a = BbwPerson(name="aaa", capacity=1, role="pil", salary_ticket=-1)
# print(a.__str__(False))
#
# print()
#
# exit()
