import os
import time

from discord.ext import commands
import discord

from cogst5.company import *
from cogst5.library import Library
from cogst5.session_data import BbwSessionData
from cogst5.trade import *
from cogst5.vehicle import *
from cogst5.wishlist import *

jsonpickle.set_encoder_options("json", sort_keys=True)


class Game(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    _msg_divisor = "__                                                                          __\n"
    """Traveller 5 commands."""

    def __init__(self, bot):
        self.bot = bot
        self.library = Library()
        self.session_data = BbwSessionData()

    def save_path(self, filename: str, with_timestamp: bool = False):
        save_path = "../../" if os.getcwd() == "/home/bambleweeny" else ""
        if not filename.endswith(".json"):
            filename += ".json"

        s = f"{save_path}save/{filename}"
        if not with_timestamp:
            return s
        ts = time.gmtime()
        timestamp = time.strftime("%Y%m%d%H%M%S", ts)

        split_tup = os.path.splitext(s)

        return f"{split_tup[0]}_{timestamp}{split_tup[1]}"

    @commands.command(name="send", aliases=[])
    async def send(self, ctx, msg: str):
        """Split long messages to workaround the discord limit"""

        if type(msg) is not str:
            msg = msg.__str__()
        msg = Game._msg_divisor + msg

        # with open(f"save/debug.txt", "w") as f:
        #     f.write(msg)

        for idx, i in enumerate(BbwUtils.split_md_compatible(msg)):
            # with open(f"save/debug{idx}.txt", "w") as f:
            #     f.write(msg)
            await ctx.send(i)

    # ==== commands ====
    @commands.command(name="library_data", aliases=["library", "lib", "l"])
    async def query_library(self, ctx, *args):
        """*Query ship Library Database*

        In a universe with no faster-than-light communication, there is no Galactic Internet. Every ship therefore carries its own database of information about a wide variety of subjects: worlds, lifeforms, corporations, politics, history, *etc.* Almost all ships in Traveller have this database in the form of the **Library/0** program. The Library database is periodically updated, when the ship is in port at a Class A or Class B starport.

        `<search_term>` can be a single word, or a phrase. If there is an unambiguous partial match with an entry in the database, the Library Data for that entry will be returned. If there are multiple matching terms, a list of possible matches will be returned (try again with a more specific term from the list).
        """

        await self.send(ctx, self.library.search(" ".join(args)))

    ##################################################
    ### load/save
    ##################################################

    @commands.command(name="save")
    async def save_session_data(self, ctx, filename: str = "session_data"):
        """Save session data to a file in JSON format."""

        enc_data = jsonpickle.encode(self.session_data)
        p = self.save_path(filename)
        with open(p, "w") as f:
            json.dump(json.loads(enc_data), f, indent=2)

        p_backup = self.save_path(filename, True)
        with open(p_backup, "w") as f:
            json.dump(json.loads(enc_data), f, indent=2)

        await self.send(ctx, f"Session data saved as: {p}. Backup in: {p_backup}")

    @commands.command(name="load", aliases=["Load"])
    async def load_session_data(self, ctx, filename: str = "session_data.json"):
        """Load session data from a JSON-formatted file."""

        p = self.save_path(filename)
        with open(p, "r") as f:
            enc_data = json.dumps(json.load(f))
            self.session_data = jsonpickle.decode(enc_data)

        await self.send(ctx, f"Session data loaded from {p}.")

    @commands.command(name="get_session_data", aliases=[])
    async def get_session_data(self, ctx):
        """send session_data.json in the chat"""

        await ctx.send(file=discord.File(self.save_path("session_data.json")))

    ##################################################
    ### trade
    ##################################################

    @commands.command(name="load_passengers", aliases=[])
    async def load_passengers(self, ctx, carouse_or_broker_or_streetwise_mod: int, SOC_mod: int, w_to_name: str):
        cs = self.session_data.get_ship_curr()
        w0, w1 = self.session_data.get_worlds(w_to_name=w_to_name)
        n_sectors = BbwWorld.distance(w0, w1)

        header = ["high", "middle", "basic", "low"]
        counter = ["0/0"] * len(header)
        s = ""
        for idx, i in enumerate(header):
            person, r = BbwTrade.find_passengers(cs, carouse_or_broker_or_streetwise_mod, SOC_mod, i, w0, w1)
            s += f"{Game._msg_divisor if idx else ''}{i} passenger table modifier:\n{r}\n"
            s += f"{Game._msg_divisor}{i} passengers available: {0 if person is None else person.count()}\n"
            if person:
                res = await self.add_person(ctx, name=i, count=person.count(), n_sectors=n_sectors, mute=True)
                counter[idx] = f"{res.count()}/{person.count()}"

        await self.send(
            ctx,
            f"{s}{Game._msg_divisor}passengers"
            f" (loaded/available):\n{BbwUtils.print_table(counter, headers=header, detail_lvl=1)}\n",
        )

        self.session_data.add_log_entry(f"load passengers: {', '.join(counter)}")

    @commands.command(name="find_mail_and_freight", aliases=[])
    async def find_mail_and_freight(self, ctx, broker_or_streetwise_mod: int, SOC_mod: int, w_to_name: str):
        cs = self.session_data.get_ship_curr()
        w0, w1 = self.session_data.get_worlds(w_to_name=w_to_name)
        n_sectors = BbwWorld.distance(w0, w1)

        header = ["mail", "major", "minor", "incidental"]

        if BbwWorld.distance(w0, w1) >= 5:
            header = ["major", "minor", "incidental", "mail"]
        counter = ["0/0"] * len(header)
        s = ""
        mail_value, n_canisters = 0, 0

        def nd_tpl(item):
            tons_per_lot = 0
            if item is not None and item.count():
                tons_per_lot = int(item.capacity(is_per_obj=True))

            nd = 0 if item is None else item.count()
            return nd, tons_per_lot

        for idx, i in enumerate(header):
            if i == "mail":
                item, r, rft = BbwTrade.find_mail(cs, broker_or_streetwise_mod, SOC_mod, w0, w1)
                nd, tons_per_lot = nd_tpl(item)
                s += f"freight table modifier:\n{rft}\n"
                s += f"{Game._msg_divisor}mail table modifier (qualified if  > 0):\n{r}\n"
                s += f"{Game._msg_divisor}available mail canisters (5 tons each) (take all or nothing): {nd}\n"
            else:
                item, r = BbwTrade.find_freight(broker_or_streetwise_mod, SOC_mod, i, w0, w1)
                nd, tons_per_lot = nd_tpl(item)

                s += f"{Game._msg_divisor}{i} freight table modifier:\n{r}\n"
                s += (
                    f"{Game._msg_divisor}{i} freight lots available ({tons_per_lot} tons each) (each lot is"
                    f" unbreakable): {nd}\n"
                )

            if item is not None and item.count():
                res = await self.add_item(
                    ctx,
                    name=i,
                    count=item.count(),
                    capacity=tons_per_lot,
                    n_sectors=n_sectors,
                    unbreakable=(i == "mail"),
                    mute=True,
                )
                if i == "mail" and res.count():
                    mail_value, n_canisters = sum([i.value() for i, _ in res.objs()]), res.count()

                counter[idx] = f"{res.count()}/{item.count()}"

        s += (
            f"{Game._msg_divisor}mail and freight"
            f" (loaded/available):\n{BbwUtils.print_table(counter, headers=header, detail_lvl=1)}\n"
        )

        self.session_data.add_log_entry(f"load mail and freight: {', '.join(counter)}")
        if mail_value:
            s += f"{Game._msg_divisor}mail (`{n_canisters}` canisters): `{mail_value}` Cr\n"
            await self.add_money(
                ctx,
                mail_value,
                f"mail ({n_canisters} canisters)",
            )
        await self.send(ctx, s)

    @commands.command(name="load_ship", aliases=[])
    async def load_ship(
        self,
        ctx,
        carouse_or_broker_or_streetwise_mod: int,
        brocker_or_streetwise_mod: int,
        SOC_mod: int,
        w_to_name: str,
    ):
        # load passengers
        await self.load_passengers(ctx, carouse_or_broker_or_streetwise_mod, SOC_mod, w_to_name)

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
        for i in BbwPersonFactory._tickets.keys():
            tot += sum([i.salary_ticket() for i, _ in cs.containers().get_objs(name=i).objs()])
            await self.del_obj(ctx, name=i, mute=True)

        await self.del_obj(ctx, name="luggage, high", mute=True)
        await self.del_obj(ctx, name="luggage, middle", mute=True)

        await self.add_money(ctx, value=int(tot), description="passenger tickets")

    @commands.command(name="unload_mail", aliases=[])
    async def unload_mail(self, ctx):
        await self.send(ctx, f"unload mail")
        await self.del_obj(ctx, name="mail", mute=True)

        self.session_data.add_log_entry(f"unload mail")

    @commands.command(name="unload_freight", aliases=[])
    async def unload_freight(self, ctx):
        cs = self.session_data.get_ship_curr()
        tot = 0

        for i in ["freight, major", "freight, minor", "freight, incidental", "mail"]:
            if i != "mail":
                tot += sum([i.value() for i, _ in cs.containers().get_objs(name=i).objs()])
                await self.del_obj(ctx, name=i, mute=True)

        await self.add_money(ctx, value=int(tot), description="unload freight")

    @commands.command(name="unload_ship", aliases=[])
    async def unload(self, ctx):
        await self.unload_mail(ctx)
        await self.unload_passengers(ctx)
        await self.unload_freight(ctx)

    ##################################################
    ### spaceship
    ##################################################

    @commands.command(name="set_spaceship", aliases=["add_spaceship", "add_starship", "add_ship"])
    async def set_spaceship(
        self,
        ctx,
        name: str,
        size: float,
        capacity: float,
        type: str,
        TL: int,
        armour: int,
        m_drive: int,
        j_drive: int,
        power_plant: int,
        fuel_refiner_speed: int,
        is_streamlined: bool,
        has_fuel_scoop: bool,
        has_cargo_scoop: bool,
        has_cargo_crane: bool,
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
            has_cargo_scoop=has_cargo_scoop,
            has_cargo_crane=has_cargo_crane,
        )
        self.session_data.fleet().dist_obj(s)

        await self.send(ctx, f"The ship {name} was successfully added to the fleet.")
        await self.set_ship_curr(ctx, name)

    @commands.command(name="del_ship", aliases=[])
    async def del_ship(self, ctx, name: str):
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
    async def rename_ship(self, ctx, new_name: str):
        cs = self.session_data.get_ship_curr()

        self.session_data.fleet().rename_obj(cs.name(), new_name)

        await self.set_ship_curr(ctx, new_name)

    @commands.command(name="ship_curr", aliases=["ship"])
    async def ship_curr(self, ctx, detail_lvl: int = 1):
        """Current ship summary"""

        cs = self.session_data.get_ship_curr()

        await self.send(ctx, cs.__str__(detail_lvl=detail_lvl))

    @commands.command(name="set_ship_curr", aliases=[])
    async def set_ship_curr(self, ctx, name: str):
        """Set current ship"""

        self.session_data.set_ship_curr(name)

        await self.ship_curr(ctx)

    @commands.command(name="fleet", aliases=["ships"])
    async def fleet(self, ctx):
        """Fleet summary"""

        await self.send(ctx, self.session_data.fleet().__str__(detail_lvl=1))

    @commands.command(name="set_ship_attr", aliases=["set_ship_curr_attr"])
    async def set_ship_attr(self, ctx, attr_name: str, *args):
        cs = self.session_data.get_ship_curr()
        cs.set_attr(attr_name, *args)

        await self.ship_curr(ctx)

    @commands.command(name="m_drive", aliases=["drive_m"])
    async def m_drive(self, ctx, d_km: int = None):
        if d_km is None:
            d_km = 100 * self.session_data.get_world().d_km()

        cs = self.session_data.get_ship_curr()

        t = cs.flight_time_m_drive(d_km)

        await self.send(
            ctx, f"the m drive {cs.m_drive()} travel time to cover {d_km} km is: {BbwUtils.conv_days_2_time(t)}"
        )

        return t

    @commands.command(name="travel_m", aliases=["jump_m"])
    async def travel_m(self, ctx, d_km: int = None):
        t = await self.m_drive(ctx, d_km)
        self.session_data.add_log_entry(f"jump m: {BbwUtils.conv_days_2_time(t)}")
        await self.newday(ctx, ndays=t, travel_accounting=True)

    @commands.command(name="j_drive", aliases=["drive_j"])
    async def j_drive(self, ctx, w_to_name: str, w_from_name: str = None):
        w0, w1 = self.session_data.get_worlds(w_to_name=w_to_name, w_from_name=w_from_name)

        cs = self.session_data.get_ship_curr()
        n_sectors = BbwWorld.distance(w0, w1)
        n_jumps = math.ceil(n_sectors / cs.j_drive())
        j_drive_required_fuel = BbwSpaceShip.j_drive_required_fuel(n_sectors)
        t = BbwSpaceShip.j_drive_required_time(n_jumps)

        h = ["n sectors", "travel time (~)", "required fuel (tons)", "n jumps"]
        tab = [n_sectors, BbwUtils.conv_days_2_time(t), j_drive_required_fuel, n_jumps]
        await self.send(ctx, BbwUtils.print_table(tab, headers=h, detail_lvl=1))

        err = cs.ck_j_drive(w0, w1)
        await self.send(ctx, err)

    @commands.command(name="trip_accounting_life_support", aliases=[])
    async def trip_accounting_life_support(self, ctx, t: int):
        cs = self.session_data.get_ship_curr()
        res, life_support_costs = cs.var_life_support(t)
        await self.add_money(ctx, value=-life_support_costs, description="variable life support costs")

    @commands.command(name="trip_accounting_payback", aliases=[])
    async def trip_accounting_payback(self, ctx, t: int):
        cs = self.session_data.get_ship_curr()

        msg = f""
        crew = cs.crew()
        for i in crew:
            payback = i.trip_payback(t)

            if payback is None:
                msg += f"upp not known for `{i.name()}`. I cannot calculate the payback!\n"
            else:
                if i.reinvest():
                    self.session_data.add_log_entry(
                        f"{i.name()} reinvested the payback",
                        payback,
                    )
                msg += f"{i.name()} gets back {payback} Cr {'(reinvested)' if i.reinvest() else ''}\n"

        await self.send(ctx, msg)

    @commands.command(name="travel_j", aliases=["jump_j", "j_jump", "j_travel"])
    async def travel_j(self, ctx, w_to_name: str):
        w0, w1 = self.session_data.get_worlds(w_to_name=w_to_name)
        cs = self.session_data.get_ship_curr()
        err = cs.ck_j_drive(w0, w1)
        if len(err):
            await self.send(ctx, err)
            return

        n_sectors = BbwWorld.distance(w0, w1)
        rf = BbwSpaceShip.j_drive_required_fuel(n_sectors)

        self.session_data.add_log_entry(f"jump j: {w0.name()} -> {w1.name()}")

        await self.consume_fuel(ctx, rf)
        t = BbwSpaceShip.j_drive_required_time()
        await self.send(ctx, f"jump time: `{BbwUtils.conv_days_2_time(t)}`")
        await self.newday(ctx, ndays=t, travel_accounting=True)
        await self.set_world_curr(ctx, w_to_name)

    @commands.command(name="get_fuel", aliases=["add_fuel", "refuel", "buy_fuel"])
    async def add_fuel(self, ctx, source: str, count: float = float("inf"), value: int = None):
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
        await self.fuel(ctx)

    @commands.command(name="consume_fuel", aliases=["del_fuel", "remove_fuel"])
    async def consume_fuel(self, ctx, count: float):
        cs = self.session_data.get_ship_curr()
        res = cs.consume_fuel(count)

        await self._send_add_res(ctx, res, count)
        await self.fuel(ctx)

    @commands.command(name="refine_fuel", aliases=["refine"])
    async def refine_fuel(self, ctx):
        cs = self.session_data.get_ship_curr()
        res, t = cs.refine_fuel()

        s = f"`{res.count()}` tons of fuel refined in: `{BbwUtils.conv_days_2_time(t)}`"
        self.session_data.add_log_entry(s)
        await self.send(ctx, s)
        await self.fuel(ctx)

        await self.newday(ctx, ndays=t)

    ##################################################
    ### containers
    ##################################################
    @commands.command(name="set_world", aliases=["add_world", "set_planet", "add_planet"])
    async def set_world(self, ctx, name: str, uwp: str, zone: str, hex: str, sector=None):
        """Add a world"""

        if sector is None:
            sector = self.session_data.get_world().sector()

        if name in self.session_data.charted_space():
            raise InvalidArgument(
                f"the world: `{name}` exists already! If you really want to replace it, delete it first"
            )

        w = BbwWorld(name=name, uwp=uwp, zone=zone, hex=hex, sector=sector)
        self.session_data.charted_space().dist_obj(w)

        await self.send(ctx, f"The world `{name}` was successfully added to the charted space")

    @commands.command(name="del_world", aliases=["del_planet"])
    async def del_world(self, ctx, name: str):
        """Del world"""

        res = self.session_data.charted_space().del_obj(name=name)

        if self.session_data.world_curr() in [i.name() for i, _ in res.objs()]:
            await self.set_world_curr(ctx, name="")

        await self.send(ctx, f"The world `{name}` was successfully deleted")
        await self.charted_space(ctx)

    @commands.command(name="rename_world_curr", aliases=["rename_world", "rename_planet"])
    async def rename_world(self, ctx, new_name: str):
        cw = self.session_data.get_world()
        self.session_data.fleet().rename_obj(name=cw, new_name=new_name)

        await self.set_world_curr(ctx, new_name)

    @commands.command(name="world_curr", aliases=["world", "planet"])
    async def world_curr(self, ctx, name: str = None):
        """Current world summary"""

        cw = self.session_data.get_world(name=name)

        await self.send(ctx, cw.__str__(detail_lvl=1))

    @commands.command(name="set_world_curr", aliases=["set_planet_curr"])
    async def set_world_curr(self, ctx, name: str):
        """Set current world"""

        self.session_data.set_world_curr(name)

        await self.world_curr(ctx)

        self.session_data.add_log_entry(f"set world curr: {self.session_data.world_curr()}")

    @commands.command(name="charted_space", aliases=["galaxy"])
    async def charted_space(self, ctx):
        """charted space summary"""

        await self.send(ctx, self.session_data.charted_space().__str__(detail_lvl=1))

    @commands.command(name="set_world_attr", aliases=["set_world_curr_attr", "set_planet_curr_attr"])
    async def set_world_attr(self, ctx, attr_name: str, *args):
        cw = self.session_data.get_world()
        cw.set_attr(attr_name, *args)

        await self.world_curr(ctx)

    ##################################################
    ### containers
    ##################################################

    async def _container(self, ctx, detail_lvl: int, res):
        s = "\n".join([i.__str__(detail_lvl) for i in res])

        free_space = sum([i.free_space() for i in res])
        s += f"{Game._msg_divisor}\nfree space: `{free_space:.2f}`"
        await self.send(ctx, s)

    @commands.command(name="container", aliases=["cont", "inv"])
    async def container(self, ctx, *args):
        containers = self.session_data.get_containers()

        detail_lvl = 1
        res = BbwRes()
        if len(args) == 0:
            res += containers.get_objs(type0=BbwContainer)
        else:
            if type(args[0]) is str:
                for i in args:
                    res += containers.get_objs(name=i, type0=BbwContainer)
            else:
                detail_lvl = 2
                for i in args:
                    res += i

        await self._container(ctx, detail_lvl, [i for i, _ in res.objs()])

    @commands.command(name="fuel", aliases=[])
    async def fuel(self, ctx):
        await self.container(ctx, "fuel tank")

    @commands.command(name="crew", aliases=[])
    async def crew(self, ctx):
        await self.get_objs(ctx, "crew")

    @commands.command(name="passenger", aliases=["pax", "pass"])
    async def passenger(self, ctx):
        await self.get_objs(ctx, "passenger")

    @commands.command(name="get_objs", aliases=["objs", "obj"])
    async def get_objs(self, ctx, name: str = "", detail_lvl: int = 1):
        cs = self.session_data.get_ship_curr()
        c = [i for i, _ in cs.containers().get_objs(name=name).objs()]
        await self._container(ctx, detail_lvl, c)

    @commands.command(name="log", aliases=["ll"])
    async def get_log(self, ctx, log_lines: int = 10, name: str = "", transactions: int = 0):
        await self.send(ctx, self.session_data.log().__str__(log_lines=log_lines, name=name, transactions=transactions))

    async def _max_skill_rank_stat(self, ctx, v, l):
        if not len(l):
            await self.send(ctx, f"`{v[0]}` is not present in the crew! max: `{v[1]}`")
        else:
            await self.send(ctx, f"{v[0]} max: `{v[1]}`. Crew members: `{', '.join(i.name() for i in l)}`")

    @commands.command(name="max_stat", aliases=[])
    async def max_stat(self, ctx, stat: str):
        cs = self.session_data.get_ship_curr()
        l = cs.crew()
        v, l = BbwPerson.max_stat(l, stat=stat)
        await self._max_skill_rank_stat(ctx, v, l)

    @commands.command(name="max_skill", aliases=[])
    async def max_skill(self, ctx, skill: str):
        cs = self.session_data.get_ship_curr()
        l = cs.crew()
        v, l = BbwPerson.max_skill(l, skill=skill)
        await self._max_skill_rank_stat(ctx, v, l)

    @commands.command(name="max_rank", aliases=[])
    async def max_rank(self, ctx, rank: str):
        cs = self.session_data.get_ship_curr()
        l = cs.crew()
        v, l = BbwPerson.max_rank(l, rank=rank)
        await self._max_skill_rank_stat(ctx, v, l)

    @commands.command(name="skill", aliases=[])
    async def skill(self, ctx, skill: str):
        cs = self.session_data.get_ship_curr()
        l = cs.crew()
        s = f"People with `{skill}`:\n"
        s += "\n".join(
            [
                f"`{i.name()}`: " + ", ".join([f"`{k}`: `{v}`" for k, v in i.skill(skill)])
                for i in l
                if i.skill(skill)[0][1] >= 0
            ]
        )

        await self.send(ctx, s)

    @commands.command(name="ship_HP", aliases=["ship_hp", "hp_ship", "HP_ship", "HP", "hp", "Hp"])
    async def HP(self, ctx, v: float):
        cs = self.session_data.get_ship_curr()
        cs.set_HP(cs.HP() + v)
        await self.send(ctx, f"Hull status: `{cs.hull()}`")

    @commands.command(name="add_container", aliases=["add_cont"])
    async def add_container(
        self, ctx, name: str, capacity: float = float("inf"), size: float = 0.0, cont: str = None, conts: str = None
    ):
        containers = self.session_data.get_containers(name=conts)
        new_container = BbwContainer(name=name, capacity=capacity, size=size)
        res = containers.dist_obj(obj=new_container, cont=cont)
        if res.count():
            await self.send(ctx, f"container `{name}` added to `{res.objs()[0][1].name()}`")
        else:
            await self.send(ctx, f"container `{name}` not added!")

    async def _send_add_res(self, ctx, res, count):
        dev = "\n".join(
            [f"`{i if type(i) is str else i.name()}` in: `{j if type(j) is str else j.name()}` " for i, j in res.objs()]
        )
        msg = f"affected objects: `{res.count()}/{count}` \n{dev}"

        await self.send(ctx, msg)

    @commands.command(name="add_person", aliases=["add_passenger"])
    async def add_person(
        self,
        ctx,
        name: str,
        count: int = 1,
        salary_ticket: int = None,
        capacity: float = None,
        n_sectors: int = 1,
        cont: str = None,
        cont_luggage: str = None,
        unbreakable: bool = False,
        mute: bool = False,
    ):
        cs = self.session_data.get_ship_curr()
        try:
            new_person = BbwPersonFactory.make(
                name=name, n_sectors=n_sectors, count=count, salary_ticket=salary_ticket, capacity=capacity
            )
        except SelectionException:
            new_person = BbwPerson(name=name, count=count, salary_ticket=salary_ticket, capacity=capacity)

        new_luggage = None
        if "passenger, high" in new_person.name():
            new_luggage = BbwItemFactory.make(name="luggage, high", n_sectors=n_sectors)
        if "passenger, middle" in new_person.name():
            new_luggage = BbwItemFactory.make(name="luggage, middle", n_sectors=n_sectors)

        with_any_tags_p = {"lowberth"} if BbwUtils.has_any_tags(new_person, "low") else {"stateroom"}
        with_any_tags_l = {"cargo"}

        if new_luggage:
            new_count = min(
                count,
                cs.containers().free_slots(
                    caps=[
                        (new_person.capacity(is_per_obj=True), cont, with_any_tags_p),
                        (new_luggage.capacity(is_per_obj=True), cont_luggage, with_any_tags_l),
                    ]
                ),
            )
            if unbreakable and new_count < count:
                count = 0
            else:
                count = new_count

            if count == 0:
                if not mute:
                    await self.send(ctx, f"no space for the passengers or their luggage!")
                return BbwRes()

            new_luggage.set_count(count)

            res_l = cs.containers().dist_obj(
                obj=new_luggage, unbreakable=False, cont=cont_luggage, with_any_tags=with_any_tags_l
            )
            if not mute:
                await self._send_add_res(ctx, res_l, res_l.count())

        new_person.set_count(count)
        res_p = cs.containers().dist_obj(obj=new_person, cont=cont, unbreakable=False, with_any_tags=with_any_tags_p)
        if not mute:
            await self._send_add_res(ctx, res_p, res_p.count())
        return res_p

    @commands.command(name="del_person", aliases=["del_obj", "del", "del_item"])
    async def del_obj(
        self, ctx, name: str, count: float = float("inf"), cont: str = None, conts: str = None, mute: bool = False
    ):
        containers = self.session_data.get_containers(conts)
        res = containers.del_obj(name=name, count=count, cont=cont)

        if count:
            msg = f"deleted: `{res.count()}/{count}`"
        else:
            msg = f"deleted: `{res.count()}`"

        if not mute:
            await self._send_add_res(ctx, res, res.count())
            await self.send(ctx, msg)

        return res

    @commands.command(name="rename_person", aliases=["rename_obj", "rename_item", "rename"])
    async def rename_obj(self, ctx, name: str, new_name: str, cont: str = None, conts: str = None):
        containers = self.session_data.get_containers(conts)
        res = containers.rename_obj(name=name, new_name=new_name, cont=cont, only_one=True)

        await self._send_add_res(ctx, res, 1)

    @commands.command(name="set_obj_attr_in_cont", aliases=[])
    async def set_obj_attr_in_cont(self, ctx, name: str, attr_name: str, cont: str = None, conts: str = None, *args):
        containers = self.session_data.get_containers(conts)
        res = containers.get_objs(name=name, cont=cont, only_one=True, self_included=True)

        res.objs()[0][0].set_attr(attr_name, *args)

        await self._send_add_res(ctx, res, 1)

    @commands.command(name="set_person_attr", aliases=["set_item_attr", "set_obj_attr"])
    async def set_obj_attr(self, ctx, name: str, attr_name: str, *args):
        await self.set_obj_attr_in_cont(ctx, name, attr_name, None, None, *args)

    @commands.command(name="move", aliases=[])
    async def move(
        self,
        ctx,
        name: str,
        cont_to: str,
        count: float = float("inf"),
        cont_from: str = "cargo",
        conts_from: str = None,
        conts_to=None,
    ):
        """add item to container
        conts_from and conts_to are the super containers that contain the containers that need to do the job.

        Example: cs.containers()
        None means the container of the ship
        """
        conts_from, conts_to = self.session_data.get_containers(conts_from), self.session_data.get_containers(conts_to)

        res = conts_from.del_obj(name=name, count=count, cont=cont_from)
        if res.count() == 0:
            raise SelectionException(f"object `{name}` not found in `{cont_from}`")

        for i, _ in res.objs():
            res_to = conts_to.dist_obj(i, cont=cont_to)
            await self._send_add_res(ctx, res_to, count)

            if i.count() > res_to.count():
                i.set_count(i.count() - res_to.count())
                res_to = conts_from.dist_obj(i, cont=cont_from)
                await self._send_add_res(ctx, res_to, count)

    @commands.command(
        name="move_vip", aliases=["move_to_world", "move_from_world", "move_to_planet", "move_from_planet"]
    )
    async def move_vip(self, ctx, name: str, world_to: str = None, world_from: str = None):
        """add person to world"""
        cs = self.session_data.get_ship_curr()

        if world_from is None:
            from_c = cs.containers()
        else:
            from_c = self.session_data.charted_space().get_objs(name=world_from, only_one=True).objs()[0][0].people()

        if world_to is None:
            to_c = self.session_data.get_world().people()
        else:
            to_c = self.session_data.charted_space().get_objs(name=world_to, only_one=True).objs()[0][0].people()

        res = from_c.del_obj(name=name, type0=BbwPerson)
        if res.count() == 0:
            from_c, to_c = to_c, from_c
            res = from_c.del_obj(name=name, type0=BbwPerson)

        for i, _ in res.objs():
            with_any_tags_p = {"lowberth", "people"} if BbwUtils.has_any_tags(i, "low") else {"stateroom", "people"}
            res_to = to_c.dist_obj(i, with_any_tags=with_any_tags_p)
            await self._send_add_res(ctx, res_to, res_to.count())

        if res.count() == 0:
            await self.send(ctx, f"person {name} not found neither in {from_c.name()} nor in {to_c.name()}")

    ##################################################
    ### date
    ##################################################
    @commands.command(name="date", aliases=[])
    async def date(self, ctx):
        await self.send(ctx, self.session_data.calendar().__str__(detail_lvl=1))

    @commands.command(name="set_date", aliases=[])
    async def set_date(self, ctx, day: int, year: int):
        self.session_data.calendar().set_date(day, year)
        await self.send(ctx, "Date set successfully")
        await self.date(ctx)

        self.session_data.add_log_entry(f"set date")

    @commands.command(name="newday", aliases=["advance"])
    async def newday(self, ctx, ndays: int = 1, msg: str = "", travel_accounting: bool = False):
        ndays = int(ndays)
        if abs(ndays) < 1:
            return

        if travel_accounting:
            await self.trip_accounting_life_support(ctx, ndays)
            await self.trip_accounting_payback(ctx, ndays)

        n_months = BbwCalendar(self.session_data.calendar().t()).add_t(ndays)

        for i in range(n_months):
            await self.close_month(ctx)

        self.session_data.calendar().add_t(ndays)
        await self.send(ctx, f"Date advanced by {ndays}d")
        await self.date(ctx)

        self.session_data.add_log_entry(f"advance {ndays} days: {msg}")

    ##################################################
    ### company
    ##################################################

    @commands.command(name="add_money", aliases=["cr"])
    async def add_money(self, ctx, value: int = 0, description: str = "", is_mute: bool = False):
        if type(description) is BbwRes:
            description = f"{description.objs()[0][0].name()} ({description.count()})"

        self.session_data.add_log_entry(description, value)
        msg = f"{description}: `{value}` Cr"
        if not is_mute:
            await self.send(ctx, msg)
        return msg

    @commands.command(name="money_status", aliases=["status", "money"])
    async def money(self, ctx, detail_lvl: int = 0):
        await self.send(ctx, self.session_data.company().__str__(detail_lvl=detail_lvl))

    @commands.command(name="add_debt", aliases=[])
    async def add_debt(
        self,
        ctx,
        name: str,
        capacity: float,
        due_day: int,
        due_year: int,
        period: int = None,
        end_day: int = None,
        end_year: int = None,
    ):
        new_debt = BbwDebt(
            name=name,
            count=1,
            due_t=BbwCalendar.date2t(due_day, due_year),
            period=period,
            end_t=BbwCalendar.date2t(end_day, end_year),
            capacity=capacity,
        )
        self.session_data.company().debts().dist_obj(new_debt)

        await self.money(ctx, 1)

    @commands.command(name="del_debt", aliases=[])
    async def del_debt(self, ctx, name: str):
        self.session_data.company().debts().del_obj(name=name)

        await self.money(ctx, 1)

    @commands.command(name="set_debt_attr", aliases=[])
    async def set_debt_attr(self, ctx, debt_name: str, attr_name: str, *args):
        res = self.session_data.company().debts().get_objs(name=debt_name, only_one=True)
        res.objs()[0][0].set_attr(attr_name, *args)

        await self.money(ctx, 1)

    @commands.command(name="rename_debt", aliases=[])
    async def rename_debt(self, ctx, name: str, new_name: str):
        self.session_data.company().debts().rename_obj(name=name, new_name=new_name)

        await self.money(ctx, 1)

    @commands.command(name="pay_debt", aliases=["pay_debts"])
    async def pay_debts(self, ctx, name: str = None):
        self.session_data.company().pay_debts(self.session_data.log(), self.session_data.calendar().t(), name)

        await self.send(ctx, "debts payed")

    @commands.command(name="pay_docking_fees", aliases=["docking", "pay_docking"])
    async def pay_docking_fees(self, ctx, value: int = None):
        cw = self.session_data.get_world()

        if value is not None:
            cw.set_docking_fee(value)

        value = cw.docking_fee()

        await self.add_money(ctx, value=-value, description=f"docking fee")

    async def _add_item(
        self,
        ctx,
        name: str,
        count: int = 1,
        capacity: float = None,
        TL: int = None,
        value: int = None,
        cont: str = "cargo",
        unbreakable: bool = False,
        n_sectors: int = 1,
        mute: bool = False,
    ):
        try:
            new_item = BbwItemFactory.make(
                name=name, count=count, TL=TL, value=value, capacity=capacity, n_sectors=n_sectors
            )
        except SelectionException:
            new_item = BbwItem(name=name, count=count, TL=TL, value=value, capacity=capacity)

        cs = self.session_data.get_ship_curr()
        res = cs.containers().dist_obj(obj=new_item, cont=cont, unbreakable=unbreakable)

        if not mute:
            await self._send_add_res(ctx, res, count)

        return res

    @commands.command(name="add_obj", aliases=["add_item"])
    async def add_item(
        self,
        ctx,
        name: str,
        count: int = 1,
        capacity: float = None,
        TL: int = None,
        value: int = None,
        cont: str = "cargo",
        conts: str = None,
        n_sectors: int = 1,
        unbreakable: bool = False,
        mute: bool = False,
    ):
        return await self.buy(
            ctx,
            name=name,
            count=count,
            price_multi=0,
            n_sectors=n_sectors,
            capacity=capacity,
            TL=TL,
            value=value,
            cont=cont,
            conts=conts,
            unbreakable=unbreakable,
            mute=mute,
        )

    @commands.command(name="buy", aliases=[])
    async def buy(
        self,
        ctx,
        name: str,
        count: int = 1,
        price_multi: float = 1.0,
        capacity: float = None,
        TL: int = None,
        value: int = None,
        n_sectors: int = 1,
        cont: str = "cargo",
        conts: str = None,
        unbreakable=False,
        mute: bool = False,
    ):
        try:
            new_item = BbwItemFactory.make(
                name=name, count=count, TL=TL, value=value, capacity=capacity, n_sectors=n_sectors
            )
        except SelectionException:
            new_item = BbwItem(name=name, count=count, TL=TL, value=value, capacity=capacity)

        containers = self.session_data.get_containers(conts)

        free_slots = containers.free_slots(
            caps=[
                (new_item.capacity(is_per_obj=True), cont, {}),
            ]
        )

        if free_slots == 0 or (unbreakable and new_item.count() > free_slots):
            if not mute:
                await self.send(ctx, f"No space!")
            return BbwRes()

        new_item.set_count(min(new_item.count(), free_slots))

        price_payed = int(new_item.value() * price_multi)
        description = f"{new_item.name()} ({new_item.count()})"
        if price_payed != 0:
            await self.add_money(ctx, value=-price_payed, description=f"buy: {description}")
        else:
            self.session_data.add_log_entry(f"add item: {description}")

        res = containers.dist_obj(obj=new_item, cont=cont)

        if not mute:
            await self._send_add_res(ctx, res, res.count())

        return res

    @commands.command(name="sell", aliases=[])
    async def sell(
        self, ctx, name: str, count: float = float("inf"), price_multi: float = 1.0, cont: str = None, conts: str = None
    ):
        res = await self.del_obj(ctx, name=name, count=count, cont=cont, conts=conts)

        description = f"sell: {', '.join(set([i.name() for i, _ in res.objs()]))} ({res.count()})"

        price_payed = res.value() * price_multi

        await self.add_money(ctx, value=price_payed, description=description)

    @commands.command(name="st", aliases=["spt"])
    async def speculative_trading(self, ctx, w_to_name: str, supplier: str = None, w_from_name: str = None):
        w0, w1 = self.session_data.get_worlds(w_to_name=w_to_name, w_from_name=w_from_name)
        cs = self.session_data.get_ship_curr()

        h, t = BbwTrade.optimize_st(w0, w1, cs, supplier)
        sort_idx = 3
        t = sorted([i for i in t if i[4] > 5000], key=lambda x: -x[sort_idx])

        s = (
            f"speculative trading options buying from `{w0.name()}` and selling in `{w1.name()}` (sorted by"
            f" {h[sort_idx]}):\n"
        )
        s += BbwUtils.print_table(t=t, headers=h, detail_lvl=1, tablefmt="fancy_grid")

        await self.send(ctx, s)

    @commands.command(name="trade_st", aliases=["trade"])
    async def get_deal_st(self, ctx, broker_skill: int, name: str, roll: str = "3d6"):
        w = self.session_data.get_world()

        buy_multi, buy_roll, sell_multi, sell_roll = BbwTrade.get_deal_st(
            name=name, broker=broker_skill, w=w, roll=roll
        )
        s = f"buy: `{int(buy_multi*10000)/100}%` {buy_roll}\n"
        s += f"sell: `{int(sell_multi * 10000)/100}%` {sell_roll}"

        await self.send(ctx, s)

    @commands.command(name="add_supplier", aliases=[])
    async def add_supplier(self, ctx, name: str):
        w = self.session_data.get_world()
        supp = BbwSupplier(name=name)
        res = w.suppliers().dist_obj(supp)
        await self._send_add_res(ctx, res, res.count())

    @commands.command(name="del_supplier", aliases=[])
    async def del_supplier(self, ctx, name: str):
        w = self.session_data.get_world()
        res = w.suppliers().del_obj(name)
        await self._send_add_res(ctx, res, res.count())

    @commands.command(name="refresh_supplier_inventory", aliases=["gen_supply"])
    async def refresh_supplier_inventory(self, ctx, name: str = ""):
        w = self.session_data.get_world()
        w.set_supply(BbwTrade, self.session_data.calendar().t(), name)
        await self.world_curr(ctx)

    @commands.command(name="pay_salaries", aliases=[])
    async def pay_salaries(self, ctx, print_recap: bool = True):
        cs = self.session_data.get_ship_curr()
        crew = [i for i, _ in cs.containers().get_objs(name="crew").objs()]
        self.session_data.company().pay_salaries(crew, self.session_data.log(), self.session_data.calendar().t())

        if print_recap:
            await self.money(ctx, 10)

    @commands.command(name="close_month", aliases=[])
    async def close_month(self, ctx):
        self.session_data.add_log_entry("close month")
        await self.consume_fuel(ctx, 1)
        await self.pay_salaries(ctx, False)
        await self.pay_debts(ctx)

    ##################################################
    ### wish
    ##################################################

    @commands.command(name="add_wish", aliases=[])
    async def add_wish(self, ctx, name: str, capacity: float = None, TL: int = None, value: int = None):
        try:
            new_item = BbwItemFactory.make(name=name, count=1, TL=TL, value=value, capacity=capacity)
        except SelectionException:
            new_item = BbwItem(name=name, count=1, TL=TL, value=value, capacity=capacity)
        self.session_data.wishlist().dist_obj(new_item)

        await self.wishlist(ctx)

    @commands.command(name="set_wish_attr", aliases=[])
    async def set_wish_attr(self, ctx, item_name: str, attr_name: str, value: int):
        res = self.session_data.wishlist().get_objs(name=item_name, only_one=True)
        res.objs()[0][0].set_attr(attr_name, value)

        await self.wishlist(ctx)

    @commands.command(name="del_wish", aliases=[])
    async def del_wish(self, ctx, name: str, count: float = float("inf"), mute: bool = False):
        res = self.session_data.wishlist().del_obj(name=name, count=float(count))
        if not mute:
            await self._send_add_res(ctx, res, res.count())

    @commands.command(name="rename_wish", aliases=[])
    async def rename_wish(self, ctx, name: str, new_name: str):
        self.session_data.wishlist().rename_obj(name=name, new_name=new_name)

        await self.wishlist(ctx)

    @commands.command(name="wish", aliases=["wishes", "wishlist"])
    async def wishlist(self, ctx, name: str = ""):
        c = BbwWishlist(name="wishes:")
        for i, _ in self.session_data.wishlist().get_objs(name=name).objs():
            c.dist_obj(i)
        await self._container(ctx, 2, [c])

    @commands.command(name="buy_wish", aliases=[])
    async def buy_wish(self, ctx, name: str, count: int = 1, price_multi: float = 1.0, erase_wish: bool = False):
        obj = copy.deepcopy(self.session_data.wishlist().get_objs(name=name, only_one=True).objs()[0][0])

        await self.buy(
            ctx,
            name=obj.name(),
            count=count,
            price_multi=price_multi,
            value=obj.value(is_per_obj=True),
            capacity=obj.capacity(is_per_obj=True),
            TL=obj.TL(),
        )
        if erase_wish:
            await self.del_wish(ctx, name)


def setup(bot):
    bot.add_cog(Game(bot))
