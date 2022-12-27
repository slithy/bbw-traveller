if __name__ == "__main__":
    import __init__

from cogst5.trade import BbwTrade
from cogst5.person import BbwSupplier
from cogst5.calendar import BbwCalendar
from cogst5.utils import BbwUtils


def test_load_passengers(cs, w0, w1):
    header = ["high", "middle", "basic", "low"]
    for idx, i in enumerate(header):
        for _ in range(10):
            person, r = BbwTrade.find_passengers(cs, 2, 3, i, w0, w1)
            if person is not None:
                break

        assert person is not None
        assert person.count() > 0
        assert i in person.name()


def test_find_mail(cs, w0, w1):
    for _ in range(10):
        item, r, rt = BbwTrade.find_mail(cs, 2, 3, w0, w1)
        if item is not None:
            break

    assert item is not None
    assert item.count() > 0
    assert "mail" in item.name()


def test_find_cargo(cs, w0, w1):
    header = ["major", "minor", "incidental"]
    for idx, i in enumerate(header):
        for _ in range(10):
            item, r = BbwTrade.find_freight(2, 3, i, w0, w1)
            if item is not None:
                break

        assert item is not None
        assert item.count() > 0
        assert i in item.name()


def test_suppliers_st(cs, w0, w1):
    supp = BbwSupplier(name="john, illegal")
    w0.suppliers().dist_obj(supp)
    supp = BbwSupplier(name="ben")
    w0.suppliers().dist_obj(supp)
    w0.set_supply(BbwTrade, BbwCalendar(12345).t(), None)

    def filter_illegal(t):
        return [i for i in t if "illegal" in i[0]]

    supp = w0.suppliers()["john, illegal"]
    assert supp.is_illegal()
    assert len(filter_illegal(supp.supply()))

    supp = w0.suppliers()["ben"]
    assert not supp.is_illegal()
    assert len(filter_illegal(supp.supply())) == 0


def test_optimize_st(cs, w0, w1):
    h, t = BbwTrade.optimize_st(cs, None, w1)
    assert "cybernetics" in t[0][0] and "illegal" in t[0][0]
    h, t = BbwTrade.optimize_st(cs, w0, None)
    assert "radioactives" in t[0][0]

    h, t = BbwTrade.optimize_st(cs, w0, filter=["advanced weapons, spt", "cybernetics, spt", "luxury goods, spt"])

    l = [i.replace(" ", "\n") for i in ["advanced weapons, spt", "cybernetics, spt"]]
    assert [t[0][0], t[1][0]] == l


if __name__ == "__main__":
    from conftest import cs, w0, w1

    cs, w0, w1 = cs.__pytest_wrapped__.obj(), w0.__pytest_wrapped__.obj(), w1.__pytest_wrapped__.obj()

    test_load_passengers(cs, w0, w1)
    test_find_mail(cs, w0, w1)
    test_find_cargo(cs, w0, w1)
    test_suppliers_st(cs, w0, w1)
    test_optimize_st(cs, w0, w1)
