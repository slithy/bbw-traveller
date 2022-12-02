from cogst5.world import BbwWorld
from cogst5.trade import BbwTrade

# def test_find_passengers():
#     w0 = BbwWorld(name="w0", uwp="B3848F9-B", zone="normal", hex="1904", sector=(-4, 1))
#     w1 = BbwWorld(name="w1", uwp="B3848F9-B", zone="normal", hex="1905", sector=(-4, 1))
#
#     header = ["high", "middle", "basic", "low"]
#     counter = ["0/0"] * len(header)
#     for idx, i in enumerate(header):
#         p, n_sectors, r, nd = BbwTrade.find_passengers(cs, "2", "3", i, w0, w1)
