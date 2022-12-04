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

    def __init__(self, upp=None, salary_ticket=None, reinvest=False, skill_rank={}, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_salary_ticket(salary_ticket)
        self.set_upp(upp)
        self.set_reinvest(reinvest)
        self.set_skill_rank(skill_rank)

    def set_containers(self):
        self._containers = BbwContainer("containers")
        self._containers.dist_obj(BbwContainer("backpack"))
        self._containers.dist_obj(BbwContainer("cybernetics"))

    @BbwUtils.set_if_not_present_decor
    def containers(self):
        return self._containers

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
            if v > 4:
                self.set_rank(k, v)
            else:
                self.set_skill(k, v)

    def skill_rank(self):
        return self._skill_rank

    def skill(self, name):
        return self.rank(name=name, default_value=-3)

    def rank(self, name, default_value=0):
        res = [(k, v) for k, v in self.skill_rank().items() if name in k]
        return sorted(res, key=lambda x: x[1]) if len(res) else [(name, default_value)]

    def salary_ticket(self, is_per_obj=False):
        return self._per_obj(self._salary_ticket, is_per_obj)

    def reinvest(self):
        return self._reinvest

    def set_reinvest(self, v):
        self._reinvest = bool(int(v))

    def set_salary_ticket(self, v):
        """v < 0 means salary. Otherwise, ticket"""
        if v is None:
            v = 0

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
    def max_rank(people, rank):
        return BbwPerson.max_skill_rank(people, rank, 0)

    @staticmethod
    def max_skill(people, skill):
        return BbwPerson.max_skill_rank(people, skill, -3)

    @staticmethod
    def max_skill_rank(people, rank, default_value):
        ans = (rank, default_value)
        pans = []
        for i in people:
            if ans[1] < i.rank(rank, default_value)[0][1]:
                ans = i.rank(rank, default_value)[0]
                pans = [i]
            elif ans[1] == i.rank(rank, default_value)[0][1]:
                pans.append(i)

        return ans, pans

    def _str_table(self, detail_lvl: int = 0):
        if detail_lvl == 0:
            return [self.count(), self.name()]
        elif detail_lvl == 1:
            return [
                self.count(),
                self.name(),
                self.upp(),
                self.salary_ticket(),
                self.capacity(),
                self.reinvest(),
            ]
        else:
            return [
                self.count(),
                self.name(),
                self.upp(),
                self.salary_ticket(),
                self.capacity(),
                self.reinvest(),
            ]

    def __str__(self, detail_lvl: int = 0):
        s = BbwUtils.print_table(self._str_table(detail_lvl), headers=self._header(detail_lvl), detail_lvl=detail_lvl)

        if detail_lvl == 0:
            return s

        h = ["stat", "value", "modifier"]
        t = [
            ["STR", BbwUtils.print_code(self.STR()[0]), f"{self.STR()[1]}"],
            ["DEX", BbwUtils.print_code(self.DEX()[0]), f"{self.DEX()[1]}"],
            ["END", BbwUtils.print_code(self.END()[0]), f"{self.END()[1]}"],
            ["INT", BbwUtils.print_code(self.INT()[0]), f"{self.INT()[1]}"],
            ["EDU", BbwUtils.print_code(self.EDU()[0]), f"{self.EDU()[1]}"],
            ["SOC", BbwUtils.print_code(self.SOC()[0]), f"{self.SOC()[1]}"],
        ]
        if self.PSI():
            t.append(["PSI", BbwUtils.print_code(self.PSI()[0]), f"{self.PSI()[1]}"])

        s += BbwUtils.print_table(t, headers=h, detail_lvl=1)
        s += "\n".join([i.__str__(detail_lvl=2) for i, _ in self.containers().get_objs(type0=BbwContainer).objs()])

        if detail_lvl == 1:
            return s

        h = ["skill/rank", "level"]
        t = [[k, str(v)] for k, v in sorted(self.skill_rank().items())]

        s += BbwUtils.print_table(t, headers=h, detail_lvl=1)

        return s

    @staticmethod
    def _header(detail_lvl=0):
        if detail_lvl == 0:
            return ["count", "name"]
        elif detail_lvl == 1:
            return [
                "count",
                "name",
                "upp",
                "salary (<0)/ticket (>=0)",
                "capacity",
                "reinvest",
            ]
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


class BbwSupplier(BbwPerson):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_supply()

    def is_illegal(self):
        return "illegal" in self.name()

    def set_supply(self, bbwtrade=None, w=None, t=None):
        self.set_t(t)
        self._supply = []
        if bbwtrade is None or w is None or self.t() is None:
            return

        self._supply = bbwtrade.gen_aval_goods(w, is_illegal=self.is_illegal())

    def t(self):
        if not hasattr(self, "_t"):
            self.set_t()

        return self._t

    def set_t(self, t=None):
        if t is None:
            self._t = None
            return
        self._t = BbwCalendar(t)

    def supply(self):
        if not hasattr(self, "_supply"):
            self.set_supply()

        return self._supply

    def _str_table(self, detail_lvl=0):
        # l = sorted(self.supply(), key=lambda x: x[0])
        # s = ["\n".join([str(i[q]) for i in l]) for q in range(3)]
        return [self.name(), self.t()]

    def __str__(self, detail_lvl=0):
        return BbwUtils.print_table(
            self._str_table(detail_lvl), headers=self._header(detail_lvl), detail_lvl=detail_lvl
        )

    @staticmethod
    def _header(detail_lvl=0):
        return ["name", "supply date"]

    def print_supply(self):
        h = ["goods", "tons", "calc"]
        t = self.supply()
        return BbwUtils.print_table(t, h, detail_lvl=1)


class BbwPersonFactory:
    _tickets = {
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

    _lib = [
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

    @staticmethod
    def make(name, n_sectors=1, count=None, salary_ticket=None, capacity=None):
        if count == 0:
            return None

        item = copy.deepcopy(BbwUtils.get_objs(raw_list=BbwPersonFactory._lib, name=name, only_one=True)[0])

        if item.name() in BbwPersonFactory._tickets.keys():
            item.set_salary_ticket(BbwPersonFactory._tickets[item.name()][int(n_sectors) - 1])
            item.set_name(f"{item.name()} (ns: {n_sectors})")

        if salary_ticket is not None:
            item.set_salary_ticket(salary_ticket)
        if capacity is not None:
            item.set_capacity(capacity)
            item.set_size(item.capacity())
        if count is not None:
            item.set_count(count)

        return item


# a = BbwWorld(name="feri", uwp="B384879-B", zone="normal", hex="1904", sector=(-4, 1))
# b = BbwSupplier(name="John, illegal")
# c = BbwSupplier(name="John, illegal")
# a.suppliers().dist_obj(b)
# a.suppliers().dist_obj(c)
#
# a.set_supply(123124)
# print(a.__str__(1))
# exit()

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
