from cogst5.trade import BbwTrade


def test_load_passengers(cs, w0, w1):
    header = ["high", "middle", "basic", "low"]
    for idx, i in enumerate(header):
        for _ in range(10):
            person, r = BbwTrade.find_passengers(cs, 2, 3, i, w0, w1)
            if person is not None:
                break

        assert person is not None
        assert person.count() > 0

def test_find_mail(cs, w0, w1):
    for _ in range(10):
        item, r, rt = BbwTrade.find_mail(cs, 2, 3, w0, w1)
        if item is not None:
            break

    assert item is not None
    assert item.count() > 0

def test_find_cargo(cs, w0, w1):
    header = ["major", "minor", "incidental"]
    for idx, i in enumerate(header):
        for _ in range(10):
            item, r = BbwTrade.find_freight(2, 3, i, w0, w1)
            if item is not None:
                break

        assert item is not None
        assert item.count() > 0


if __name__ == "__main__":
    from conftest import *
    def csw0w1():
        return cs.__pytest_wrapped__.obj(), w0.__pytest_wrapped__.obj(), w1.__pytest_wrapped__.obj()
    test_load_passengers(*csw0w1())
    test_find_cargo(*csw0w1())
    test_find_mail(*csw0w1())