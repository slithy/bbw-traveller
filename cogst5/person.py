from cogst5.base import *
from cogst5.calendar import *

import bisect


class BbwPerson(BbwObj):
    _soc_2_life_expenses = [
        [2, 4, 5, 6, 7, 8, 10, 12, 14, 15],
        [400, 800, 1000, 1200, 1500, 2000, 2500, 5000, 12000, 20000],
    ]
    _stat_2_mod = [["0", "2", "5", "8", "B", "E", "Z"], [-3, -2, -1, 0, 1, 2, 3]]
    _general_skills = [
        "animals",
        "athletics",
        "art",
        "drive",
        "electronics",
        "engineer",
        "flyer",
        "gunner",
        "gun combat",
        "heavy weapons",
        "language",
        "melee",
        "pilot",
        "profession",
        "science",
        "seafarer",
        "tactics",
    ]

    def __init__(self, upp=None, salary_ticket=0.0, reinvest=False, skill_rank={}, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_salary_ticket(salary_ticket)
        self.set_upp(upp)
        self.set_reinvest(reinvest)
        self.set_skill_rank(skill_rank)

    def set_skill(self, name, value=None):
        if value is None:
            name, value = eval(name)
        if value is None:
            del self._skill_rank[name]
            return
        if type(value) is str:
            value = int(value, 36)

        BbwUtils.test_geq("skill", value, 0)
        BbwUtils.test_leq("skill", value, 4)
        self._skill_rank[name] = value

        for i in BbwPerson._general_skills:
            if i in name:
                self._skill_rank[i] = 0

    def set_rank(self, name, value=None):
        if value is None:
            name, value = eval(name)
        if value is None:
            del self._skill_rank[name]
            return
        if type(value) is str:
            value = int(value, 36)

        BbwUtils.test_geq("skill", value, 0)
        BbwUtils.test_leq("skill", value, 6)
        self._skill_rank[name] = value

    def set_skill_rank(self, skill_rank):
        if type(skill_rank) is str:
            skill_rank = eval(skill_rank)
        if type(skill_rank) is not dict:
            raise InvalidArgument(f"{skill_rank}: must be a dict!")

        self._skill_rank = {}
        for k, v in skill_rank.items():
            self.set_rank(k, v)

    def skill_rank(self):
        return self._skill_rank

    def skill(self, name):
        return self.rank(name=name, default_value=-3)

    def rank(self, name, default_value=0):
        res = BbwUtils.get_objs(raw_list=self.skill_rank().items(), name=name)
        return sorted(res, key=lambda x: len(x))[0][1] if len(res) else default_value

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
        pans = []
        for i in people:
            val = getattr(i, stat)()
            if val is None:
                continue
            val = val[0]
            if ans < val:
                ans = val
                pans = [i]
            elif ans == val:
                pans.append(i)

        return ans, pans

    @staticmethod
    def max_skill(people, skill):
        ans = -3
        pans = []
        for i in people:
            if ans < i.skill(skill):
                ans = i.skill(skill)
                pans = [i]
            elif ans == i.skill(skill):
                pans.append(i)

        return ans, pans

    @staticmethod
    def max_rank(people, rank):
        ans = 0
        pans = []
        for i in people:
            if ans < i.rank(rank):
                ans = i.rank(rank)
                pans = [i]
            elif ans == i.rank(rank):
                pans.append(i)

        return ans, pans

    def _str_table(self, is_compact=True):
        if is_compact:
            return [self.count(), self.name()]
        else:
            return [
                self.count(),
                self.name(),
                self.upp(),
                tabulate([[f"{k}:", str(v)] for k, v in sorted(self.skill_rank().items())], tablefmt="plain"),
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
                "skills/ranks",
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
    def factory(name, n_sectors, count, capacity=0.5, only_std=False):
        if count == 0:
            return None

        _std_passengers = [
            BbwPerson(name="passenger, high", capacity=1),
            BbwPerson(name="passenger, middle", capacity=1),
            BbwPerson(name="passenger, basic", capacity=0.5),
            BbwPerson(name="passenger, low", capacity=1),
            BbwPerson(name="crew, pilot", capacity=0.5, salary_ticket=-6000),
            BbwPerson(name="crew, astrogator", capacity=0.5, salary_ticket=-5000),
            BbwPerson(name="crew, engineer", capacity=0.5, salary_ticket=-4000),
            BbwPerson(name="crew, steward", capacity=0.5, salary_ticket=-2000),
            BbwPerson(name="crew, medic", capacity=0.5, salary_ticket=-3000),
            BbwPerson(name="crew, gunner", capacity=0.5, salary_ticket=-1000),
            BbwPerson(name="crew, marine", capacity=0.5, salary_ticket=-1000),
            BbwPerson(name="crew, other", capacity=0.5, salary_ticket=-1000),
        ]

        n_sectors = int(n_sectors)
        try:
            p = BbwUtils.get_objs(raw_list=_std_passengers, name=name, only_one=True)
        except SelectionException:
            return BbwPerson(name=name, count=count, capacity=capacity) if not only_std else None

        p = copy.deepcopy(p[0])
        p.set_count(count)
        if p.name() in BbwPerson._std_tickets:
            p.set_salary_ticket(BbwPerson._std_tickets[p.name()][n_sectors - 1])
            p.set_name(f"{p.name()} (ns: {n_sectors})")

        return p


# new_person = BbwPerson(
#     name="aaa, crew, other",
#     count=1,
#     salary_ticket=-1,
#     capacity=1,
#     reinvest=False,
#     upp="337CCF",
#     skill_rank={'steward':1},
# )
# new_person.set_skill("pilot, spacecraft", 4)
#
# new_person.set_rank("noble, admin", 6)
#
# print(new_person.__str__(False))
# print(new_person.skill("bau"))
# print(new_person.rank("noble"))
# exit()
