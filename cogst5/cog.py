import copy

import discord
from discord.ext import commands
from cogst5.library import Library
import json
import jsonpickle
from os.path import basename
import time

from cogst5.models.errors import *

from cogst5.session_data import BbwSessionData
from cogst5.base import *
from cogst5.person import *
from cogst5.vehicle import *
from cogst5.company import *
from cogst5.item import *
from cogst5.world import *
from cogst5.trade import *


jsonpickle.set_encoder_options("json", sort_keys=True)


class Game(commands.Cog):
    """Traveller 5 commands."""

    def __init__(self, bot):
        self.bot = bot
        self.library = Library()
        self.session_data = BbwSessionData()

    async def send(self, ctx, msg):
        """Split long messages to workaround the discord limit"""

        if type(msg) is not str:
            msg = msg.__str__()
        msg = "__                                                                          __\n" + msg
        max_length = 2000

        for i in BbwUtils.split_md_compatible(msg, max_length):
            await ctx.send(i)

    # ==== commands ====
    @commands.command(name="library_data", aliases=["library", "lib", "l"])
    async def query_library(self, ctx, search_term: str, *args):
        """*Query ship Library Database*

        In a universe with no faster-than-light communication, there is no Galactic Internet. Every ship therefore carries its own database of information about a wide variety of subjects: worlds, lifeforms, corporations, politics, history, *etc.* Almost all ships in Traveller have this database in the form of the **Library/0** program. The Library database is periodically updated, when the ship is in port at a Class A or Class B starport.

        `<search_term>` can be a single word, or a phrase. If there is an unambiguous partial match with an entry in the database, the Library Data for that entry will be returned. If there are multiple matching terms, a list of possible matches will be returned (try again with a more specific term from the list).
        """
        for arg in args:
            search_term = f"{search_term} {arg}"
        await self.send(ctx, self.library.search(search_term))

    ##################################################
    ### load/save
    ##################################################

    @commands.command(name="save")
    async def save_session_data(self, ctx, filename: str = "session_data"):
        """Save session data to a file in JSON format."""

        enc_data = jsonpickle.encode(self.session_data)
        p = f"/save/{filename}.json"
        with open(p, "w") as f:
            json.dump(json.loads(enc_data), f, indent=2)

        ts = time.gmtime()
        timestamp = time.strftime("%Y%m%d%H%M%S", ts)
        p_backup = f"/save/{filename}_{timestamp}.json"
        with open(p_backup, "w") as f:
            json.dump(json.loads(enc_data), f, indent=2)

        await self.send(ctx, f"Session data saved as: {basename(p)}. Backup in: {basename(p_backup)}")

    @commands.command(name="load")
    async def load_session_data(self, ctx, filename: str = "session_data.json"):
        """Load session data from a JSON-formatted file."""

        with open(f"../../save/{basename(filename)}", "r") as f:
            enc_data = json.dumps(json.load(f))
            self.session_data = jsonpickle.decode(enc_data)

        await self.send(ctx, f"Session data loaded from {filename}.")

    ##################################################
    ### trade
    ##################################################

    @commands.command(name="find_passengers", aliases=[])
    async def find_passengers(self, ctx, carouse_or_broker_or_streetwise_mod, SOC_mod, w_to_name):
        cs = self.session_data.get_ship_curr()
        w0 = self.session_data.get_world_curr()
        w1 = self.session_data.charted_space().get_objs(name=w_to_name, only_one=True).objs()[0][0]

        header = ["high", "middle", "basic", "low"]
        counter = ["0/0"] * len(header)
        for idx, i in enumerate(header):
            p, n_sectors = BbwTrade.find_passengers(cs, carouse_or_broker_or_streetwise_mod, SOC_mod, i, w0, w1)
            if p is not None:
                res = await self.add_person(ctx, name=i, count=p.count(), n_sectors=n_sectors, mute=True)
                counter[idx] = f"{res.count()}/{p.count()}"

        await self.send(ctx, f"passengers (loaded/available):\n{BbwUtils.print_table(counter, headers=header)}")

    @commands.command(name="find_mail_and_freight", aliases=[])
    async def find_mail_and_freight(self, ctx, broker_or_streetwise_mod, SOC_mod, w_to_name):
        cs = self.session_data.get_ship_curr()
        w0 = self.session_data.get_world_curr()
        w1 = self.session_data.charted_space().get_objs(name=w_to_name, only_one=True).objs()[0][0]

        header = ["mail", "major", "minor", "incidental"]
        counter = ["0/0"] * len(header)

        mail_value, n_canisters = 0, 0
        for idx, i in enumerate(header):
            if i == "mail":
                item, n_sectors = BbwTrade.find_mail(cs, broker_or_streetwise_mod, SOC_mod, w0, w1)
            else:
                item, n_sectors = BbwTrade.find_freight(broker_or_streetwise_mod, SOC_mod, i, w0, w1)

            if item is not None:
                res = await self.add_item(
                    ctx, name=i, count=item.count(), n_sectors=n_sectors, unbreakable=(i == "mail"), mute=True
                )
                if i == "mail" and res.count():
                    mail_value, n_canisters = sum([i.value() for i, _ in res.objs()]), res.count()
                    self.session_data.company().add_log_entry(
                        mail_value, f"mail (`{n_canisters}` canisters)", self.session_data.calendar().t()
                    )

                counter[idx] = f"{res.count()}/{item.count()}"

        await self.send(ctx, f"mail and freight (loaded/available):\n{BbwUtils.print_table(counter, headers=header)}")
        if mail_value:
            await self.send(ctx, f"mail (`{n_canisters}` canisters): {mail_value} Cr")

    @commands.command(name="load_ship", aliases=[])
    async def load_ship(self, ctx, carouse_or_broker_or_streetwise_mod, brocker_or_streetwise_mod, SOC_mod, w_to_name):
        # load passengers
        await self.find_passengers(ctx, carouse_or_broker_or_streetwise_mod, SOC_mod, w_to_name)

        # load mail and freight
        await self.find_mail_and_freight(
            ctx,
            brocker_or_streetwise_mod,
            SOC_mod,
            w_to_name,
        )

    @commands.command(name="unload_passengers", aliases=[])
    async def unload_passengers(self, ctx):
        cs = self.session_data.get_ship_curr()
        tot = 0
        for i in BbwPerson._std_tickets.keys():
            tot += sum([i.salary_ticket() for i, _ in cs.containers().get_objs(name=i).objs()])
            await self.del_obj(ctx, name=i, mute=True)
        for i in BbwItem._luggage_capacities.keys():
            await self.del_obj(ctx, name=i, mute=True)

        self.session_data.company().add_log_entry(int(tot), f"passenger tickets", self.session_data.calendar().t())

        await self.send(ctx, f"passenger tickets: {int(tot)} Cr")

    @commands.command(name="unload_mail_and_freight", aliases=[])
    async def unload_mail_and_freight(self, ctx):
        cs = self.session_data.get_ship_curr()
        tot = 0
        for i in BbwItem._freight_lot_ton_multi_dict.keys():
            if i != "mail":
                tot += sum([i.value() for i, _ in cs.containers().get_objs(name=i).objs()])
            await self.del_obj(ctx, name=i, mute=True)

        self.session_data.company().add_log_entry(int(tot), f"freight", self.session_data.calendar().t())

        await self.send(ctx, f"freight: {int(tot)} Cr")

    @commands.command(name="unload_ship", aliases=[])
    async def unload(self, ctx, except_set="{}"):
        await self.unload_passengers(ctx)
        await self.unload_mail_and_freight(ctx)

    ##################################################
    ### spaceship
    ##################################################

    @commands.command(name="set_spaceship", aliases=["add_spaceship", "add_starship", "add_ship"])
    async def set_spaceship(
        self,
        ctx,
        name,
        size,
        capacity,
        type,
        TL,
        armour,
        m_drive,
        j_drive,
        power_plant,
        fuel_refiner_speed,
        is_streamlined,
        has_fuel_scoop,
        has_cargo_crane,
    ):
        """Add a ship"""

        if name in self.session_data.fleet():
            raise InvalidArgument(
                f"A ship with that name: {name} already exists! If you really want to replace it, delete it first"
            )

        s = BbwSpaceShip(
            name=name,
            size=size,
            capacity=capacity,
            type=type,
            TL=TL,
            armour=armour,
            m_drive=m_drive,
            j_drive=j_drive,
            power_plant=power_plant,
            fuel_refiner_speed=fuel_refiner_speed,
            is_streamlined=is_streamlined,
            has_fuel_scoop=has_fuel_scoop,
            has_cargo_crane=has_cargo_crane,
        )
        self.session_data.fleet().add_obj(s)

        await self.send(ctx, f"The ship {name} was successfully added to the fleet.")
        await self.set_ship_curr(ctx, name)

    @commands.command(name="del_ship", aliases=[])
    async def del_ship(self, ctx, name):
        """Del ship"""

        res = self.session_data.fleet().del_obj(name=name)
        names = [i.name() for i, _ in res.objs()]
        if res.count():
            await self.send(ctx, f"The ships {', '.join(names)} were successfully deleted.")
        else:
            await self.send(ctx, f"No ship was deleted. `{name}` ship not found!")

        if self.session_data.ship_curr() in names:
            await self.set_ship_curr(ctx, "")
        await self.fleet(ctx)

    @commands.command(name="rename_ship_curr", aliases=["rename_ship"])
    async def rename_ship(self, ctx, new_name):
        cs = self.session_data.get_ship_curr()

        self.session_data.fleet().rename_obj(cs.name(), new_name)

        await self.set_ship_curr(ctx, new_name)

    @commands.command(name="ship_curr", aliases=["ship"])
    async def ship_curr(self, ctx, compactness=1):
        """Current ship summary"""

        cs = self.session_data.get_ship_curr()

        await self.send(ctx, cs.__str__(is_compact=compactness))

    @commands.command(name="set_ship_curr", aliases=[])
    async def set_ship_curr(self, ctx, name):
        """Set current ship"""

        self.session_data.set_ship_curr(name)

        await self.ship_curr(ctx)

    @commands.command(name="fleet", aliases=["ships"])
    async def fleet(self, ctx):
        """Fleet summary"""

        await self.send(ctx, self.session_data.fleet().__str__(is_compact=False))

    @commands.command(name="set_ship_attr", aliases=["set_ship_curr_attr"])
    async def set_ship_attr(self, ctx, attr_name, value):
        cs = self.session_data.get_ship_curr()
        cs.set_attr(attr_name, value)

        await self.ship_curr(ctx)

    @commands.command(name="t_m_drive", aliases=["m_drive_t"])
    async def travel_time_m_drive(self, ctx, d_km):
        cs = self.session_data.get_ship_curr()

        t = cs.flight_time_m_drive(d_km)

        await self.send(
            ctx, f"the m drive {cs.m_drive()} travel time to cover {d_km} km is: {BbwUtils.conv_days_2_time(t)}"
        )

        return t

    @commands.command(name="m_drive", aliases=[])
    async def travel_m_drive(self, ctx, d_km=None, is_diam_for_jump=False):
        if d_km is None:
            d_km = 100 * self.session_data.get_world_curr().d_km()
        else:
            try:
                d_km = int(d_km)
                is_diam_for_jump = bool(int(is_diam_for_jump))
                if is_diam_for_jump:
                    d_km *= 100
            except ValueError:
                d_km = 100 * self.session_data.charted_space().get_objs(name=d_km, only_one=True).objs()[0][0].d_km()

        t = await self.travel_time_m_drive(ctx, d_km)
        await self.newday(ctx, ndays=t, travel_accounting=True)

    @commands.command(name="t_j_drive", aliases=["j_drive_t"])
    async def travel_time_j_drive(self, ctx, n_jumps=1):
        cs = self.session_data.get_ship_curr()

        t = cs.flight_time_j_drive(n_jumps)

        await self.send(
            ctx, f"the j drive {cs.j_drive()} travel time to do {n_jumps} jumps is: {BbwUtils.conv_days_2_time(t)}"
        )
        return t

    @commands.command(name="trip_accounting_life_support", aliases=[])
    async def trip_accounting_life_support(self, ctx, t):
        cs = self.session_data.get_ship_curr()
        res, life_support_costs = cs.var_life_support(t)
        self.session_data.company().add_log_entry(
            -life_support_costs, f"var life support ({res.count()} people)", self.session_data.calendar().t()
        )

        await self.send(ctx, f"variable life support costs: {life_support_costs} Cr")

    @commands.command(name="trip_accounting_payback", aliases=[])
    async def trip_accounting_payback(self, ctx, t):
        cs = self.session_data.get_ship_curr()

        msg = f""
        crew = [i for i, _ in cs.containers().get_objs(name="crew", type0=BbwPerson).objs()]
        for i in crew:
            payback = i.trip_payback(t)

            if payback is None:
                msg += f"upp not known for `{i.name()}`. I cannot calculate the payback!\n"
            else:
                if i.reinvest():
                    self.session_data.company().add_log_entry(
                        payback, f"{i.name()} reinvested the payback", self.session_data.calendar().t()
                    )
                msg += f"{i.name()} gets back {payback} Cr {'(reinvested)' if i.reinvest() else ''}\n"

        await self.send(ctx, msg)

    @commands.command(name="j_drive", aliases=[])
    async def travel_j_drive(self, ctx, w_to_name):
        w0 = self.session_data.get_world_curr()
        w1 = self.session_data.charted_space().get_objs(name=w_to_name, only_one=True).objs()[0][0]
        n_sectors = BbwWorld.distance(w0, w1)
        if await self.consume_fuel(ctx, n_sectors * 20):
            return
        t = await self.travel_time_j_drive(ctx, n_sectors)
        await self.newday(ctx, ndays=t, travel_accounting=True)
        await self.set_world_curr(ctx, w_to_name)

    @commands.command(name="fuel", aliases=[])
    async def fuel(self, ctx, source, q=float("inf")):
        if q > 0:
            await self.add_fuel(ctx, source, q)
        else:
            await self.consume_fuel(ctx, q)

    @commands.command(name="get_fuel", aliases=["add_fuel", "refuel", "buy_fuel"])
    async def add_fuel(self, ctx, source, count=float("inf"), value=None):
        cs = self.session_data.get_ship_curr()
        res, cost = cs.add_fuel(source=source, count=count)
        if res.count():
            t = d20.roll(f"1d6").total / 24
            await self.send(ctx, f"refueling time is: {BbwUtils.conv_days_2_time(t)}")

            if value is None:
                value = cost
            if value:
                await self.add_money(ctx, value=-value, description=res)
        else:
            await self.send(ctx, f"the tank was full. Nothing to do")

    @commands.command(name="consume_fuel", aliases=[])
    async def consume_fuel(self, ctx, count):
        cs = self.session_data.get_ship_curr()
        res = cs.consume_fuel(count)

        if res.count() != int(count):
            await self.send(ctx, f"not enough `fuel, refined` (`{res.count()}` tons)! `{count}` tons required")
            return 1
        else:
            await self._send_add_res(ctx, res, count)
            return 0

    @commands.command(name="refine_fuel", aliases=["refine"])
    async def refine_fuel(self, ctx):
        cs = self.session_data.get_ship_curr()
        res, t = cs.refine_fuel()

        await self.send(ctx, f"`{res.count()}` tons of fuel refined in: `{BbwUtils.conv_days_2_time(t)}`")

        await self.newday(ctx, ndays=t)

    ##################################################
    ### containers
    ##################################################
    @commands.command(name="set_world", aliases=["add_world", "set_planet", "add_planet"])
    async def set_world(self, ctx, name, uwp, zone, hex, sector=None):
        """Add a world"""
        if sector is None:
            sector = self.session_data.get_world_curr().sector()

        if name in self.session_data.charted_space():
            raise InvalidArgument(
                f"the world: `{name}` exists already! If you really want to replace it, delete it first"
            )

        w = BbwWorld(name=name, uwp=uwp, zone=zone, hex=hex, sector=sector)
        self.session_data.charted_space().add_obj(w)

        await self.send(ctx, f"The world `{name}` was successfully added to the charted space")

    @commands.command(name="del_world", aliases=["del_planet"])
    async def del_world(self, ctx, name):
        """Del world"""

        res = self.session_data.charted_space().del_obj(name=name)

        if self.session_data.world_curr() in [i.name() for i, _ in res.objs()]:
            await self.set_world_curr(ctx, name="")

        await self.send(ctx, f"The world `{name}` was successfully deleted")
        await self.charted_space(ctx)

    @commands.command(name="rename_world_curr", aliases=["rename_world", "rename_planet"])
    async def rename_world(self, ctx, new_name):
        cw = self.session_data.get_world_curr()
        self.session_data.fleet().rename_obj(name=cw, new_name=new_name)

        await self.set_world_curr(ctx, new_name)

    @commands.command(name="world_curr", aliases=["world", "planet"])
    async def world_curr(self, ctx):
        """Current world summary"""

        cw = self.session_data.get_world_curr()

        await self.send(ctx, f"current world:\n{cw.__str__(is_compact=False)}")

    @commands.command(name="set_world_curr", aliases=["set_planet_curr"])
    async def set_world_curr(self, ctx, name):
        """Set current world"""

        self.session_data.set_world_curr(name)

        await self.world_curr(ctx)

    @commands.command(name="charted_space", aliases=["galaxy"])
    async def charted_space(self, ctx):
        """charted space summary"""

        await self.send(ctx, self.session_data.charted_space().__str__(is_compact=False))

    @commands.command(name="set_world_attr", aliases=["set_world_curr_attr", "set_planet_curr_attr"])
    async def set_world_attr(self, ctx, attr_name, value):
        cw = self.session_data.get_world_curr()
        cw.set_attr(attr_name, value)

        await self.world_curr(ctx)

    ##################################################
    ### containers
    ##################################################

    @commands.command(name="container", aliases=["cont", "inv"])
    async def container(self, ctx, *args):
        cs = self.session_data.get_ship_curr()

        res = []
        if len(args) == 0:
            res = [i for i, _ in cs.containers().get_objs(type0=BbwContainer).objs()]
        else:
            if type(args[0]) is str:
                for i in args:
                    res = [i for i, _ in cs.containers().get_objs(name=i, type0=BbwContainer)]
            else:
                res = args

        s = "\n".join([i.__str__(False) for i in res])
        await self.send(ctx, s)

    @commands.command(name="get_objs", aliases=["objs", "obj"])
    async def get_objs(self, ctx, name):
        cs = self.session_data.get_ship_curr()
        c = BbwContainer(name="results:")
        for i, _ in cs.containers().get_objs(name=name).objs():
            c.add_obj(i)
        await self.container(ctx, c)

    async def _max_skill_rank_stat(self, ctx, v, l):
        if not len(l):
            await self.send(ctx, f"the skill/rank/stat is not present in the crew! max: {v}")
        else:
            await self.send(ctx, f"max: `{v}`. Crew members: `{', '.join(i.name() for i in l)}`")

    @commands.command(name="max_stat", aliases=[])
    async def max_stat(self, ctx, stat):
        cs = self.session_data.get_ship_curr()
        l = [i for i, _ in cs.containers().get_objs(name="crew").objs()]
        v, l = BbwPerson.max_stat(l, stat=stat)
        await self._max_skill_rank_stat(ctx, v, l)

    @commands.command(name="max_skill", aliases=[])
    async def max_skill(self, ctx, skill):
        cs = self.session_data.get_ship_curr()
        l = [i for i, _ in cs.containers().get_objs(name="crew").objs()]
        v, l = BbwPerson.max_skill(l, skill=skill)
        await self._max_skill_rank_stat(ctx, v, l)

    @commands.command(name="max_rank", aliases=[])
    async def max_rank(self, ctx, rank):
        cs = self.session_data.get_ship_curr()
        l = [i for i, _ in cs.containers().get_objs(name="crew").objs()]
        v, l = BbwPerson.max_rank(l, rank=rank)
        await self._max_skill_rank_stat(ctx, v, l)

    @commands.command(name="add_container", aliases=["add_cont"])
    async def add_container(self, ctx, name, capacity=float("inf"), size=0.0, cont=None):
        cs = self.session_data.get_ship_curr()
        new_container = BbwContainer(name=name, capacity=capacity, size=size)
        res = cs.containers().add_obj(obj=new_container, cont=cont)
        if res.count():
            await self.send(ctx, f"container `{name}` added to `{res.objs()[0][1].name()}`")
        else:
            await self.send(ctx, f"container `{name}` not added!")

    async def _send_add_res(self, ctx, res, count):
        dev = "\n".join(
            [f"`{i if type(i) is str else i.name()}` in: `{j if type(j) is str else j.name()}` " for i, j in res.objs()]
        )
        msg = f"affected objects: `{int(res.count())}/{int(count)}` \n{dev}"

        await self.send(ctx, msg)

    @commands.command(name="add_person", aliases=["add_passenger"])
    async def add_person(
        self, ctx, name, count=1, n_sectors=1, cont=None, cont_luggage=None, unbreakable=False, mute=False
    ):
        cs = self.session_data.get_ship_curr()
        new_person = BbwPerson.factory(name=name, n_sectors=n_sectors, count=1, only_std=True)
        new_luggage = BbwItem.factory(name=new_person.name(), count=1, only_std=True)
        with_any_tags_p = {"lowberth"} if BbwUtils.has_any_tags(new_person, "low") else {"stateroom"}
        with_any_tags_l = {"cargo"}

        if new_luggage:
            new_count = min(
                count,
                cs.containers().free_slots(
                    caps=[
                        (new_person.capacity(), cont, with_any_tags_p),
                        (new_luggage.capacity(), cont_luggage, with_any_tags_l),
                    ]
                ),
            )
            if unbreakable and new_count < count:
                count = 0
            if count == 0:
                if not mute:
                    await self.send(ctx, f"no space for the passengers or their luggage!")
                return BbwRes()

            new_luggage.set_count(count)

            res_l = cs.containers().dist_obj(
                obj=new_luggage, unbreakable=False, cont=cont_luggage, with_any_tags=with_any_tags_l
            )
            if not mute:
                await self.container(ctx, *[i for _, i in res_l.objs()])

        new_person.set_count(count)
        res_p = cs.containers().dist_obj(obj=new_person, cont=cont, unbreakable=False, with_any_tags=with_any_tags_p)
        if not mute:
            await self.container(ctx, *[i for _, i in res_p.objs()])
        return res_p

    @commands.command(name="add_item", aliases=[])
    async def add_item(
        self,
        ctx,
        name,
        count=1,
        capacity=0,
        TL=0,
        value=0,
        cont="cargo",
        unbreakable=False,
        n_sectors=1,
        mute=False,
    ):
        cs = self.session_data.get_ship_curr()
        new_item = BbwItem.factory(name=name, count=count, TL=TL, value=value, capacity=capacity, n_sectors=n_sectors)

        res = cs.containers().dist_obj(obj=new_item, cont=cont, unbreakable=unbreakable, with_any_tags={"cargo"})
        if not mute:
            await self._send_add_res(ctx, res, count)

        return res

    @commands.command(name="del_person", aliases=["del_obj", "del"])
    async def del_obj(self, ctx, name, count=float("inf"), cont=None, mute=False):
        cs = self.session_data.get_ship_curr()
        res = cs.containers().del_obj(name=name, count=count, cont=cont)

        if count:
            msg = f"deleted: `{res.count()}/{count}`"
        else:
            msg = f"deleted: `{res.count()}`"

        if not mute:
            await self._send_add_res(ctx, res, res.count())
            await self.send(ctx, msg)

        return res

    @commands.command(name="sell", aliases=[])
    async def sell(self, ctx, name, count=float("inf"), value=None, cont=None):
        res = await self.del_obj(ctx, name=name, count=count, cont=cont)
        description = f"sold: `{', '.join([i.name() for i, _ in res.objs()])}` (`{res.count()}`)"

        if value is None:
            value = sum([i.value() for i, _ in res.objs()])

        self.session_data.company().add_log_entry(value, description, self.session_data.calendar().t())
        await self.send(ctx, f"{description} for: `{value}` Cr")

    @commands.command(name="rename_person", aliases=["rename_obj", "rename_item", "rename"])
    async def rename_obj(self, ctx, name, new_name, cont=None):
        cs = self.session_data.get_ship_curr()
        res = cs.containers().rename_obj(name=name, new_name=new_name, cont=cont, only_one=True)

        await self._send_add_res(ctx, res, 1)

    @commands.command(name="set_person_attr", aliases=["set_item_attr", "set_obj_attr"])
    async def set_obj_attr(self, ctx, name, attr_name, value, cont=None):
        cs = self.session_data.get_ship_curr()
        res = cs.containers().get_objs(name=name, cont=cont, only_one=True)

        res.objs()[0][0].set_attr(attr_name, value)

        await self._send_add_res(ctx, res, 1)

    @commands.command(name="move", aliases=[])
    async def move(self, ctx, name, cont_to, count=float("inf"), cont_from=None):
        """add item to container"""
        cs = self.session_data.get_ship_curr()
        res_from = cs.containers().get_objs(name=name, cont=cont_from, only_one=True)

        old_obj, new_obj, cont_from = res_from.objs()[0][0], copy.deepcopy(res_from.objs()[0][0]), res_from.objs()[0][1]

        new_obj.set_count(min(count, old_obj.count()))
        res_to = cs.containers().add_obj(new_obj, cont=cont_to)
        old_obj_name = old_obj.name()
        cs.containers().del_obj(name=old_obj.name(), count=new_obj.count(), cont=cont_from.name())

        await self.send(ctx, f"`{old_obj_name}` moved from `{cont_from.name()}` to `{res_to.objs()[0][1].name()}`")

    ##################################################
    ### date
    ##################################################
    @commands.command(name="date", aliases=[])
    async def date(self, ctx):
        await self.send(ctx, self.session_data.calendar().__str__(is_compact=False))

    @commands.command(name="set_date", aliases=[])
    async def set_date(self, ctx, day, year):
        self.session_data.calendar().set_date(day, year)
        await self.send(ctx, "Date set successfully")
        await self.date(ctx)

    @commands.command(name="newday", aliases=["advance"])
    async def newday(self, ctx, ndays=1, travel_accounting=False):
        ndays = int(ndays)
        if abs(ndays) < 1:
            return

        await self.trip_accounting_life_support(ctx, ndays)
        await self.trip_accounting_payback(ctx, ndays)

        n_months = self.session_data.calendar().add_t(ndays)
        for i in range(n_months):
            await self.close_month(ctx)
        await self.send(ctx, f"Date advanced by {ndays}d")
        await self.date(ctx)

    ##################################################
    ### company
    ##################################################

    @commands.command(name="add_money", aliases=["cr"])
    async def add_money(self, ctx, value=0, description=""):
        if type(description) is BbwRes:
            description = f"{description.objs()[0][0].name()} ({description.count()})"

        if value:
            self.session_data.company().add_log_entry(value, description, self.session_data.calendar().t())
        await self.money(ctx, 10)

    @commands.command(name="money_status", aliases=["status", "money", "log"])
    async def money(self, ctx, log_lines=10):
        await self.send(ctx, self.session_data.company().__str__(log_lines))

    @commands.command(name="add_debt", aliases=[])
    async def add_debt(self, ctx, name, capacity, due_day, due_year, period=None, end_day=None, end_year=None):
        new_debt = BbwDebt(
            name=name,
            count=1,
            due_t=BbwCalendar.date2t(due_day, due_year),
            period=period,
            end_t=BbwCalendar.date2t(end_day, end_year),
            capacity=capacity,
        )
        self.session_data.company().debts().add_obj(new_debt)

        await self.money(ctx)

    @commands.command(name="del_debt", aliases=[])
    async def del_debt(self, ctx, name):
        self.session_data.company().debts().del_obj(name=name)

        await self.money(ctx)

    @commands.command(name="set_debt_attr", aliases=[])
    async def set_debt_attr(self, ctx, debt_name, attr_name, value):
        res = self.session_data.company().debts().get_objs(name=debt_name, only_one=True)
        res.objs()[0][0].set_attr(attr_name, value)

        await self.money(ctx)

    @commands.command(name="rename_debt", aliases=[])
    async def rename_debt(self, ctx, name, new_name):
        self.session_data.company().debts().rename_obj(name=name, new_name=new_name)

        await self.money(ctx)

    @commands.command(name="pay_debt", aliases=["pay_debts"])
    async def pay_debts(self, ctx, name=None):
        self.session_data.company().pay_debts(self.session_data.calendar().t(), name)

        await self.money(ctx)

    @commands.command(name="buy", aliases=[])
    async def buy(self, ctx, name, count=1, value=0, cont=None, capacity=0, TL=0, price_payed=None):
        res = await self.add_item(ctx, name=name, cont=cont, count=count, capacity=capacity, TL=TL, value=value)

        if price_payed is None:
            price_payed = value * count

        await self.add_money(ctx, value=-price_payed, description=res)

    @commands.command(name="pay_salaries", aliases=[])
    async def pay_salaries(self, ctx, print_recap=True):
        cs = self.session_data.get_ship_curr()
        crew = [i for i, _ in cs.containers().get_objs(name="crew").objs()]
        self.session_data.company().pay_salaries(crew, self.session_data.calendar().t())

        if print_recap:
            await self.money(ctx, 10)

    @commands.command(name="close_month", aliases=[])
    async def close_month(self, ctx):
        await self.consume_fuel(ctx, 1)
        await self.pay_salaries(ctx, False)
        await self.pay_debts(ctx)

    ##################################################
    ### wish
    ##################################################

    @commands.command(name="add_wish", aliases=[])
    async def add_wish(self, ctx, name, count=1, TL=0, value=0, capacity=0):
        new_item = BbwItem.factory(name=name, count=count, TL=TL, value=value, capacity=capacity, n_sectors=1)
        self.session_data.wishlist().add_obj(new_item)

        await self.wishlist(ctx)

    @commands.command(name="set_wish_attr", aliases=[])
    async def set_wish_attr(self, ctx, item_name, attr_name, value):
        res = self.session_data.wishlist().get_objs(name=item_name, only_one=True)
        res.objs()[0][0].set_attr(attr_name, value)

        await self.wishlist(ctx)

    @commands.command(name="del_wish", aliases=[])
    async def del_wish(self, ctx, name, count=1, mute=False):
        res = self.session_data.wishlist().del_obj(name=name, count=count)
        if not mute:
            await self._send_add_res(ctx, res, res.count())

    @commands.command(name="rename_wish", aliases=[])
    async def rename_wish(self, ctx, name, new_name):
        self.session_data.wishlist().rename_obj(name=name, new_name=new_name)

        await self.wishlist(ctx)

    @commands.command(name="wish", aliases=["wishes", "wishlist"])
    async def wishlist(self, ctx):
        await self.send(ctx, self.session_data.wishlist().__str__(is_compact=False))

    @commands.command(name="buy_wish", aliases=[])
    async def buy_wish(self, ctx, name):
        res = self.session_data.wishlist().get_objs(name=name, only_one=True)
        obj = res.objs()[0][0]
        c = obj.count()
        obj.set_count(1)
        await self.buy(
            ctx,
            obj.name(),
            count=c,
            value=obj.value(),
            cont=None,
            capacity=obj.capacity(),
            TL=obj.TL(),
            price_payed=None,
        )
        await self.del_wish(ctx, name, mute=True)
