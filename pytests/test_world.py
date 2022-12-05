from cogst5.world import BbwWorld


def test_world_stats():
    w0 = BbwWorld(name="w0", uwp="B3848F9-B", zone="normal", hex="1904", sector=(-4, 1))

    assert w0.SP()[:2] == ("B", 1)
    assert w0.SIZE()[:2] == ("3", 3)
    assert w0.ATM()[:2] == ("8", 8)
    assert w0.HYDRO()[:2] == ("4", 4)
    assert w0.POP()[:2] == ("8", 8)
    assert w0.GOV()[:2] == ("F", 15)
    assert w0.LAW()[:2] == ("9", 9)
    assert w0.TL()[:2] == ("B", 11)


def test_setters_and_print(max_detail_level):
    w0 = BbwWorld(name="w0", uwp="B3848F9-B", zone="normal", hex="1904", sector=(-4, 1))
    for i in range(max_detail_level):
        w0.__str__(detail_lvl=i)


def test_distance():
    w0 = BbwWorld(name="w0", uwp="B3848F9-B", zone="normal", hex="1910", sector=(-4, 1))
    w1 = BbwWorld(name="w1", uwp="B3848F9-B", zone="normal", hex="1910", sector=(-4, 1))

    assert BbwWorld.distance(w0, w1) == 0
    for i in ["1909", "1809", "1810", "1911", "2010", "2009"]:
        w1.set_hex(i)
        assert BbwWorld.distance(w0, w1) == 1
    w1.set_hex("1511")
    assert BbwWorld.distance(w0, w1) == 4
    w1.set_hex("1607")
    assert BbwWorld.distance(w0, w1) == 4
    w1.set_hex("1806")
    assert BbwWorld.distance(w0, w1) == 4
    w1.set_hex("2110")
    assert BbwWorld.distance(w0, w1) == 2
    w1.set_hex("2111")
    assert BbwWorld.distance(w0, w1) == 2
    w1.set_hex("2313")
    assert BbwWorld.distance(w0, w1) == 5
    w1.set_hex("1140")
    w1.set_sector((-4, 2))
    assert BbwWorld.distance(w0, w1) == 14
    w1.set_hex("3111")
    w1.set_sector((-5, 1))
    assert BbwWorld.distance(w0, w1) == 20


def test_set_trade_code():
    w0 = BbwWorld(name="w0", uwp="A788899-C", zone="normal", hex="1910", sector=(-4, 1))
    assert w0.trade_codes() == {"Ri", "Ht"}
    w0.set_trade_code("('Ri', None)")
    assert w0.trade_codes() == {"Ht"}
    w0.set_trade_code("As", 1)
    assert w0.trade_codes() == {"Ht", "As"}
    w0.set_trade_codes()
    assert w0.trade_codes() == {"Ri", "Ht"}


def test_people():
    w0 = BbwWorld(name="w0", uwp="A788899-C", zone="normal", hex="1910", sector=(-4, 1))
    w0.people()


def test_set_docking_fee():
    w0 = BbwWorld(name="w0", uwp="A788899-C", zone="normal", hex="1910", sector=(-4, 1))

    w0.set_docking_fee(1000)
    assert w0.docking_fee() == 1000

    oldv = w0.docking_fee()
    for i in range(10):
        w0.set_docking_fee()
        newv = w0.docking_fee()
        assert newv >= 1000
        assert newv <= 6000
        if newv != oldv:
            break
    assert w0.docking_fee() != oldv


if __name__ == "__main__":
    test_setters_and_print(2)
