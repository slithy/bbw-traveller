from cogst5.vehicle import BbwSpaceShip

def test_spaceship_init(max_detail_level):
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
            capacity="80",
        size="79",
        armour="14",
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
    assert s.armour() == 14
    assert s.TL() == 14
    assert s.capacity() == 80
    assert s.size() == 79
    assert s.hull() == "(79.0/80.0)"

    for i in range(max_detail_level):
        print(s.__str__(detail_lvl=i))


if __name__ == "__main__":
    test_spaceship_init(2)
