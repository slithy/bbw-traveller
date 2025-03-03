if __name__ == "__main__":
    import __init__

import copy

from cogst5.person import BbwPerson, BbwPersonFactory, BbwSkill, BbwSkillSpeciality
from cogst5.item import BbwItem
from cogst5.models.errors import *
import pytest


def test_setters_and_print(p0):
    print(p0.__str__(detail_lvl=2))


def test_basic_functions(p0):
    assert p0.salary_ticket() == -5000
    assert p0.life_expenses() == 5000
    assert p0.carrying_capacity() == 0.028
    assert p0.skill("gun combat")[1] == 0
    assert p0.skill("gun combat, slug")[1] == 1
    assert p0.capacity() == 4
    p0.set_skill("electronics, comm", 1)
    assert p0.skill("electronics")[1] == 0
    assert p0.skill("electronics, comm")[1] == 1
    assert p0.skill("bau")[1] == -3
    assert p0.rank("bau")[1] == 0
    assert p0.skill("jack-of-all-trades")[1] == -3
    p0.set_skill("jack-of-all-trades", 1)
    assert p0.skill("bau")[1] == -2
    p0.set_skill("jack-of-all-trades", 4)
    assert p0.skill("bau")[1] == -0
    assert p0.capacity() == 4
    assert p0.size() == 4 - 0.028


def test_person_factory():
    person = BbwPersonFactory.make("high")
    assert person.capacity() == 4
    assert not person.reinvest()
    assert person.size() == 4


def test_size_capacity():
    person = BbwPersonFactory.make("high")
    person.set_upp("337CCF")
    assert person.capacity() == 4
    assert person.size() == pytest.approx(3.98)
    person.set_skill("athletics, endurance", 1)
    assert person.size() == pytest.approx(3.978)
    person.set_upp("357CCF")
    assert person.size() == pytest.approx(3.978)
    person.set_upp("358CCF")
    assert person.size() == pytest.approx(3.976)
    assert person.used_space() == 0
    assert person.dist_obj(BbwItem(name="gun", capacity=0.001)).count() == 1
    assert person.dist_obj(BbwItem(name="box", capacity=0.04)).count() == 0
    assert person.dist_obj(BbwItem(name="box2", capacity=0.04, armour=1)).count() == 1
    assert person.used_space() == pytest.approx(0.04 / 4 + 0.001)
    assert person.free_space() == pytest.approx(0.02 + 0.004 - 0.04 / 4 - 0.001)
    assert person.info() == ""
    assert person.dist_obj(BbwItem(name="gun"))
    assert person.info() == ""
    assert person.dist_obj(BbwItem(name="gun"))
    assert person.info() != ""


def test_std_person():
    p = BbwPerson(name="Marie")
    assert p.capacity() == 2
    assert p.size() == 2
    p.set_upp("377CCF")
    assert p.size() == pytest.approx(1.98)
    p.set_capacity(4)
    assert p.size() == pytest.approx(3.98)


def test_skills():
    pp = BbwPerson(
        upp="37AEDC3", reinvest="True", skill_rank={"seafarer, personal": 4, "jack-of-all-trades":1, "art, holography": 1, "art, new_art": 1, "flyer, rotor": 1}
    )
    assert pp.skill(", per") == ("seafarer, personal", 4)
    assert pp.skill("zio fa")[1] == -2
    assert pp.skill("bau")[1] == -2
    assert pp.skill("seafarer")[1] == 0

    pp.skill_check("art")
    pp.skill_check("art, ho")
    pp.skill_check("gun combat")
    pp.skill_check("art, new_art")
    pp.skill_check("flyer, rotor")


if __name__ == "__main__":
    from conftest import p0

    p0 = p0.__pytest_wrapped__.obj()
    # test_setters_and_print(copy.deepcopy(p0))
    test_basic_functions(copy.deepcopy(p0))
    # test_person_factory()
    # test_size_capacity()
    # test_std_person()
    # test_skills()
