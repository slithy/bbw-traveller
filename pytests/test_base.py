import pytest

from cogst5.base import BbwObj, BbwContainer
from cogst5.models.errors import *


def test_setters_and_print(max_detail_level):
    o = BbwObj("ooo", 3, 2, 3)
    for i in range(max_detail_level):
        print(o.__str__(detail_lvl=i))

    c0 = BbwContainer("c0")
    for i in range(max_detail_level):
        print(c0.__str__(detail_lvl=i))
    c0 = BbwContainer("c0", 5)
    for i in range(max_detail_level):
        print(c0.__str__(detail_lvl=i))
    c0 = BbwContainer("c0", 5, 2)
    for i in range(max_detail_level):
        print(c0.__str__(detail_lvl=i))

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
    o.set_capacity(6)
    assert o.size() == 12

    c0 = BbwContainer("c0")
    assert c0.capacity() == float("inf")
    assert c0.size() == 0
    c0.set_size(3)
    assert c0.size() == 3
    c0.set_capacity(10)
    assert c0.capacity() == 10
    assert c0.size() == 3
    c0.set_capacity(2)
    assert c0.capacity() == 2
    assert c0.size() == 2
    c0.set_capacity(20)
    c0.dist_obj(o)
    assert c0.size() == 14
    assert c0.free_space() == 6
    c1 = BbwContainer("c0", 2)
    c0.dist_obj(c1)
    assert c0.free_space() == 4
    assert c0.size() == 16

def test_dist_routines():
    o = BbwObj("ooo", capacity=3, count=2, size=3)
    c0 = BbwContainer("c0")
    r = c0.dist_obj(o)
    assert r.count() == 2
    assert c0.size() == 6
    assert c0.capacity() == float("inf")
    o = BbwObj("ooo", capacity=3, count=2, size=3)
    c0 = BbwContainer("c0", 4)
    r = c0.dist_obj(o)
    assert r.count() == 1
    o = BbwObj("ooo", capacity=3, count=2, size=3)
    c0 = BbwContainer("c0", 9)
    r = c0.dist_obj(o)
    assert r.count() == 2
    r = c0.dist_obj(o)
    assert r.count() == 1
    o = BbwObj("ooo", capacity=3, count=2, size=3)
    c0 = BbwContainer("c0", 9, 5)
    r = c0.dist_obj(o)
    assert r.count() == 1
    o = BbwObj("ooo", capacity=3, count=2, size=3)
    c0 = BbwContainer("c0", 9, 2)
    c1 = BbwContainer("c0", 3, 2)
    r = c0.dist_obj(c1)
    assert r.count() == 1
    assert c0.size() == 5
    assert c0.free_space() == 4
    c0 = BbwContainer("c0", 9, 2)
    r = c0.dist_obj(o, unbreakable=True)
    assert r.count() == 2
    c0 = BbwContainer("c0", 5, 0)
    r = c0.dist_obj(o, unbreakable=True)
    assert r.count() == 0
    c0 = BbwContainer("c0", 10, 0)
    c1 = BbwContainer("c1", 9, 0)
    c0.dist_obj(c1)
    r = c0.dist_obj(o, False, "c1")

    assert r.count() == 2
    assert c0.get_objs("oo").count() == 2
    assert c0.get_objs("oo", False).count() == 0
    with pytest.raises(SelectionException):
        c0.get_objs("c", True, True, True)
    c0 = BbwContainer("c0", 10, 0)
    r = c0.dist_obj(o)
    assert c0.get_objs("c0").count() == 0
    assert c0.get_objs("c0", True, True).count() == 1

def test_rename():
    c0 = BbwContainer("c0", 10, 0)
    c1 = BbwContainer("c1", 9, 0)
    o = BbwObj("ooo", capacity=3, count=2, size=3)
    c1.dist_obj(o)
    c0.dist_obj(c1)

    c0.rename_obj("oo", "aaa")
    c0.rename_obj("c1", "dd")
    assert c0.get_objs("aa").count() == 2
    assert c0.get_objs("oo").count() == 0
    assert c0.get_objs("dd").count() == 1
    assert c0.get_objs("c1").count() == 0

def test_del_obj():
    c0 = BbwContainer("c0", 10, 0)
    o = BbwObj("ooo", capacity=3, count=2, size=3)
    c0.dist_obj(o)
    c0.del_obj("oo")
    assert c0.get_objs("oo").count() == 0
    c0.dist_obj(o)
    c0.del_obj("oo", 1)
    assert c0.get_objs("oo").count() == 1

def test_free_space():
    base, c1, c2, c3, c4 = BbwContainer("base"), BbwContainer("c1", 8), BbwContainer("c2", 3, 1), BbwContainer("c3", 3), BbwContainer("c4", 2, 1)
    c1.dist_obj(c2)
    base.dist_obj(c1)
    def fs(name=None):
        return sum([i.free_space() for i in [i for i, _ in base.get_objs(name=name, type0=BbwContainer).objs()]])

    assert fs() == 7
    base.dist_obj(c3, cont="c1")
    base.dist_obj(c4, cont="c3")
    assert fs() == 6
    assert fs("c3") == 1
    assert fs("c4") == 1
    assert fs("c1") == 2

if __name__ == "__main__":
    test_free_space()
