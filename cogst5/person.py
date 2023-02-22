from cogst5.base import *
from cogst5.calendar import *
from cogst5.expr import *

import bisect


@BbwUtils.for_all_methods(BbwUtils.type_sanitizer_decor)
class BbwSkillSpeciality:
    def __init__(self, info: str, diff: int, stats: list, time: tuple = None):
        self._diff = diff
        self._time = time
        self._stats = stats
        self._info = info


@BbwUtils.for_all_methods(BbwUtils.type_sanitizer_decor)
class BbwSkill:
    @staticmethod
    def _get_skill(raw_list, name):
        res = BbwUtils.get_objs(raw_list=raw_list, name=name)

        if len(res) > 1:
            print(res)
            raise SelectionException(f"object `{name}` too generic! Options: `{res}`")
        if len(res) == 1:
            return res[0]
        q = name.split(",")
        if len(q) > 1:
            return BbwSkill._get_skill(raw_list=raw_list, name=q[0].strip())

        return None

    def __init__(self, name: str, specialities: list):
        self._name = name
        self._specialities = specialities

    def name(self):
        return self._name

    def fallback_skill(self):
        l = self._name.split(",")
        return l[0].strip() if len(l) == 2 else None

    def base_roll(self, skill_name, skill, stat_name, stat, roll=None, diff=8):
        r = BbwExpr()
        r += (skill_name, skill)
        r += (stat_name, stat)

        r += ("diff", -diff)
        if roll:
            r += roll

        return r

    def roll(self, person, skill_name, skill, chosen_stat: str = None, roll: str = "2d6"):
        if roll:
            roll = d20.roll(f"{roll} [roll]")

        if chosen_stat:
            stat_list = [i for i in dir(person) if i.isupper() and len(i) == 3]
            chosen_stat = BbwUtils.get_objs(raw_list=stat_list, name=chosen_stat, only_one=True)[0]

            stat = getattr(person, chosen_stat)()[1]

            r = self.base_roll(skill_name, skill, chosen_stat, stat, roll)

            return f"**roll**: {r}\n"

        s = []
        for spec in self._specialities:
            v = [getattr(person, i)()[1] for i in spec._stats]
            stat = max(v)
            chosen_stat = "/".join([f"{s}({vi})" for s, vi in zip(spec._stats, v)])

            r = self.base_roll(skill_name, skill, chosen_stat, stat, roll, spec._diff)

            if spec._time:
                t = BbwExpr()
                t += d20.roll(spec._time[0])
                t = f"**T**: {t} {spec._time[1]}"
            else:
                t = ""

            l = []
            if spec._info:
                l.append(spec._info)
            if t:
                l.append(t)
            l.append(f"** roll **: {r}")

            s.append("\n".join(l))

        return f"\n{BbwUtils._msg_divisor}".join(s)


@BbwUtils.for_all_methods(BbwUtils.type_sanitizer_decor)
class BbwPerson(BbwObj):
    _soc_2_life_expenses = [
        [2, 4, 5, 6, 7, 8, 10, 12, 14, 100],
        [400, 800, 1000, 1200, 1500, 2000, 2500, 5000, 12000, 20000],
    ]
    _soc_2_capacity = [[11, 100], [2, 4]]
    _stat_2_mod = [["0", "2", "5", "8", "B", "E", "Z"], [-3, -2, -1, 0, 1, 2, 3]]

    _skills = [
        BbwSkill(
            "admin",
            [
                BbwSkillSpeciality("avoiding close examination of papers", 8, ["SOC", "EDU"], ("1d6*10", "sec")),
                BbwSkillSpeciality("dealing with police harassment", 10, ["SOC", "EDU"], ("1d6*10", "min")),
            ],
        ),
        BbwSkill(
            "advocate",
            [
                BbwSkillSpeciality("arguing in court", 8, ["SOC", "EDU"], ("1d6", "days")),
                BbwSkillSpeciality("debating an argument", 8, ["INT"], ("1d6*10", "min")),
            ],
        ),
        BbwSkill(
            "animals",
            [
                BbwSkillSpeciality("", 8, ["DEX", "EDU", "INT"], None),
            ],
        ),
        BbwSkill(
            "animals, handling",
            [
                BbwSkillSpeciality("riding a horse into battle", 10, ["DEX"], ("1d6", "sec")),
            ],
        ),
        BbwSkill(
            "animals, veterinary",
            [
                BbwSkillSpeciality("first aid", 8, ["EDU"], ("1d6", "rounds")),
                BbwSkillSpeciality("treat poison or disease", 8, ["EDU"], ("1d6", "hours")),
                BbwSkillSpeciality("long-term care", 8, ["EDU"], ("1", "day")),
            ],
        ),
        BbwSkill(
            "animals, training",
            [
                BbwSkillSpeciality("taming a strange alien creature", 14, ["INT"], ("1d6", "days")),
            ],
        ),
        BbwSkill(
            "art",
            [
                BbwSkillSpeciality("", 8, ["DEX", "EDU", "INT"], None),
            ],
        ),
        BbwSkill(
            "art, performer",
            [
                BbwSkillSpeciality("performing a play", 8, ["EDU"], ("1d6", "hours")),
                BbwSkillSpeciality(
                    "convincing a person you are actually someone else (vs recon/INT)", 8, ["INT"], None
                ),
            ],
        ),
        BbwSkill(
            "art, holography",
            [
                BbwSkillSpeciality(
                    "surreptitiously switching on your recorder while in a secret meeting", 14, ["DEX"], ("1d6", "sec")
                ),
            ],
        ),
        BbwSkill(
            "art, instrument",
            [
                BbwSkillSpeciality("playing a concerto", 10, ["EDU"], ("1d6*10", "min")),
            ],
        ),
        BbwSkill(
            "art, visual media",
            [
                BbwSkillSpeciality("making a statue of someone", 10, ["INT"], ("1d6", "days")),
            ],
        ),
        BbwSkill(
            "art, write",
            [
                BbwSkillSpeciality(
                    "rousing the people of a planet by exposing their government's corruption",
                    10,
                    ["INT", "EDU"],
                    ("1d6", "hours"),
                ),
                BbwSkillSpeciality("writing an update of traveller", 14, ["INT"], ("1d6", "months")),
            ],
        ),
        BbwSkill(
            "astrogation",
            [
                BbwSkillSpeciality(
                    "plotting course to a target world using a gas giant for a gravity slingshot",
                    10,
                    ["EDU"],
                    ("1d6*10", "min"),
                ),
                BbwSkillSpeciality("plotting a standard jump (-DM jump sectors)", 4, ["EDU"], ("1d6*10", "min")),
            ],
        ),
        BbwSkill(
            "athletics",
            [
                BbwSkillSpeciality("", 8, ["DEX", "STR", "END"], None),
            ],
        ),
        BbwSkill(
            "athletics, dexterity",
            [
                BbwSkillSpeciality(
                    "climbing",
                    8,
                    [
                        "DEX",
                    ],
                    ("1d6*10", "sec"),
                ),
                BbwSkillSpeciality(
                    "sprinting (covers 24 + effect meters every check)",
                    8,
                    [
                        "DEX",
                    ],
                    ("1d6", "sec"),
                ),
                BbwSkillSpeciality(
                    "high jumping (effect/2 meters up)",
                    8,
                    [
                        "DEX",
                    ],
                    ("1d6", "sec"),
                ),
                BbwSkillSpeciality(
                    "long jumping (effect meters long with running start)",
                    8,
                    [
                        "DEX",
                    ],
                    ("1d6", "sec"),
                ),
                BbwSkillSpeciality(
                    "righting yourself when artificial gravity suddenly fails on board a ship",
                    8,
                    [
                        "DEX",
                    ],
                    ("1d6", "sec"),
                ),
            ],
        ),
        BbwSkill(
            "athletics, endurance",
            [
                BbwSkillSpeciality(
                    "long-distance running/swimming",
                    8,
                    [
                        "END",
                    ],
                    ("1d6*10", "min"),
                ),
            ],
        ),
        BbwSkill(
            "athletics, strength",
            [
                BbwSkillSpeciality(
                    "arm-wrestling (vs athletics, strength/STR)",
                    8,
                    [
                        "END",
                    ],
                    ("1d6", "min"),
                ),
                BbwSkillSpeciality(
                    "feats of strength",
                    8,
                    [
                        "END",
                    ],
                    ("1d6*10", "sec"),
                ),
                BbwSkillSpeciality(
                    "performing a complicated task in a high gravity environment",
                    10,
                    [
                        "END",
                    ],
                    ("1d6", "sec"),
                ),
            ],
        ),
        BbwSkill(
            "broker",
            [
                BbwSkillSpeciality(
                    "negotiating a deal",
                    8,
                    [
                        "INT",
                    ],
                    ("1d6", "hours"),
                ),
                BbwSkillSpeciality(
                    "finding a buyer",
                    8,
                    [
                        "SOC",
                    ],
                    ("1d6", "hours"),
                ),
            ],
        ),
        BbwSkill(
            "carouse",
            [
                BbwSkillSpeciality(
                    "drinking someone under the table (vs carouse/END)",
                    8,
                    [
                        "END",
                    ],
                    ("1d6", "hours"),
                ),
                BbwSkillSpeciality(
                    "gathering rumors at a party",
                    8,
                    [
                        "SOC",
                    ],
                    ("1d6", "hours"),
                ),
            ],
        ),
        BbwSkill(
            "deception",
            [
                BbwSkillSpeciality(
                    "convincing a guard to let you pass without ID (possible vs recon/DEX)",
                    12,
                    [
                        "INT",
                    ],
                    ("1d6", "min"),
                ),
                BbwSkillSpeciality(
                    "palming a credit chit",
                    8,
                    [
                        "DEX",
                    ],
                    ("1d6", "sec"),
                ),
                BbwSkillSpeciality(
                    "disguising yourself as a wealthy nobel to fool a client (possible vs recon/DEX)",
                    10,
                    ["INT", "SOC"],
                    ("1d6*10", "min"),
                ),
            ],
        ),
        BbwSkill(
            "diplomat",
            [
                BbwSkillSpeciality(
                    "greeting the emperor properly",
                    10,
                    [
                        "SOC",
                    ],
                    ("1d6", "min"),
                ),
                BbwSkillSpeciality(
                    "negotiating a peace treaty",
                    8,
                    [
                        "EDU",
                    ],
                    ("1d6", "days"),
                ),
                BbwSkillSpeciality(
                    "transmitting a formal surrender",
                    8,
                    [
                        "INT",
                    ],
                    ("1d6*10", "sec"),
                ),
            ],
        ),
        BbwSkill(
            "drive",
            [
                BbwSkillSpeciality("", 8, ["INT", "DEX"], None),
            ],
        ),
        BbwSkill(
            "drive, hovercraft",
            [
                BbwSkillSpeciality("maneuvering a hovercraft through a tight canal", 10, ["DEX"], ("1d6", "min")),
            ],
        ),
        BbwSkill(
            "drive, mole",
            [
                BbwSkillSpeciality("surfacing in the right place", 8, ["INT"], ("1d6*10", "min")),
                BbwSkillSpeciality(
                    "precisely controlling a dig to expose a vein of minerals", 10, ["DEX"], ("1d6*10", "min")
                ),
            ],
        ),
        BbwSkill(
            "drive, track",
            [
                BbwSkillSpeciality("maneuvering/smashing through a forest", 10, ["DEX"], ("1d6", "min")),
                BbwSkillSpeciality("driving a tank into a cargo bay", 8, ["DEX"], ("1d6*10", "sec")),
            ],
        ),
        BbwSkill(
            "drive, walker",
            [
                BbwSkillSpeciality("negotiating rough terrain", 10, ["DEX"], ("1d6", "min")),
            ],
        ),
        BbwSkill(
            "drive, wheel",
            [
                BbwSkillSpeciality(
                    "driving a groundcar in a short race (vs drive, wheel/DEX)", 8, ["DEX"], ("1d6", "min")
                ),
                BbwSkillSpeciality(
                    "driving a groundcar in a long race (vs drive, wheel/END)", 8, ["END"], ("1d6", "hours")
                ),
                BbwSkillSpeciality("avoiding an unexpected obstacle on the road", 8, ["DEX"], ("1d6", "sec")),
            ],
        ),
        BbwSkill(
            "electronics",
            [
                BbwSkillSpeciality("", 8, ["EDU", "INT", "DEX"], None),
            ],
        ),
        BbwSkill(
            "electronics, comms",
            [
                BbwSkillSpeciality("requesting landing privileges at a starport", 6, ["EDU"], ("1d6", "min")),
                BbwSkillSpeciality(
                    "accessing publicly available but obscure data over comms", 8, ["EDU"], ("1d6*10", "min")
                ),
                BbwSkillSpeciality(
                    "bouncing a signal off orbiting satellite to hide your transmitter", 10, ["INT"], ("1d6*10", "min")
                ),
                BbwSkillSpeciality(
                    "jamming a comms system (vs electronics, comms/INT). DM -2/-4 for laser/maser respectively. DM+1"
                    " for each TL difference",
                    10,
                    ["INT"],
                    ("1d6", "min"),
                ),
            ],
        ),
        BbwSkill(
            "electronics, computers",
            [
                BbwSkillSpeciality("accessing public available data", 4, ["EDU", "INT"], ("1d6", "min")),
                BbwSkillSpeciality(
                    "activating a computer program on a ship's computer", 6, ["EDU", "INT"], ("1d6*10", "sec")
                ),
                BbwSkillSpeciality(
                    "searching a corporate database for evidence of illegal activity", 10, ["INT"], ("1d6", "hours")
                ),
                BbwSkillSpeciality(
                    "hacking into a secure computer network. DM for hacking a security programs. Failure means that the"
                    " targeted system may be able to trace the hacking attempt",
                    14,
                    ["INT"],
                    ("1d6*10", "hours"),
                ),
            ],
        ),
        BbwSkill(
            "electronics, remote ops",
            [
                BbwSkillSpeciality("using a mining drone to excavate an asteroid", 6, ["DEX"], ("1d6", "hours")),
            ],
        ),
        BbwSkill(
            "electronics, sensors",
            [
                BbwSkillSpeciality("making a detailed sensor scan", 6, ["INT", "EDU"], ("1d6*10", "min")),
                BbwSkillSpeciality("analizing sensor data", 8, ["INT"], ("1d6", "hours")),
            ],
        ),
        BbwSkill(
            "engineer",
            [
                BbwSkillSpeciality("", 8, ["EDU", "INT"], None),
            ],
        ),
        BbwSkill(
            "engineer, M-drive",
            [
                BbwSkillSpeciality(
                    "overcharging a thruster plate to increase a ship's agility", 10, ["INT"], ("1d6", "min")
                ),
                BbwSkillSpeciality(
                    "estimating a ship's tonnage from its observed performance", 8, ["INT"], ("1d6*10", "sec")
                ),
            ],
        ),
        BbwSkill(
            "engineer, J-drive",
            [
                BbwSkillSpeciality("making a jump", 4, ["EDU"], ("1d6*10", "min")),
            ],
        ),
        BbwSkill(
            "engineer, life support",
            [
                BbwSkillSpeciality(
                    "safely reducing power to life support to prolong a ship's battery life", 8, ["EDU"], ("1d6", "min")
                ),
            ],
        ),
        BbwSkill(
            "engineer, power",
            [
                BbwSkillSpeciality(
                    "monitoring a ship's power output to determine its capabilities", 10, ["INT"], ("1d6", "min")
                ),
            ],
        ),
        BbwSkill(
            "explosives",
            [
                BbwSkillSpeciality("planting charges to collapse a wall in a building", 8, ["EDU"], ("1d6*10", "min")),
                BbwSkillSpeciality(
                    "planting a breaching charge. Dmg multiplied by the effect", 8, ["EDU"], ("1d6*10", "sec")
                ),
                BbwSkillSpeciality(
                    "disarming a bomb equipped with anti-tamper trembler detonators", 14, ["DEX"], ("1d6", "min")
                ),
            ],
        ),
        BbwSkill(
            "flyer",
            [
                BbwSkillSpeciality("landing safely", 6, ["DEX"], ("1d6", "min")),
                BbwSkillSpeciality("racing another flyer (vs flyer/DEX)", 8, ["DEX"], ("1d6*10", "min")),
            ],
        ),
        BbwSkill(
            "gambler",
            [
                BbwSkillSpeciality("a casual game of poker (vs gambler/INT)", 8, ["INT"], ("1d6", "hours")),
                BbwSkillSpeciality("picking the right horse to bet on", 8, ["INT"], ("1d6", "min")),
            ],
        ),
        BbwSkill(
            "gunner",
            [
                BbwSkillSpeciality("", 8, ["INT", "DEX"], None),
            ],
        ),
        BbwSkill(
            "gunner, turret",
            [
                BbwSkillSpeciality("firing a turret at an enemy ship", 8, ["DEX"], ("1d6", "sec")),
            ],
        ),
        BbwSkill(
            "gunner, ortillery",
            [
                BbwSkillSpeciality("planetary bombardment/stationary targets", 8, ["INT"], ("1d6", "min")),
            ],
        ),
        BbwSkill(
            "gunner, screen",
            [
                BbwSkillSpeciality("activating a screen to intercept enemy fire", 10, ["DEX"], ("1d6", "sec")),
            ],
        ),
        BbwSkill(
            "gunner, capital",
            [
                BbwSkillSpeciality("firing a spinal mount weapon", 8, ["INT"], ("1d6", "min")),
            ],
        ),
        BbwSkill(
            "gun combat",
            [
                BbwSkillSpeciality("", 8, ["DEX"], ("1d6", "sec")),
            ],
        ),
        BbwSkill(
            "heavy weapons",
            [
                BbwSkillSpeciality("firing an artillery piece at a visible target", 8, ["DEX"], ("1d6", "sec")),
                BbwSkillSpeciality("firing an artillery piece using indirect fire", 10, ["INT"], ("1d6*10", "sec")),
            ],
        ),
        BbwSkill(
            "investigate",
            [
                BbwSkillSpeciality("searching a crime scene for clues", 8, ["INT"], ("1d6*10", "min")),
                BbwSkillSpeciality(
                    "watching a bank of security monitors in a starport, waiting for a specific criminal",
                    10,
                    ["INT"],
                    ("1d6", "hours"),
                ),
            ],
        ),
        BbwSkill(
            "jack-of-all-trades",
            [
                BbwSkillSpeciality("", 8, ["STR", "DEX", "END", "INT", "EDU", "SOC"], None),
            ],
        ),
        BbwSkill(
            "language",
            [
                BbwSkillSpeciality("ordering a meal, asking for basic directions", 6, ["EDU"], ("1d6", "sec")),
                BbwSkillSpeciality("holding a simple conversation", 8, ["EDU"], ("1d6*10", "sec")),
                BbwSkillSpeciality("understanding a complex technical document or report", 12, ["EDU"], ("1d6", "min")),
            ],
        ),
        BbwSkill(
            "leadership",
            [
                BbwSkillSpeciality("shouting an order", 8, ["SOC"], ("1d6", "sec")),
                BbwSkillSpeciality("rallying shaken troops", 10, ["SOC"], ("1d6", "sec")),
            ],
        ),
        BbwSkill(
            "mechanic",
            [
                BbwSkillSpeciality("reparing a damaged system in the field", 8, ["INT", "EDU"], ("1d6", "min")),
            ],
        ),
        BbwSkill(
            "medic",
            [
                BbwSkillSpeciality("first aid", 8, ["EDU"], ("1d6", "rounds")),
                BbwSkillSpeciality("treat poison or disease", 8, ["EDU"], ("1d6", "hours")),
                BbwSkillSpeciality("long-term care", 8, ["EDU"], ("1", "day")),
            ],
        ),
        BbwSkill(
            "melee",
            [
                BbwSkillSpeciality("swinging an object", 8, ["STR", "DEX"], ("1d6", "sec")),
            ],
        ),
        BbwSkill(
            "navigation",
            [
                BbwSkillSpeciality(
                    "plotting a course using an orbiting satellite beacon", 6, ["INT", "EDU"], ("1d6*10", "min")
                ),
                BbwSkillSpeciality("avoiding getting lost in a thick jungle", 10, ["INT"], ("1d6", "hours")),
            ],
        ),
        BbwSkill(
            "persuade",
            [
                BbwSkillSpeciality(
                    "bluffing your way past a guard (vs persuade/INT or SOC)", 8, ["INT", "SOC"], ("1d6", "min")
                ),
                BbwSkillSpeciality("haggling in a bazaar (vs persuade/INT or SOC)", 8, ["INT", "SOC"], ("1d6", "min")),
                BbwSkillSpeciality("intimidating a thug (vs persuade/INT or SOC)", 8, ["STR", "SOC"], ("1d6", "min")),
                BbwSkillSpeciality("asking the alien space princess to marry you", 14, ["SOC"], ("1d6*10", "min")),
            ],
        ),
        BbwSkill(
            "pilot",
            [
                BbwSkillSpeciality("", 8, ["DEX"], None),
            ],
        ),
        BbwSkill(
            "profession",
            [
                BbwSkillSpeciality("", 8, ["EDU", "INT", "STR"], None),
            ],
        ),
        BbwSkill(
            "recon",
            [
                BbwSkillSpeciality("working out the routine of a trio of guard patrols", 8, ["INT"], ("1d6*10", "min")),
                BbwSkillSpeciality(
                    "spotting the sniper before they shoot you (vs stealth/DEX)", 8, ["INT"], ("1d6*10", "sec")
                ),
            ],
        ),
        BbwSkill(
            "science",
            [
                BbwSkillSpeciality("remember a commonly known fact", 6, ["EDU"], ("1d6", "min")),
                BbwSkillSpeciality("researching a problem related to a field of science", 8, ["INT"], ("1d6", "days")),
            ],
        ),
        BbwSkill(
            "seafarer",
            [
                BbwSkillSpeciality("", 8, ["DEX"], None),
            ],
        ),
        BbwSkill(
            "seafarer, personal",
            [
                BbwSkillSpeciality("controlling a canoe in a violent storm", 14, ["END"], ("1d6", "hours")),
            ],
        ),
        BbwSkill(
            "stealth",
            [
                BbwSkillSpeciality("sneaking past the guard (vs recon/INT)", 8, ["DEX"], ("1d6*10", "sec")),
                BbwSkillSpeciality("avoiding detection by security patrol (vs recon/INT)", 8, ["DEX"], ("1d6", "min")),
            ],
        ),
        BbwSkill(
            "steward",
            [
                BbwSkillSpeciality("cooking a fine meal", 8, ["EDU"], ("1d6", "hours")),
                BbwSkillSpeciality(
                    "calming down an angry duke who has just been told he will not be jumping to his destination on"
                    " time",
                    10,
                    ["SOC"],
                    ("1d6", "min"),
                ),
            ],
        ),
        BbwSkill(
            "streetwise",
            [
                BbwSkillSpeciality(
                    "finding a dealer in illegal materials or technologies", 8, ["INT"], ("1d6*10", "hours")
                ),
                BbwSkillSpeciality("evade a police search (vs recon/INT)", 8, ["INT"], ("1d6*10", "min")),
            ],
        ),
        BbwSkill(
            "survival",
            [
                BbwSkillSpeciality(
                    "gathering supplies in the wilderness to survive for a week", 8, ["EDU"], ("1d6", "days")
                ),
                BbwSkillSpeciality("identifying a poisonous plant", 8, ["INT", "EDU"], ("1d6*10", "seconds")),
            ],
        ),
        BbwSkill(
            "tactic",
            [
                BbwSkillSpeciality(
                    "developing a strategy for attacking an enemy base", 8, ["INT"], ("1d6*10", "hours")
                ),
            ],
        ),
        BbwSkill(
            "vacc suit",
            [
                BbwSkillSpeciality("performing a system check on battle dress", 8, ["EDU"], ("1d6", "min")),
            ],
        ),
        BbwSkill(
            "0G",
            [
                BbwSkillSpeciality("", 8, ["DEX"], None),
            ],
        ),
    ]

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

    def __init__(self, upp=None, salary_ticket=None, reinvest=True, skill_rank={}, *args, **kwargs):
        self._size = 0
        self._capacity = 2
        self.set_upp(upp)
        self.set_salary_ticket(salary_ticket)
        self.set_reinvest(reinvest)
        self.set_skill_rank(skill_rank)
        super().__init__(*args, **kwargs)

    def armour(self):
        return BbwUtils.secondary_armour(self)

    def armor(self):
        return self.armour()

    def get_obj_capacity(self, i, is_per_obj=False):
        if i.armour() > 0 or "wearable" in i.name():
            return i.capacity(is_per_obj=is_per_obj) / 4
        return i.capacity(is_per_obj=is_per_obj)

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
                if i == name and value != 0:
                    raise InvalidArgument(
                        f"{name} is a generic skill. You need to give a speciality (ex: {name}, [speciality]) to have"
                        " it above 0. For now it has been added at level 0"
                    )
                break

        self.set_size()

    def set_capacity(self, v: float = None):
        if v is None:
            if self.SOC() is not None:
                v = BbwUtils.get_modifier(int(self.SOC()[0], 36), BbwPerson._soc_2_capacity)
            else:
                v = 2
        self._capacity = v
        self.set_size()
        super().set_capacity(v)

    def set_size(self, v: float = None):
        if v is None:
            v = self._capacity - self.carrying_capacity()
        super().set_size(v)

    def set_rank(self, name, value=None):
        if value is None:
            name, value = eval(name)
        if value is None:
            del self._skill_rank[name]
            return
        if type(value) is str:
            value = int(value, 36)

        BbwUtils.test_geq("skill/rank", value, 0)
        BbwUtils.test_leq("skill/rank", value, 6)
        self._skill_rank[name] = value

    def set_skill_rank(self, skill_rank={}):
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

        self.set_size()

    @BbwUtils.set_if_not_present_decor
    def skill_rank(self):
        return self._skill_rank

    # def skill(self, name):
    #     # the unskilled base value cannot surpass 0
    #     joat = max(min(self.rank(name="jack-of-all-trades", default_value=-3)[0][1], 3), 0)
    #     return self.rank(name=name, default_value=joat - 3)
    #
    # def rank(self, name, default_value=0):
    #     res = [(k, v) for k, v in self.skill_rank().items() if name in k]
    #     return sorted(res, key=lambda x: x[1]) if len(res) else [(name, default_value)]

    def skill(self, name):
        # the unskilled base value cannot surpass 0
        joat = max(min(self.rank(name="jack-of-all-trades", default_value=-3)[1], 3), 0)
        return self.rank(name=name, default_value=joat - 3)

    def rank(self, name, default_value=0):
        res = BbwSkill._get_skill(raw_list=list(self.skill_rank().items()), name=name)

        return res if res else (name, default_value)

    def skill_check(self, skill, roll: str = "2d6", chosen_stat: str = None):
        skill_name, skill_value = self.skill(skill)
        skill_obj = BbwSkill._get_skill(raw_list=BbwPerson._skills, name=skill_name)

        if not skill_obj:
            raise InvalidArgument(f"{skill_name} skill not found!")

        return skill_obj.roll(self, skill_name=skill_name, skill=skill_value, roll=roll, chosen_stat=chosen_stat)

    @BbwUtils.set_if_not_present_decor
    def salary_ticket(self, is_per_obj=False):
        return self._per_obj(self._salary_ticket, is_per_obj)

    @BbwUtils.set_if_not_present_decor
    def reinvest(self):
        return self._reinvest

    def set_reinvest(self, v: bool = True):
        self._reinvest = v

    def set_salary_ticket(self, v: float = None):
        """v < 0 means salary. Otherwise, ticket"""
        if v is None or v == float("inf"):
            v = -self.life_expenses()

        self._salary_ticket = v

    @BbwUtils.set_if_not_present_decor
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

    def set_upp(self, v: str = None):
        if v is None:
            self._upp = v
            return

        v = v.replace("-", "")

        BbwUtils.test_hexstr("upp", v, [6, 7])
        self._upp = v
        self.set_size()
        self.set_salary_ticket()

    def life_expenses(self):
        if self.SOC() is None:
            return 0

        return BbwUtils.get_modifier(int(self.SOC()[0], 36), self._soc_2_life_expenses)

    def carrying_capacity(self):
        if self.upp() is None:
            return 0

        return (
            (
                int(self.STR()[0], 36)
                + int(self.END()[0], 36)
                + self.rank("athletics, strength", 0)[1]
                + self.rank("athletics, endurance", 0)[1]
            )
            * 2
            / 1000
        )

    def info(self):
        l = []
        if l:
            l.append(super().info())

        if self.free_space() < self.carrying_capacity() / 2:
            l.append("encumbered DM-2")

        return ", ".join(l)

    def trip_payback(self, t: int):
        BbwUtils.test_geq("trip time", t, 0)

        if self.life_expenses() is None:
            return None
        return round(self.life_expenses() * t / 28)

    @staticmethod
    def max_stat(people, stat):
        ans = ("0", -3)
        q = []
        for i in people:
            val = getattr(i, stat)()
            if val is None:
                continue
            if ans[0] < val[0]:
                ans = val
                q = [i]
            elif ans[0] == val[0]:
                q.append(i)

        return ans, q

    @staticmethod
    def max_rank(people, rank):
        return BbwPerson.max_skill_rank(people, rank, "rank")

    @staticmethod
    def max_skill(people, skill):
        return BbwPerson.max_skill_rank(people, skill, "skill")

    @staticmethod
    def max_skill_rank(people, rank, f):
        ans = (rank, -4)
        pans = []
        for i in people:
            new_rank = getattr(i, f)(rank)
            if ans[1] < new_rank[1]:
                ans = new_rank
                pans = [i]
            elif ans[1] == new_rank[1]:
                pans.append(i)

        return ans, pans

    def _str_table(self, detail_lvl: int = 0):
        if detail_lvl == 0:
            return [self.count(), self.name()]
        else:
            return [
                self.count(),
                self.name(),
                self.upp(),
                self.salary_ticket(),
                self.status(),
                self.reinvest(),
                self.armour(),
                self.info(),
            ]

    def __str__(self, detail_lvl: int = 0):
        s = BbwUtils.print_table(self._str_table(detail_lvl), headers=self._header(detail_lvl), detail_lvl=detail_lvl)

        if detail_lvl == 0:
            return s

        if self.upp():
            s += "stats:\n"
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

        if len(self.get_children()):
            s += "backpack:\n"
            s += super().__str__(detail_lvl=-1)

        if len(self.skill_rank().items()):
            s += "skills and ranks:\n"
            h = ["skill/rank", "level"]
            t = [[k, str(v)] for k, v in sorted(self.skill_rank().items())]

            s += BbwUtils.print_table(t, headers=h, detail_lvl=1)

        return s

    @staticmethod
    def _header(detail_lvl=0):
        if detail_lvl == 0:
            return ["count", "name"]
        else:
            return [
                "count",
                "name",
                "upp",
                "salary (<0)/ticket (>=0)",
                "status",
                "reinvest",
                "armour",
                "info",
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

    @BbwUtils.set_if_not_present_decor
    def supply(self):
        return self._supply

    def _str_table(self, detail_lvl=0):
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
        BbwPerson(name="passenger, high", capacity=4, reinvest=False),
        BbwPerson(name="passenger, middle", capacity=4, reinvest=False),
        BbwPerson(name="passenger, basic", capacity=2, reinvest=False),
        BbwPerson(name="passenger, low", capacity=2, reinvest=False),
        BbwPerson(name="crew, pilot", capacity=2, salary_ticket=-6000, reinvest=False),
        BbwPerson(name="crew, astrogator", capacity=2, salary_ticket=-5000, reinvest=False),
        BbwPerson(name="crew, engineer", capacity=2, salary_ticket=-4000, reinvest=False),
        BbwPerson(name="crew, steward", capacity=2, salary_ticket=-2000, reinvest=False),
        BbwPerson(name="crew, medic", capacity=2, salary_ticket=-3000, reinvest=False),
        BbwPerson(name="crew, gunner", capacity=2, salary_ticket=-1000, reinvest=False),
        BbwPerson(name="crew, marine", capacity=2, salary_ticket=-1000, reinvest=False),
        BbwPerson(name="crew, other", capacity=2, salary_ticket=-1000, reinvest=False),
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
