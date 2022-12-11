import pytest

from cogst5.base import BbwObj, BbwRes
from cogst5.models.errors import *


def test_setters_and_print(max_detail_level):
    o = BbwObj("ooo", 3, 2, 3)
    for i in range(max_detail_level):
        print(o.__str__(detail_lvl=i))

    c0 = BbwObj("c0", capacity="inf", size=5)
    for i in range(max_detail_level):
        print(c0.__str__(detail_lvl=i))
    c0 = BbwObj("c0", 5)
    for i in range(max_detail_level):
        print(c0.__str__(detail_lvl=i))
    c0 = BbwObj("c0", 5, 2)
    for i in range(max_detail_level):
        print(c0.__str__(detail_lvl=i))


def test_capacity_and_size():
    o = BbwObj("ooo", capacity=3, count=2, size=3)
    assert o.capacity() == 6
    assert o.size() == 6
    assert o.size(is_per_obj=True) == 3
    assert o.capacity(is_per_obj=True) == 3
    o = BbwObj("ooo", capacity=3, count=2, size=3)
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
    o.set_attr("size", 1000)
    o.set_attr("capacity", 1000)
    assert o.size(is_per_obj=True) == 1000
    o.set_size(6)
    o.set_capacity(6)
    assert o.size() == 12

    c0 = BbwObj("c0", "inf")
    assert c0.capacity() == float("inf")
    assert c0.size() == float("inf")
    c0.set_size(3)
    assert c0.size() == 3
    c0.set_capacity(10)
    assert c0.capacity() == 10
    assert c0.size() == 3
    with pytest.raises(InvalidArgument):
        c0.set_capacity(2)
    c0.set_size(2)
    c0.set_capacity(2)
    assert c0.capacity() == 2
    assert c0.size() == 2
    c0.set_capacity(20)
    c0.dist_obj(o)
    assert c0.size() == 2
    assert c0.free_space() == 6
    c1 = BbwObj("c0", 2)
    c0.dist_obj(c1)
    assert c0.free_space() == 4
    assert c0.size() == 2

    c0, c1 = BbwObj("c0", 10, size=0), BbwObj("c0", 8, size=0)
    c0.dist_obj(c1)
    assert c0.free_space() == 2
    c0.set_size(2)
    with pytest.raises(InvalidArgument):
        c0.set_size(3)


def test_dist_routines():
    o = BbwObj("ooo", capacity=3, count=2, size=3)
    c0 = BbwObj("c0", capacity="inf", size=0)
    r = c0.dist_obj(o)
    assert r.count() == 2
    assert c0.used_space() == 6
    c0.set_size(2)
    assert c0.size() == 2
    assert c0.capacity() == float("inf")
    o = BbwObj("ooo", capacity=3, count=2, size=3)
    c0 = BbwObj("c0", capacity=4, size=0)
    r = c0.dist_obj(o)
    assert r.count() == 1
    o = BbwObj("ooo", capacity=3, count=2, size=3)
    c0 = BbwObj("c0", capacity=9, size=0)
    r = c0.dist_obj(o)
    assert r.count() == 2
    r = c0.dist_obj(o)
    assert r.count() == 1
    o = BbwObj("ooo", capacity=3, count=2, size=3)
    c0 = BbwObj("c0", capacity=9, size=5)
    r = c0.dist_obj(o)
    assert r.count() == 1
    o = BbwObj("ooo", capacity=3, count=2, size=3)
    c0 = BbwObj("c0", capacity=9, size=2)
    c1 = BbwObj("c0", capacity=3, size=2)
    r = c0.dist_obj(c1)
    assert r.count() == 1
    assert c0.size() == 2
    assert c0.free_space() == 4
    c0 = BbwObj("c0", capacity=9, size=2)
    r = c0.dist_obj(o, unbreakable=True)
    assert r.count() == 2
    c0 = BbwObj("c0", 5, size=0)
    r = c0.dist_obj(o, unbreakable=True)
    assert r.count() == 0
    c0 = BbwObj("c0", 10, size=0)
    c1 = BbwObj("c1", 9, size=0)
    c0.dist_obj(c1)
    r = c0.dist_obj(o, False, "c1")

    assert r.count() == 2
    assert c0.get_objs("oo").count() == 2
    assert c0.get_objs("oo", False).count() == 0
    with pytest.raises(SelectionException):
        c0.get_objs("c", True, True, True)
    c0 = BbwObj("c0", 10, size=0)
    r = c0.dist_obj(o)
    assert c0.get_objs("c0").count() == 0
    assert c0.get_objs("c0", True, True).count() == 1


def test_rename():
    c0 = BbwObj("c0", 10, size=0)
    c1 = BbwObj("c1", 9, size=0)
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
    c0 = BbwObj("c0", 10, size=0)
    o = BbwObj("ooo", capacity=3, count=2, size=3)
    c0.dist_obj(o)
    c0.del_obj("oo")
    assert c0.get_objs("oo").count() == 0
    c0.dist_obj(o)
    c0.del_obj("oo", 1)
    assert c0.get_objs("oo").count() == 1


def test_free_space():
    base, c1, c2, c3, c4 = (
        BbwObj("base", "inf", size=0),
        BbwObj("c1", 8, size=0),
        BbwObj("c2", 3, size=1),
        BbwObj("c3", 3, size=0),
        BbwObj("c4", 2, size=1),
    )
    c1.dist_obj(c2)
    base.dist_obj(c1)
    def fs(name=None):
        return sum([i.free_space() for i in [i for i, _ in base.get_objs(name=name, type0=BbwObj).objs()]])

    assert fs() == 7
    base.dist_obj(c3, cont="c1")
    base.dist_obj(c4, cont="c3")

    assert fs() == 6
    assert fs("c3") == 1
    assert fs("c4") == 1
    assert fs("c1") == 2

def test_res():
    c0 = BbwObj("c0", 9, size=0)
    res = c0.dist_obj(BbwObj("o0", capacity=1))
    assert res.count() == 1
    res = c0.dist_obj(BbwObj("o0", capacity=1, count=2))
    assert res.count() == 2
    res = c0.get_objs("o0")
    assert res.count() == 3
    assert len(res) == 1
    assert res[0].name() == "o0"
    with pytest.raises(IndexError):
        res[1]
    c0.dist_obj(BbwObj("c1", 5, size=0))
    res = c0.dist_obj(BbwObj("o1", capacity=1), cont="c1")
    assert res.count() == 1
    res = c0.get_objs("o")
    assert res.count() == 4
    assert len(res) == 2
    res.print_objs()
    res.print_containers()
    print(res)
    assert res[1].name() == "o1"
    with pytest.raises(IndexError):
        res[2]

    res0 = c0.get_objs("o0")
    res1 = c0.get_objs("o1")
    res = res0+res1
    assert res.count() == 4
    assert len(res) == 2
    res0 = c0.dist_obj(BbwObj("o0", capacity=1, count=1))
    res1 += res0
    assert res1.count() == 2
    assert len(res1) == 2
    assert res1.objs()[0][1].name() == "c1"
    assert res1.objs()[1][1].name() == "c0"
    res0 = c0.dist_obj(BbwObj("o0", capacity=1, count=1))
    assert res0.objs()[0][1].name() == "c1"

if __name__ == "__main__":
    test_setters_and_print(2)
    test_capacity_and_size()
    test_dist_routines()
    test_rename()
    test_del_obj()
    test_free_space()
    test_res()

