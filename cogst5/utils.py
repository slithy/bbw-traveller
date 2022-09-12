from cogst5.models.errors import *
from tabulate import tabulate

import bisect


def test_g(k, v, tr):
    if v <= tr:
        raise InvalidArgument(f"{k}: {v} must be > {tr}!")


def test_l(k, v, tr):
    if v >= tr:
        raise InvalidArgument(f"{k}: {v} must be < {tr}!")


def test_leq(k, v, tr):
    if v >= tr:
        raise InvalidArgument(f"{k}: {v} must be < {tr}!")


def test_hexstr(k, v, n):
    if type(v) is not str:
        raise InvalidArgument(f"{k}: {v} must be a str!")

    if len(v) != n:
        raise InvalidArgument(f"{k}: {v} len must be {n}!")

    for i in v:
        test_geq(k, int(i, 16), 0)
        test_leq(k, int(i, 16), 15)


def test_geq(k, v, tr):
    if v < tr:
        raise InvalidArgument(f"{k}: {v} must be >= {tr}!")


def test_leq(k, v, tr):
    if v > tr:
        raise InvalidArgument(f"{k}: {v} must be <= {tr}!")


def check_get_item_list(k, l):
    if len(l) == 1:
        return l[0][0], l[0][1], True
    if len(l) > 0:
        keys, _ = zip(*l)
        raise SelectionException(f"Multiple matches for key {k}: {keys}")
    return None, None, False


def print_table(t, headers=()):
    if len(t) and not isinstance(t[0], list):
        return tabulate([t], headers)
    else:
        return tabulate(t, headers)


def int_or_float(v):
    try:
        int(v)
        t = int
    except ValueError:
        float(v)
        t = float
    return t


def conv_days_2_time(d):
    days = int(d)
    d = d % 1
    hours = int(24 * d)
    d = (24 * d) % 1
    minutes = int(60 * d)
    d = (60 * d) % 1

    ans = []
    if days:
        ans.append(f"{days}d")
    if hours or len(ans):
        ans.append(f"{hours}h")
    ans.append(f"{minutes}m")

    return "-".join(ans)


def get_item(key, d):
    k, v, valid = check_get_item_list(key, [(k, v) for k, v in d.items() if key == k])

    if valid:
        return k, v
    k, v, valid = check_get_item_list(key, [(k, v) for k, v in d.items() if key.lower() == k.lower()])
    if valid:
        return k, v
    # If we want to check by prefix, reenable this
    # ans = self.check_getitem_list(key, [(k, v) for k, v in self.items() if k.startswith(key)])
    # if ans:
    #     return k, v
    # ans = self.check_getitem_list(key, [(k, v) for k, v in self.items() if k.lower().startswith(key.lower())])
    # if ans:
    #     return k, v
    k, v, valid = check_get_item_list(key, [(k, v) for k, v in d.items() if key in k])
    if valid:
        return k, v
    k, v, valid = check_get_item_list(key, [(k, v) for k, v in d.items() if key.lower() in k.lower()])
    if valid:
        return k, v

    raise SelectionException(f"Unknown key: {key}. Possible options: {', '.join(d.keys())}")


def get_modifier(key, ll):
    return ll[1][bisect.bisect_left(ll[0], key)]
