import os
import time

from discord.ext import commands
import discord
import itertools

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

    """Traveller 5 commands."""

    def __init__(self, bot):
        self.bot = bot
        self.library = Library()
        self.session_data = BbwSessionData()

    def save_path(self, filename: str, with_timestamp: bool = False):
        """Save status to file ana backup with date"""
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
        """Send message in chat

        Split long ones to workaround the discord limit
        """

        if type(msg) is not str:
            msg = msg.__str__()
        msg = BbwUtils._msg_divisor + msg

        # with open(f"save/debug.txt", "w") as f:
        #     f.write(msg)

        for idx, i in enumerate(BbwUtils.split_md_compatible(msg)):
            # with open(f"save/debug{idx}.txt", "w") as f:
            #     f.write(msg)
            await ctx.send(i)

    # ==== commands ====
    @commands.command(name="library_data", aliases=["library", "lib", "l"])
    async def query_library(self, ctx, *args):
        """Query ship's Library Database

        In a universe with no faster-than-light communication, there is no Galactic Internet. Every ship therefore carries its own database of information about a wide variety of subjects: worlds, lifeforms, corporations, politics, history, *etc.* Almost all ships in Traveller have this database in the form of the **Library/0** program. The Library database is periodically updated, when the ship is in port at a Class A or Class B starport.

        `<search_term>` can be a single word, or a phrase. If there is an unambiguous partial match with an entry in the database, the Library Data for that entry will be returned. If there are multiple matching terms, a list of possible matches will be returned (try again with a more specific term from the list).
        """

        await self.send(ctx, self.library.search(" ".join(args)))

    ##################################################
    ### load/save
    ##################################################

    @commands.command(name="save")
    async def save_session_data(self, ctx, filename: str = "session_data"):
        """Save session data to a file in JSON format"""

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
        """Load session data from a JSON-formatted file"""

        p = self.save_path(filename)
        with open(p, "r") as f:
            enc_data = json.dumps(json.load(f))
            self.session_data = jsonpickle.decode(enc_data)

        await self.send(ctx, f"Session data loaded from {p}.")

    @commands.command(name="get_session_data", aliases=[])
    async def get_session_data(self, ctx):
        """Send session_data.json in the chat"""

        await ctx.send(file=discord.File(self.save_path("session_data.json")))

    ##################################################
    ### trade
    ##################################################

    @commands.command(name="load_passengers", aliases=[])
    async def load_passengers(self, ctx, carouse_or_broker_or_streetwise_mod: int, SOC_mod: int, w_to_name: str):
        """Embark passengers

        Order: high -> medium -> basic -> low"""
        cs = self.session_data.get_ship_curr()
        w0, w1 = self.session_data.get_worlds(w_to_name=w_to_name)
        n_sectors = BbwWorld.distance(w0, w1)

        header = ["high", "middle", "basic", "low"]
        counter = ["0/0"] * len(header)
        s = ""
        for idx, i in enumerate(header):
            person, r = BbwTrade.find_passengers(cs, carouse_or_broker_or_streetwise_mod, SOC_mod, i, w0, w1)

            s += f"{BbwUtils._msg_divisor if idx else ''}{i} passenger table modifier:\n{r}\n"
            s += f"{BbwUtils._msg_divisor}{i} passengers available: {0 if person is None else person.count()}\n"
            if person is not None:
                res = await self.add_person(ctx, name=i, count=person.count(), n_sectors=n_sectors, mute=True)
                counter[idx] = f"{res.count()}/{person.count()}"

        await self.send(
            ctx,
            f"{s}{BbwUtils._msg_divisor}passengers"
            f" (loaded/available):\n{BbwUtils.print_table(counter, headers=header, detail_lvl=1)}\n",
        )

        self.session_data.add_log_entry(f"load passengers: {', '.join(counter)}")

    @commands.command(name="find_mail_and_freight", aliases=[])
    async def find_mail_and_freight(self, ctx, broker_or_streetwise_mod: int, SOC_mod: int, w_to_name: str):
        """Embark mail and cargo

        Priority: mail -> major freight -> minor freight -> incidental freight
        Exception: for long jumps (>5) mail loses priority and becomes the last resort"""
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
            value_per_lot = 0
            if item is not None and item.count():
                tons_per_lot = int(item.capacity(is_per_obj=True))
                value_per_lot = int(item.value(is_per_obj=True))

            nd = 0 if item is None else item.count()
            return nd, tons_per_lot, value_per_lot

        for idx, i in enumerate(header):
            if i == "mail":
                item, r, rft = BbwTrade.find_mail(cs, broker_or_streetwise_mod, SOC_mod, w0, w1)

                nd, tons_per_lot, value_per_lot = nd_tpl(item)
                s += f"freight table modifier:\n{rft}\n"
                s += f"{BbwUtils._msg_divisor}mail table modifier (qualified if  > 0):\n{r}\n"
                s += f"{BbwUtils._msg_divisor}available mail canisters (5 tons each) (take all or nothing): {nd}\n"
            else:
                item, r = BbwTrade.find_freight(broker_or_streetwise_mod, SOC_mod, i, w0, w1)
                nd, tons_per_lot, value_per_lot = nd_tpl(item)

                s += f"{BbwUtils._msg_divisor}{i} freight table modifier:\n{r}\n"
                s += (
                    f"{BbwUtils._msg_divisor}{i} freight lots available ({tons_per_lot} tons each) (each lot is"
                    f" unbreakable): {nd}\n"
                )

            if item is not None and item.count():
                res = await self.add_item(
                    ctx,
                    name=i,
                    count=item.count(),
                    capacity=tons_per_lot,
                    value=value_per_lot,
                    n_sectors=n_sectors,
                    unbreakable=(i == "mail"),
                    mute=True,
                )
                if i == "mail" and res.count():
                    mail_value, n_canisters = sum([i.value() for i, _ in res.objs()]), res.count()

                counter[idx] = f"{res.count()}/{item.count()}"

        s += (
            f"{BbwUtils._msg_divisor}mail and freight"
            f" (loaded/available):\n{BbwUtils.print_table(counter, headers=header, detail_lvl=1)}\n"
        )

        self.session_data.add_log_entry(f"load mail and freight: {', '.join(counter)}")
        if mail_value:
            s += f"{BbwUtils._msg_divisor}mail (`{n_canisters}` canisters): `{mail_value}` Cr\n"
            await self.money(
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
        """Fill the ship with freight, mail and passengers"""

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
        """Unload passengers and get paid"""
        cs = self.session_data.get_ship_curr()
        tot = 0
        for i in BbwPersonFactory._tickets.keys():
            tot += sum([i.salary_ticket() for i in cs.get_objs(name=i)])
            await self.del_obj(ctx, name=i, mute=True)

        await self.del_obj(ctx, name="luggage, high", mute=True)
        await self.del_obj(ctx, name="luggage, middle", mute=True)

        await self.money(ctx, value=int(tot), description="passenger tickets")

    @commands.command(name="unload_mail", aliases=[])
    async def unload_mail(self, ctx):
        """Eject mail in space (payment on loading)"""
        await self.send(ctx, f"unload mail")
        await self.del_obj(ctx, name="mail", mute=True)

        self.session_data.add_log_entry(f"unload mail")

    @commands.command(name="unload_freight", aliases=[])
    async def unload_freight(self, ctx):
        """Unload freight and get paid"""
        cs = self.session_data.get_ship_curr()
        tot = 0

        for i in ["freight, major", "freight, minor", "freight, incidental", "mail"]:
            if i != "mail":
                tot += sum([i.value() for i in cs.get_objs(name=i)])
                await self.del_obj(ctx, name=i, mute=True)

        await self.money(ctx, value=int(tot), description="unload freight")

    @commands.command(name="unload_ship", aliases=[])
    async def unload(self, ctx):
        """Unload passengers, mail and freight and get paid for passengers and freight"""
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
        """Rename ship"""
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
        """Set current ship among the ones already registered"""

        self.session_data.set_ship_curr(name)

        await self.ship_curr(ctx)

    @commands.command(name="fleet", aliases=["ships"])
    async def fleet(self, ctx):
        """Fleet summary"""

        await self.send(ctx, self.session_data.fleet().__str__(detail_lvl=1))

    @commands.command(name="set_ship_attr", aliases=["set_ship_curr_attr"])
    async def set_ship_attr(self, ctx, attr_name: str, *args):
        """Set an attribute of the current ship"""
        cs = self.session_data.get_ship_curr()
        cs.set_attr(attr_name, *args)

        await self.ship_curr(ctx)

    @commands.command(name="drive_m", aliases=["m_drive"])
    async def m_drive(self, ctx, d_km: int = None):
        """Compute the flight time with the m_drive

        No d_km inserted means flight time to reach jumping distance"""
        if d_km is None:
            d_km = 100 * self.session_data.get_world().d_km()

        cs = self.session_data.get_ship_curr()

        t = cs.flight_time_m_drive(d_km)

        await self.send(
            ctx, f"the m drive {cs.m_drive()} travel time to cover {d_km} km is: {BbwUtils.conv_days_2_time(t)}"
        )

        return t

    @commands.command(name="jump_m", aliases=["travel_m"])
    async def travel_m(self, ctx, d_km: int = None):
        """As drive_m but we really do the trip"""
        t = await self.m_drive(ctx, d_km)
        self.session_data.add_log_entry(f"jump m: {BbwUtils.conv_days_2_time(t)}")
        await self.newday(ctx, ndays=t, travel_accounting=True)

    @commands.command(name="drive_j", aliases=["j_drive"])
    async def j_drive(self, ctx, w_to_name: str, w_from_name: str = None):
        """Compute the flight time with the j_drive

        No w_from_name inserted means that we move from current planet"""
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

    @commands.command(name="jump_j", aliases=["travel_j", "j_jump", "j_travel"])
    async def travel_j(self, ctx, w_to_name: str):
        """As drive_j but we really do the trip"""
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

    @commands.command(name="trip_accounting_life_support", aliases=[])
    async def trip_accounting_life_support(self, ctx, t: int):
        """Do the accounting for the life support"""
        cs = self.session_data.get_ship_curr()
        res, life_support_costs = cs.var_life_support(t)
        await self.money(ctx, value=-life_support_costs, description="variable life support costs")

    @commands.command(name="trip_accounting_payback", aliases=[])
    async def trip_accounting_payback(self, ctx, t: int):
        """Do the accounting for the payback

        Our life-style expenses are refunded for the duration of the trip (since we cannot spend money in during a jump).
        It can be automatically reinvested in the company (so we do not "forget" about this money)
        """
        cs = self.session_data.get_ship_curr()

        msg = f""
        crew = cs.get_objs("crew")
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

    @commands.command(name="refuel", aliases=["add_fuel", "get_fuel", "buy_fuel"])
    async def add_fuel(self, ctx, source: str, count: float = float("inf"), value: int = None):
        """Refuel

        Possible sources: gas_giant, planet, world, refined, unrefined. (planet, world mean that we scoop from the ocean)
        """
        cs = self.session_data.get_ship_curr()
        res, cost = cs.add_fuel(source=source, count=count)

        if res.count():
            t = d20.roll(f"1d6").total / 24
            await self.send(ctx, f"refueling time is: {BbwUtils.conv_days_2_time(t)}")

            if value is None:
                value = cost
            if value:
                await self.money(ctx, value=-value, description=res)
        else:
            await self.send(ctx, f"the tank was full. Nothing to do")
        await self.fuel(ctx)

    @commands.command(name="del_fuel", aliases=["consume_fuel", "remove_fuel"])
    async def consume_fuel(self, ctx, count: float):
        """Del fuel

        Only refined fuel can be consumed (for now)
        """
        cs = self.session_data.get_ship_curr()
        res = cs.consume_fuel(count)

        await self._send_add_res(ctx, res, count)
        await self.fuel(ctx)

    @commands.command(name="refine_fuel", aliases=["refine"])
    async def refine_fuel(self, ctx):
        """Activate refinery"""
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
    @commands.command(name="add_world", aliases=["set_planet", "add_planet"])
    async def set_world(self, ctx, name: str, uwp: str, zone: str, hex: str, sector=None):
        """Add a world to the galaxy"""

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

    @commands.command(name="rename_world", aliases=["rename_planet"])
    async def rename_world(self, ctx, name: str, new_name: str):
        """Rename world"""
        self.session_data.charted_space().rename_obj(name=name, new_name=new_name)

        await self.set_world_curr(ctx, new_name)

    @commands.command(name="world_curr", aliases=["world", "planet"])
    async def world_curr(self, ctx, name: str = None):
        """Current world summary"""

        cw = self.session_data.get_world(name=name)

        await self.send(ctx, cw.__str__(detail_lvl=1))

    @commands.command(name="set_world_curr", aliases=["set_planet_curr", "set_world"])
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
        """Set world attribute"""
        cw = self.session_data.get_world()
        cw.set_attr(attr_name, *args)

        await self.world_curr(ctx)

    async def _container(self, ctx, detail_lvl: int, res):
        s = ""
        s += res.__str__(detail_lvl)

        free_space = sum([i.free_space() for i in res])
        s += f"{BbwUtils._msg_divisor}\nfree space: `{BbwUtils.pf(free_space)}` t"
        if len(res) and "room" in res[0].name():
            s += f" ({BbwUtils.pf(int(free_space/2)/2)} cabins)"
        await self.send(ctx, s)

    @commands.command(name="fuel", aliases=[])
    async def fuel(self, ctx):
        """Fuel tank summery"""
        cs = self.session_data.get_ship_curr()

        await self._container(ctx, 1, cs.get_objs("fuel tank"))

    @commands.command(name="crew", aliases=[])
    async def crew(self, ctx):
        """Crew summery"""
        await self.get_objs(ctx, "crew")

    @commands.command(name="passenger", aliases=["pax", "pass"])
    async def passenger(self, ctx):
        """Passenger summary"""
        await self.get_objs(ctx, "passenger")

    @commands.command(name="get_objs", aliases=["objs", "obj"])
    async def get_objs(self, ctx, name: str = "", detail_lvl: int = 1, cont: str = None):
        """Get a summary of all the objects on the ship that match the name

        cont: restrict the search to the container cont
        detail_lvl: higher number, more details
        """
        cs = self.session_data.get_ship_curr()
        if cont:
            cs = cs.get_objs(name=cont, only_one=True)[0]

        c = cs.get_objs(name=name)
        await self._container(ctx, detail_lvl, c)

    @commands.command(name="log", aliases=["ll"])
    async def get_log(self, ctx, log_lines: int = 10, name: str = "", transactions: int = 0):
        """Return the ship's log

        log_lines: number of lines displayed
        name: filter the log with a matching name
        transactions: 0 -> all, 1-> only transactions, 2-> no transactions
        """
        await self.send(ctx, self.session_data.log().__str__(log_lines=log_lines, name=name, transactions=transactions))

    async def _max_skill_rank_stat(self, ctx, skill, v, l):
        if not len(l):
            await self.send(ctx, f"`{skill}` is not present in the crew! max: `{v}`")
        else:
            await self.send(ctx, f"`{skill}` max: `{v}`. Crew members: {', '.join(f'`{i.name()}`' for i in l)}")

    @commands.command(name="max_stat", aliases=[])
    async def max_stat(self, ctx, stat: str):
        """Get the max of the stat among the crew"""
        cs = self.session_data.get_ship_curr()
        l = cs.get_objs("crew")

        stat = stat.upper()
        v, l = BbwPerson.max_stat(l, stat=stat)
        await self._max_skill_rank_stat(ctx, stat, v[0][0], l)

    @commands.command(name="max_skill", aliases=[])
    async def max_skill(self, ctx, skill: str):
        """Get the max of the skill among the crew"""
        cs = self.session_data.get_ship_curr()
        l = cs.get_objs("crew")
        v, l = BbwPerson.max_skill(l, skill=skill)
        await self._max_skill_rank_stat(ctx, v[0], v[1], l)

    @commands.command(name="max_rank", aliases=[])
    async def max_rank(self, ctx, rank: str):
        """Get the max of the rank among the crew"""
        cs = self.session_data.get_ship_curr()
        l = cs.get_objs("crew")
        v, l = BbwPerson.max_rank(l, rank=rank)
        await self._max_skill_rank_stat(ctx, v[0], v[1], l)

    @commands.command(name="check", aliases=["skill_check", "ck"])
    async def skill_check(self, ctx, name: str, skill: str, custom: int = 0, chosen_stat: str = None):
        """Perform a skill check

        name: crew member that performs the check
        skill: skill name (ex: "art, holography")
        custom: additional custom modifiers to add
        chosen_stat: set this to perform a custom skill check based on this stat
        """
        cs = self.session_data.get_ship_curr()
        person = cs.get_objs(name=name, with_all_tags={"crew"}, only_one=True)[0]
        await self.send(ctx, person.skill_check(skill, custom=custom, chosen_stat=chosen_stat))

    @commands.command(name="ship_HP", aliases=["ship_hp", "hp_ship", "HP_ship", "HP", "hp", "Hp"])
    async def HP(self, ctx, v: float):
        """Get ship's Health Points (HP)"""
        cs = self.session_data.get_ship_curr()
        cs.set_HP(cs.HP() + v)
        await self.send(ctx, f"Hull status: `{cs.hull()}`")

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
        cont: str = "room",
        cont_luggage: str = None,
        unbreakable: bool = False,
        mute: bool = False,
    ):
        """Add person to the stateroom"""
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

        if new_luggage is not None:
            new_count = min(
                count,
                cs.free_slots(
                    caps=[
                        (new_person, cont, with_any_tags_p),
                        (new_luggage, cont_luggage, with_any_tags_l),
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

            res_l = cs.dist_obj(obj=new_luggage, unbreakable=False, cont=cont_luggage, with_any_tags=with_any_tags_l)
            if not mute:
                await self._send_add_res(ctx, res_l, res_l.count())

        new_person.set_count(count)
        res_p = cs.dist_obj(obj=new_person, cont=cont, unbreakable=False, with_any_tags=with_any_tags_p)
        if not mute:
            await self._send_add_res(ctx, res_p, res_p.count())
        return res_p

    @commands.command(name="del_person", aliases=["del_obj", "del", "del_item"])
    async def del_obj(self, ctx, name: str, count: float = float("inf"), cont: str = None, mute: bool = False):
        """Delete object

        name: what?
        count: how many?
        cont: from which container?
        mute: do not comment about it
        """
        cs = self.session_data.get_ship_curr()
        res = cs.del_obj(name=name, count=count, cont=cont)

        if count:
            msg = f"deleted: `{res.count()}/{count}`"
        else:
            msg = f"deleted: `{res.count()}`"

        if not mute:
            await self._send_add_res(ctx, res, res.count())
            await self.send(ctx, msg)

        return res

    @commands.command(name="rename_person", aliases=["rename_obj", "rename_item", "rename"])
    async def rename_obj(self, ctx, name: str, new_name: str, cont: str = None):
        """Rename object

        Containers are updated automatically
        """
        cs = self.session_data.get_ship_curr()
        res = cs.rename_obj(name=name, new_name=new_name, cont=cont, only_one=True)

        await self._send_add_res(ctx, res, 1)

    @commands.command(name="set_obj_attr_in_cont", aliases=["set_item_attr_in_cont"])
    async def set_obj_attr_in_cont(self, ctx, name: str, cont: str, attr_name: str, *args):
        """Set an object attribute in a container"""
        cs = self.session_data.get_ship_curr()
        res = cs.get_objs(name=name, cont=cont, only_one=True, self_included=True)

        res[0].set_attr(attr_name, *args)

        await self._send_add_res(ctx, res, 1)

    @commands.command(name="set_person_attr", aliases=["set_item_attr", "set_obj_attr"])
    async def set_obj_attr(self, ctx, name: str, attr_name: str, *args):
        """Set an object attribute"""
        await self.set_obj_attr_in_cont(ctx, name, None, attr_name, *args)

    @commands.command(name="scatter", aliases=["distribute"])
    async def scatter(
        self,
        ctx,
        name: str,
        cont_from: str = "cargo",
    ):
        """Take an object from a container and distribute it among the crew

        The opposite of gather
        """
        cs = self.session_data.get_ship_curr()
        crew = cs.get_objs("crew")
        n = cs.get_objs(name, cont=cont_from, only_one=True)[0].count()
        res = BbwRes()
        for idx, i in enumerate(crew):
            if idx < n and not i.get_objs(name=name).count():
                ans = await self.move(ctx, name, i.name(), 1, cont_from, mute=True)
                res += ans[1]
        await self._send_add_res(ctx, res, len(crew))

    @commands.command(name="gather", aliases=["collect"])
    async def gather(
        self,
        ctx,
        name: str,
        cont_to: str = "cargo",
    ):
        """Gather objects from the crew and put them in the cargo

        The opposite of scatter
        """
        cs = self.session_data.get_ship_curr()
        crew = cs.get_objs("crew")

        res = BbwRes()
        for i in crew:
            if i.get_objs(name=name, cont=i.name()).count():
                ans = await self.move(ctx, name, cont_to, "inf", i.name(), mute=True)
                res += ans[0]
        await self._send_add_res(ctx, res, "inf")

    @commands.command(name="move", aliases=[])
    async def move(
        self, ctx, name: str, cont_to: str, count: float = float("inf"), cont_from: str = "cargo", mute: bool = False
    ):
        """Move item from container to container"""
        cs = self.session_data.get_ship_curr()

        res_from = cs.del_obj(name=name, count=count, cont=cont_from)
        if res_from.count() == 0:
            raise SelectionException(f"object `{name}` not found in `{cont_from}`")

        res_to_tot = BbwRes()

        for i, _ in res_from.objs():
            res_to = cs.dist_obj(i, cont=cont_to)
            if not mute:
                await self._send_add_res(ctx, res_to, count)

            if i.count() > res_to.count():
                i.set_count(i.count() - res_to.count())
                res_to = cs.dist_obj(i, cont=cont_from)
                if not mute:
                    await self._send_add_res(ctx, res_to, count)
            res_to_tot += res_to
        return res_from, res_to_tot

    @commands.command(
        name="move_vip", aliases=["move_to_world", "move_from_world", "move_to_planet", "move_from_planet"]
    )
    async def move_vip(self, ctx, name: str, world_to: str = None, world_from: str = None):
        """Move a person to a world

        Usually used to put people to bench
        """
        cs = self.session_data.get_ship_curr()

        if world_from is None:
            from_c = cs
        else:
            from_c = self.session_data.charted_space().get_objs(name=world_from, only_one=True)[0].people()

        if world_to is None:
            to_c = self.session_data.get_world().people()
        else:
            to_c = self.session_data.charted_space().get_objs(name=world_to, only_one=True)[0].people()

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
        """What day is it?"""
        await self.send(ctx, self.session_data.calendar().__str__(detail_lvl=1))

    @commands.command(name="set_date", aliases=[])
    async def set_date(self, ctx, day: int, year: int):
        """Set date"""
        self.session_data.calendar().set_date(day, year)
        await self.send(ctx, "Date set successfully")
        await self.date(ctx)

        self.session_data.add_log_entry(f"set date")

    @commands.command(name="newday", aliases=["advance"])
    async def newday(self, ctx, ndays: int = 1, msg: str = "", travel_accounting: bool = False):
        """Advance ndays

        ndays: number of days
        msg: message for the log
        travel_accounting: paybacks in case of jump. Used only internally
        """
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

    @commands.command(name="cr", aliases=["add_money"])
    async def money(self, ctx, value: int = 0, description: str = "", is_mute: bool = False):
        """Add money/get balance

        value == 0 gets balance
        """

        if value == 0:
            return await self.send(ctx, self.session_data.company().__str__(detail_lvl=0))

        if type(description) is BbwRes:
            description = f"{description.objs()[0][0].name()} ({description.count()})"

        self.session_data.add_log_entry(description, value)
        msg = f"{description}: `{value}` Cr"
        if not is_mute:
            await self.send(ctx, msg)
        return msg

    @commands.command(name="debts", aliases=["debt"])
    async def debts(self, ctx):
        """Debts"""
        return await self.send(ctx, self.session_data.company().__str__(detail_lvl=1))

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
        """Add debt

        They can be recurring and can end eventually
        """
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
        """Del debt"""
        self.session_data.company().debts().del_obj(name=name)

        await self.money(ctx, 1)

    @commands.command(name="set_debt_attr", aliases=[])
    async def set_debt_attr(self, ctx, debt_name: str, attr_name: str, *args):
        """Set debt attribute"""
        res = self.session_data.company().debts().get_objs(name=debt_name, only_one=True)
        res.objs()[0][0].set_attr(attr_name, *args)

        await self.money(ctx, 1)

    @commands.command(name="rename_debt", aliases=[])
    async def rename_debt(self, ctx, name: str, new_name: str):
        """Rename debt"""
        self.session_data.company().debts().rename_obj(name=name, new_name=new_name)

        await self.money(ctx, 1)

    @commands.command(name="pay_debt", aliases=["pay_debts"])
    async def pay_debts(self, ctx, name: str = None):
        """Pay debts

        Used usually only internally
        """
        self.session_data.company().pay_debts(self.session_data.log(), self.session_data.calendar().t(), name)

        await self.send(ctx, "debts payed")

    @commands.command(name="pay_docking_fees", aliases=["docking", "pay_docking"])
    async def pay_docking_fees(self, ctx, value: int = None):
        """Pay docking fees

        It rolls automatically if value is omitted. Otherwise `value` takes priority
        """
        cw = self.session_data.get_world()

        if value is not None:
            cw.set_docking_fee(value)

        value = cw.docking_fee()

        await self.money(ctx, value=-value, description=f"docking fee")

    @commands.command(name="pay_salaries", aliases=[])
    async def pay_salaries(self, ctx, print_recap: bool = True):
        """Pay salaries"""
        cs = self.session_data.get_ship_curr()
        crew = cs.get_objs(name="crew")
        self.session_data.company().pay_salaries(crew, self.session_data.log(), self.session_data.calendar().t())

        if print_recap:
            await self.money(ctx, 10)

    @commands.command(name="close_month", aliases=[])
    async def close_month(self, ctx):
        """Accounting for the end of the month"""
        self.session_data.add_log_entry("close month")
        await self.consume_fuel(ctx, 1)
        await self.pay_salaries(ctx, False)
        await self.pay_debts(ctx)

    @commands.command(name="add_gen_obj", aliases=["add_cont"])
    async def add_obj(
        self, ctx, name: str, capacity: float = None, size: float = 0.0, count: int = 1, cont: str = None
    ):
        """Add generic object

        Used to add containers usually
        """
        new_obj = BbwObj(name=name, capacity=capacity, size=size, count=count)
        cs = self.session_data.get_ship_curr()
        res = cs.dist_obj(new_obj, cont=cont)
        await self._send_add_res(ctx, res, count)

    @commands.command(name="add_item", aliases=["add_obj"])
    async def add_item(
        self,
        ctx,
        name: str,
        count: int = 1,
        capacity: float = None,
        TL: int = None,
        value: int = None,
        cont: str = "cargo",
        n_sectors: int = 1,
        unbreakable: bool = False,
        mute: bool = False,
    ):
        """Add free items (no cost)"""

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
        unbreakable=False,
        mute: bool = False,
    ):
        """Add objects paying price_multi*value"""
        try:
            new_item = BbwItemFactory.make(
                name=name, count=count, TL=TL, value=value, capacity=capacity, n_sectors=n_sectors
            )
        except SelectionException:
            new_item = BbwItem(name=name, count=count, TL=TL, value=value, capacity=capacity)

        cs = self.session_data.get_ship_curr()

        free_slots = cs.free_slots(
            caps=[
                (new_item, cont, {}),
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
            await self.money(ctx, value=-price_payed, description=f"buy: {description}")
        else:
            self.session_data.add_log_entry(f"add item: {description}")

        res = cs.dist_obj(obj=new_item, cont=cont)

        if not mute:
            await self._send_add_res(ctx, res, res.count())

        return res

    @commands.command(name="sell", aliases=[])
    async def sell(self, ctx, name: str, price_multi: float = 1.0, count: float = float("inf"), cont: str = None):
        """Sell object and gain price_multi*value"""
        res = await self.del_obj(ctx, name=name, count=count, cont=cont)

        description = f"sell: {', '.join(set([i.name() for i in res]))} ({res.count()})"

        price_payed = res.value() * price_multi

        await self.money(ctx, value=price_payed, description=description)

    @commands.command(name="buy_spt", aliases=["st_buy", "spt_buy", "buy_st", "stbuy", "buyst", "sptbuy", "buyspt"])
    async def optimize_buy_spt(self, ctx, w_name: str = None, supplier: str = None):
        """Optimize buying

        w_name: buy from here
        supplier: filter with what the supplier has
        """
        w = self.session_data.get_world(w_name)

        cs = self.session_data.get_ship_curr()
        filter = set()
        s = f"speculative trading in `{w.name()}`\n"
        if supplier is not None and supplier != "":
            supplier = BbwUtils.get_objs(w.suppliers().values(), name=supplier, only_one=True)[0]
            s += f"from `{supplier.name()}`\n"
            filter = set([i[0] for i in supplier.supply()])

        h, t = BbwTrade.optimize_spt(cs, w_buy=w, w_sell=None, filter=filter)
        s += BbwUtils.print_table(t=t, headers=h, detail_lvl=1, tablefmt="fancy_grid")

        await self.send(ctx, s)

    @commands.command(
        name="sell_spt", aliases=["st_sell", "spt_sell", "sell_st", "stsell", "sellst", "sptsell", "sellspt"]
    )
    async def optimize_sell_spt(self, ctx, w_name: str = None, from_ship_supplies: bool = False):
        """Optimize selling

        w_name: sell on this planet
        supplier: filter with what the ship has
        """
        w = self.session_data.get_world(w_name)

        cs = self.session_data.get_ship_curr()
        filter = set()
        s = f"Speculative trading in `{w.name()}`\n"
        if from_ship_supplies:
            filter = set([i.name() for i in cs.get_objs("spt")])
            s += f"using ship `spt` cargo: " + ", ".join([f"`{i}`" for i in filter]) + "\n"

        h, t = BbwTrade.optimize_spt(cs, w_buy=None, w_sell=w, filter=filter)
        s += BbwUtils.print_table(t=t, headers=h, detail_lvl=1, tablefmt="fancy_grid")

        await self.send(ctx, s)

    @commands.command(
        name="jump_spt", aliases=["st_jump", "spt_jump", "jump_st", "stjump", "jumpst", "sptjump", "jumpspt"]
    )
    async def optimize_jump_spt(self, ctx, w_to_name: str, supplier: str = None, w_from_name: str = None):
        """Optimize speculative trading given jumping points

        w_to_name: sell on this planet
        supplier: filter with what the ship has
        w_from_name: buy in this planet
        """
        w0, w1 = self.session_data.get_worlds(w_to_name=w_to_name, w_from_name=w_from_name)
        cs = self.session_data.get_ship_curr()

        filter = set()
        s = f"Speculative trading from `{w0.name()}` to `{w1.name()}`\n"
        if supplier is not None and supplier != "":
            supplier = BbwUtils.get_objs(w0.suppliers().values(), name=supplier, only_one=True)[0]
            s += f"from `{supplier.name()}`\n"
            filter = set([i[0] for i in supplier.supply()])

        h, t = BbwTrade.optimize_spt(cs, w_buy=w0, w_sell=w1, filter=filter)
        s += BbwUtils.print_table(t=t, headers=h, detail_lvl=1, tablefmt="fancy_grid")

        await self.send(ctx, s)

    @commands.command(name="trade_spt", aliases=["trade", "trade_st"])
    async def get_deal_spt(self, ctx, broker_skill: int, name: str, roll: str = "3d6"):
        """Get deal on item"""
        w = self.session_data.get_world()

        buy_multi, buy_roll, sell_multi, sell_roll = BbwTrade.get_deal_spt(
            name=name, broker=broker_skill, w=w, roll=roll
        )
        s = f"buy: `{int(buy_multi*10000)/100}%` {buy_roll}\n"
        s += f"sell: `{int(sell_multi * 10000)/100}%` {sell_roll}"

        await self.send(ctx, s)

    @commands.command(name="add_supplier", aliases=[])
    async def add_supplier(self, ctx, name: str):
        """Add supplier to world"""
        w = self.session_data.get_world()
        supp = BbwSupplier(name=name)
        res = w.suppliers().dist_obj(supp)
        await self._send_add_res(ctx, res, res.count())

    @commands.command(name="del_supplier", aliases=[])
    async def del_supplier(self, ctx, name: str):
        """Del supplier"""
        w = self.session_data.get_world()
        res = w.suppliers().del_obj(name)
        await self._send_add_res(ctx, res, res.count())

    @commands.command(name="refresh_supplier_inventory", aliases=["gen_supply"])
    async def refresh_supplier_inventory(self, ctx, name: str = ""):
        """Refresh/regenrate supplier inventory"""
        w = self.session_data.get_world()
        w.set_supply(BbwTrade, self.session_data.calendar().t(), name)
        await self.world_curr(ctx)

    ##################################################
    ### wish
    ##################################################

    @commands.command(name="add_wish", aliases=[])
    async def add_wish(self, ctx, name: str, capacity: float = None, TL: int = None, value: int = None):
        """Add wish"""
        try:
            new_item = BbwItemFactory.make(name=name, count=1, TL=TL, value=value, capacity=capacity)
        except SelectionException:
            new_item = BbwItem(name=name, count=1, TL=TL, value=value, capacity=capacity)
        res = self.session_data.wishlist().dist_obj(new_item)

        await self._send_add_res(ctx, res, res.count())

    @commands.command(name="set_wish_attr", aliases=[])
    async def set_wish_attr(self, ctx, item_name: str, attr_name: str, *args):
        """Set wish attribute"""
        res = self.session_data.wishlist().get_objs(name=item_name, only_one=True)
        res[0].set_attr(attr_name, *args)

        await self._send_add_res(ctx, res, res.count())

    @commands.command(name="del_wish", aliases=[])
    async def del_wish(self, ctx, name: str, count: float = float("inf"), mute: bool = False):
        """Del wish"""
        res = self.session_data.wishlist().del_obj(name=name, count=float(count))
        if not mute:
            await self._send_add_res(ctx, res, count)

    @commands.command(name="rename_wish", aliases=[])
    async def rename_wish(self, ctx, name: str, new_name: str):
        """Rename wish"""
        res = self.session_data.wishlist().rename_obj(name=name, new_name=new_name)

        await self._send_add_res(ctx, res, res.count())

    @commands.command(name="wish", aliases=["wishes", "wishlist"])
    async def wishlist(self, ctx, name: str = ""):
        """Get wishlist"""
        await self.send(ctx, self.session_data.wishlist().__str__(detail_lvl=1, lname=name))

    @commands.command(name="buy_wish", aliases=[])
    async def buy_wish(self, ctx, name: str, count: int = 1, price_multi: float = 1.0, erase_wish: bool = False):
        """Buy an item in the wishlist"""
        obj = copy.deepcopy(self.session_data.wishlist().get_objs(name=name, only_one=True)[0])

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


class BbwHelp(commands.DefaultHelpCommand):
    async def command_callback(self, ctx, *, command=None):
        """|coro|

        The actual implementation of the help command.

        It is not recommended to override this method and instead change
        the behaviour through the methods that actually get dispatched.

        - :meth:`send_bot_help`
        - :meth:`send_cog_help`
        - :meth:`send_group_help`
        - :meth:`send_command_help`
        - :meth:`get_destination`
        - :meth:`command_not_found`
        - :meth:`subcommand_not_found`
        - :meth:`send_error_message`
        - :meth:`on_help_command_error`
        - :meth:`prepare_help_command`
        """
        await self.prepare_help_command(ctx, command)
        bot = ctx.bot
        cmds = BbwUtils.get_objs(bot.commands, command)

        if len(cmds) > 1:
            # similar to send_bot_help

            if bot.description:
                # <description> portion
                self.paginator.add_line(bot.description, empty=True)

            no_category = "\u200b{0.no_category}:".format(self)

            def get_category(command, *, no_category=no_category):
                cog = command.cog
                return cog.qualified_name + ":" if cog is not None else no_category

            filtered = await self.filter_commands(cmds, sort=True, key=get_category)
            max_size = self.get_max_size(filtered)
            to_iterate = itertools.groupby(filtered, key=get_category)

            # Now we can add the commands to the page.
            for category, commands in to_iterate:
                commands = sorted(commands, key=lambda c: c.name) if self.sort_commands else list(commands)
                self.add_indented_commands(commands, heading=category, max_size=max_size)

            note = self.get_ending_note()
            if note:
                self.paginator.add_line()
                self.paginator.add_line(note)

            return await self.send_pages()

        # Check if it's a cog
        cog = bot.get_cog(command)
        if cog is not None:
            return await self.send_cog_help(cog)
        if len(cmds) == 1:
            return await self.send_command_help(cmds[0])


def setup(bot):
    bot.add_cog(Game(bot))
