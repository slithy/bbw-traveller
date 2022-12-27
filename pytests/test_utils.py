if __name__ == "__main__":
    import __init__

from cogst5.utils import BbwUtils


def test_print_code():
    assert "3" == BbwUtils.print_code("3")
    assert "A" == BbwUtils.print_code("A")[0]
    assert "10" in BbwUtils.print_code("A")


def test_convert_d20_traveller():
    assert BbwUtils.conv_d20_2_traveller("3d6+5") == "3D+5"
    assert "3d6+5" == BbwUtils.conv_traveller_2_d20("3D+5")
    assert BbwUtils.conv_d20_2_traveller("2d6*10") == "2DD"
    assert "2d6*10" == BbwUtils.conv_traveller_2_d20("2DD")
    assert BbwUtils.to_traveller_roll("3d6+5") == "3D+5"
    assert BbwUtils.to_traveller_roll("3D+5") == "3D+5"
    assert BbwUtils.to_traveller_roll("2d6*10") == "2DD"
    assert BbwUtils.to_traveller_roll("2DD") == "2DD"
    assert BbwUtils.to_d20_roll("3d6+5") == "3d6+5"
    assert BbwUtils.to_d20_roll("3D+5") == "3d6+5"
    assert BbwUtils.to_d20_roll("2d6*10") == "2d6*10"
    assert BbwUtils.to_d20_roll("2DD") == "2d6*10"


if __name__ == "__main__":
    test_convert_d20_traveller()
