from cogst5.models.errors import *
from tabulate import tabulate


def test_g(k, v, tr):
    if v <= tr:
        raise InvalidArgument(f"{k}: {v} must be > {tr}!")


def test_leq(k, v, tr):
    if v >= tr:
        raise InvalidArgument(f"{k}: {v} must be < {tr}!")


def test_geq(k, v, tr):
    if v < tr:
        raise InvalidArgument(f"{k}: {v} must be >= {tr}!")


def test_leq(k, v, tr):
    if v > tr:
        raise InvalidArgument(f"{k}: {v} must be <= {tr}!")


def check_get_item_list(k, l):
    if len(l) == 1:
        return l[0][1]
    if len(l) > 0:
        keys, _ = zip(*l)
        raise SelectionException(f"Multiple matches for key {k}: {keys}")
    return None


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
