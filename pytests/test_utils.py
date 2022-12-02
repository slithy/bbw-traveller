from cogst5.utils import BbwUtils


def test_print_code():
    assert "3" == BbwUtils.print_code("3")
    assert "A" == BbwUtils.print_code("A")[0]
    assert "10" in BbwUtils.print_code("A")
