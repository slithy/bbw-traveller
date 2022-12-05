import pytest
from cogst5.vehicle import BbwSpaceShip
from cogst5.world import BbwWorld
from cogst5.base import BbwObj


@pytest.fixture
def max_detail_level():
    return 2


@pytest.fixture
def cs():
    ship = BbwSpaceShip(
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
        armour="14",
        TL="14",
    )
    ship.dist_obj(BbwObj("fuel tank", 41, size=0))
    return ship

@pytest.fixture
def w0():
    return BbwWorld(name="Regina", uwp="A788899-C", zone="normal", hex="1910", sector=(-4, 1))


@pytest.fixture
def w1():
    return BbwWorld(name="Wypoc", uwp="E9C45479", zone="amber", hex="2011", sector=(-4, 1))
