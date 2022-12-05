from cogst5.trade import BbwTrade
from cogst5.person import BbwSupplier
from cogst5.calendar import BbwCalendar


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


def test_optimize_st_and_suppliers(cs, w0, w1):
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
