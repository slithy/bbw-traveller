from cogst5.models.errors import *
from cogst5.utils import *

import d20

import bisect

import math

wp_table = [[1, 5, 7, 16], [-4, 0, 1, 3]]
starport_table = [["A", "B", "D", "E", "X"], [2, 1, 0, -1, -3]]
zone_table = {"normal": 0, "amber": 1, "red": -4}
passenger_traffic_table = [[1, 3, 6, 10, 13, 15, 16, 17, 18, 19, 100], [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]]


class PassengerGroup:
    def __init__(self, kind, n, distance):
        self.kind = kind
        self.n = n
        self.distance = distance

    def __str__(self):
        s = f"kind: {self.kind}, n: {self.n}, ticket per person: {self.ticket()}.\n They require {self.n_rooms()} rooms"
        if self.kind in {"high", "middle"}:
            s += f", 1 ton of cargo and steward 1 every {10 if self.kind == 'high' else 100}"
        return s

    def n_rooms(self):
        if self.kind == "basic":
            return self.n / 2
        else:
            return self.n

    def ticket(self):
        return "TODO"


def passengers(main_check_modifier, steward, distance, kind, w0, w1):
    """
    - distance: in parsec
    - main_check_modifier: it is usually a carouse, broker or streetwise check + SOC.
    - steward: the max steward modifier of the group
    - w0_*: departure world data
    - w1_*: arrival world data
    """

    r = d20.roll("2d6").total + main_check_modifier - 8
    r += steward

    if kind == "high":
        r -= 4

    if kind == "low":
        r += 1

    for w in [w0, w1]:
        r += wp_table[1][bisect.bisect_left(wp_table[0], w["pop"])]
        r += starport_table[1][bisect.bisect_left(starport_table[0], w["starport"])]
        r += zone_table[w["zone"]]

    r -= distance - 1

    nd = passenger_traffic_table[1][bisect.bisect_left(passenger_traffic_table[0], r)]

    return PassengerGroup(kind, d20.roll(f"{nd}d6").total, distance)
