from cogst5.base import BbwObj
from cogst5.models.errors import *
import pytest


def test_setters_and_print(max_detail_level):
    o = BbwObj("ooo", 3, 2, 3)
    for i in range(max_detail_level):
        print(o.__str__(detail_lvl=i))


def test_capacity_and_size():
    o = BbwObj("ooo", capacity=3, count=2, size=3)
    assert o.capacity() == 6
    assert o.size() == 6
    assert o.size(is_per_obj=True) == 3
    assert o.capacity(is_per_obj=True) == 3
    o = BbwObj("ooo", capacity=3, count=2)
    assert o.size() == 6
    with pytest.raises(InvalidArgument):
        o.set_attr("size", 7)
    with pytest.raises(InvalidArgument):
        o.set_attr("size", -1)
    o.set_attr("size", 0)
    o.set_attr("capacity", float("inf"))
    o.set_attr("size", 1000)
    o.set_attr("size", float("inf"))
    assert o.size() == float("inf")
    assert o.size(is_per_obj=True) == float("inf")
    o.set_attr("capacity", 1000)
    assert o.size(is_per_obj=True) == 1000


if __name__ == "__main__":
    test_capacity_and_size()
