if __name__ == "__main__":
    import __init__

import copy

from cogst5.vehicle import BbwSpaceShip
from cogst5.item import BbwItem
from cogst5.models.errors import *
import pytest


def test_setters_and_print(max_detail_level):
    s = BbwSpaceShip(
        name="Zana's Nickel",
        m_drive="1",
        j_drive="2",
        type="k (safari ship)",
        power_plant="105",
        fuel_refiner_speed="40",
        is_streamlined="1",
        has_fuel_scoop="1",
        has_cargo_scoop="1",
        has_cargo_crane="0",
        info="repair DM-1",
        capacity="200",
        size="79.0",
        TL="14",
    )
    assert s.m_drive() == 1
    assert s.j_drive() == 2
    assert s.type() == "k (safari ship)"
    assert s.power_plant() == 105
    assert s.fuel_refiner_speed() == 40
    assert s.has_fuel_scoop() is True
    assert s.has_cargo_scoop() is True
    assert s.has_cargo_crane() is False
    assert s.info() == "repair DM-1"
    assert s.armour() == 0
    assert s.TL() == 14
    assert s.capacity() == 200
    assert s.size() == 79
    assert s.hull() == "(80/80)"

    for i in range(max_detail_level):
        print(s.__str__(detail_lvl=i))


def test_armour():
    s = BbwSpaceShip(
        name="Zana's Nickel",
        m_drive="1",
        j_drive="2",
        type="k (safari ship)",
        power_plant="105",
        fuel_refiner_speed="40",
        is_streamlined="1",
        has_fuel_scoop="1",
        has_cargo_scoop="1",
        has_cargo_crane="0",
        info="repair DM-1",
        capacity="200",
        TL="14",
    )
    assert s.armour() == 0

    a = BbwItem(name="armour, bonded superdense", capacity=22.4, armour=14)

    r = s.dist_obj(a, cont=None)
    assert s.armor() == 14


def test_m_drive():
    s = BbwSpaceShip(
        name="Zana's Nickel",
        m_drive="1",
        j_drive="2",
        type="k (safari ship)",
        power_plant="105",
        fuel_refiner_speed="40",
        is_streamlined="1",
        has_fuel_scoop="1",
        has_cargo_scoop="1",
        has_cargo_crane="0",
        info="repair DM-1",
        capacity="200",
        size=0,
        TL="14",
    )
    assert s.flight_time_m_drive(10000) == 0.023148148148148147
    assert s.flight_time_m_drive(0) == 0
    assert s.flight_time_m_drive("0") == 0
    with pytest.raises(InvalidArgument):
        s.flight_time_m_drive(-1)


def test_fuel_tank(cs):
    ft = cs.get_objs("fuel tank").objs()[0][0]
    assert ft.capacity() == 41
    cs.add_fuel("refined")
    assert ft.free_space() == 0
    cs.consume_fuel(5)
    assert ft.free_space() == 5
    assert ft.used_space() == 41 - 5
    cs.add_fuel("gas")
    assert ft.free_space() == 0
    assert ft.get_objs("refined").objs()[0][0].count() == 36
    assert ft.get_objs("unrefined").objs()[0][0].count() == 5
    q, t = cs.refine_fuel()
    assert q.count() == 5
    assert t == 5 / 40
    assert ft.get_objs("refined").objs()[0][0].count() == 41
    assert ft.free_space() == 0


if __name__ == "__main__":
    from conftest import cs

    test_setters_and_print(2)
    test_m_drive()
    cs = cs.__pytest_wrapped__.obj()
    test_fuel_tank(copy.deepcopy(cs))
    test_armour()
