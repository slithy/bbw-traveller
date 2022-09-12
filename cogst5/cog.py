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

jsonpickle.set_encoder_options("json", sort_keys=True)

hrline = "__                                                                 __\n"


class Game(commands.Cog):
    """Traveller 5 commands."""

    def __init__(self, bot):
        self.bot = bot
        self.library = Library()
        self.session_data = BbwSessionData()

    async def send(self, ctx, msg):
        """Split long messages to workaround the discord limit"""

        max_length = 2000

        if len(msg) <= max_length:
            await ctx.send(msg)
        else:
            s = msg.split("\n")

            j = 0
            l = 0
            for i in range(len(s)):
                newl = l + len(s[i]) + (l != 0)
                if newl <= max_length:
                    l = newl
                else:
                    token = "\n".join(s[j:i])
                    await ctx.send(token)
                    j = i
                    l = len(s[i])

            last_line = "\n".join(s[j:])
            await ctx.send(last_line)

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

        await ctx.send(f"Session data saved as: {basename(p)}. Backup in: {basename(p_backup)}")

    @commands.command(name="load")
    async def load_session_data(self, ctx, filename: str = "session_data.json"):
        """Load session data from a JSON-formatted file."""

        with open(f"../../save/{basename(filename)}", "r") as f:
            enc_data = json.dumps(json.load(f))
            self.session_data = jsonpickle.decode(enc_data)

        await ctx.send(f"Session data loaded from {filename}.")

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
        containers,
        drive_m,
        drive_j,
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
            containers=eval(containers),
            drive_m=drive_m,
            drive_j=drive_j,
            power_plant=power_plant,
            fuel_refiner_speed=fuel_refiner_speed,
            is_streamlined=is_streamlined,
            has_fuel_scoop=has_fuel_scoop,
            has_cargo_crane=has_cargo_crane,
        )
        self.session_data.fleet().set_item(s)

        await ctx.send(f"The ship {name} was successfully added to the fleet.")
        await self.set_ship_curr(ctx, name)

    @commands.command(name="del_ship", aliases=[])
    async def del_ship(self, ctx, name):
        """Del ship"""

        self.session_data.fleet.del_ship(name=name)

        await ctx.send(f"The ship {name} was successfully deleted.")
        await self.fleet(ctx)

    @commands.command(name="rename_ship_curr", aliases=["rename_ship"])
    async def rename_ship(self, ctx, new_name):
        cs = self.session_data.get_ship_curr()
        self.session_data.fleet().rename_item(cs, new_name)

        await self.set_ship_curr(ctx, new_name)

    @commands.command(name="ship_curr", aliases=["ship"])
    async def ship_curr(self, ctx):
        """Current ship summary"""

        cs = self.session_data.get_ship_curr()

        await self.send(ctx, cs.__str__(is_compact=False))

    @commands.command(name="set_ship_curr", aliases=[])
    async def set_ship_curr(self, ctx, name):
        """Set current ship"""

        self.session_data.set_ship_curr(name)

        await self.ship_curr(ctx)

    @commands.command(name="fleet", aliases=["ships"])
    async def fleet(self, ctx):
        """Fleet summary"""

        await ctx.send(self.session_data.fleet().__str__(is_compact=False))

    @commands.command(name="wish", aliases=["wishes", "wishlist"])
    async def wishlist(self, ctx):
        await self.send(ctx, self.session_data.wishlist().__str__(is_compact=False))

    @commands.command(name="add_wish", aliases=[])
    async def add_wish(self, ctx, name, count=1, TL=0, value=0):
        new_item = BbwItem(name=name, count=count, capacity=1.0, value=value, TL=TL)
        self.session_data.wishlist().add_item(new_item)

        await self.wishlist(ctx)

    @commands.command(name="del_wish", aliases=[])
    async def del_wish(self, ctx, name, count=1):
        _, item = self.session_data.wishlist().get_item(name)
        self.session_data.wishlist().del_item(item.name(), count)

        await self.wishlist(ctx)

    @commands.command(name="rename_wish", aliases=[])
    async def rename_wish(self, ctx, name, new_name):
        self.session_data.wishlist().rename_item(name, new_name)

        await self.wishlist(ctx)

    @commands.command(name="add_debt", aliases=[])
    async def add_debt(self, ctx, name, count, due_day, due_year, period=None, end_day=None, end_year=None):
        new_debt = BbwDebt(
            name=name,
            count=count,
            due_t=BbwCalendar.date2t(due_day, due_year),
            period=period,
            end_t=BbwCalendar.date2t(end_day, end_year),
            capacity=1.0,
        )
        self.session_data.company().debts().add_item(new_debt)

        await self.money(ctx)

    @commands.command(name="del_debt", aliases=[])
    async def del_debt(self, ctx, name, count=1):
        _, debt = self.session_data.company().debts().get_item(name)
        self.session_data.company().debts().del_item(debt.name(), count)

        await self.money(ctx)

    @commands.command(name="rename_debt", aliases=[])
    async def rename_debt(self, ctx, name, new_name):
        self.session_data.company().rename_item(name, new_name)

        await self.money(ctx)

    @commands.command(name="pay_debt", aliases=["pay_debts"])
    async def pay_debts(self, ctx, name=None):
        if name is None:
            await self.save_session_data(ctx)

        self.session_data.company().pay_debts(self.session_data.calendar().t(), name)

        await self.money(ctx)

    @commands.command(name="add_money", aliases=["cr"])
    async def add_money(self, ctx, value=0, description=""):
        if value:
            self.session_data.company().add_log_entry(value, description, self.session_data.calendar().t())

        await self.money(ctx, 10)

    @commands.command(name="money_status", aliases=["status", "money", "log"])
    async def money(self, ctx, log_lines=10):
        await self.send(ctx, self.session_data.company().__str__(log_lines))

    @commands.command(name="date", aliases=[])
    async def date(self, ctx):
        await self.send(ctx, self.session_data.calendar().__str__(is_compact=False))

    @commands.command(name="set_date", aliases=[])
    async def set_date(self, ctx, day, year):
        self.session_data.calendar().set_date(day, year)
        await ctx.send("Date set successfully")
        await self.date(ctx)

    @commands.command(name="newday", aliases=["advance"])
    async def newday(self, ctx, ndays=1):
        self.session_data.calendar().add_t(ndays)
        await self.send(ctx, f"{hrline}Date advanced")
        await self.date(ctx)

    @commands.command(name="set_ship_attr", aliases=["set_ship_curr_attr"])
    async def set_ship_attr(self, ctx, attr_name, value):
        cs = self.session_data.get_ship_curr()
        cs.set_attr(attr_name, value)

        await self.ship_curr(ctx)

    @commands.command(name="set_debt_attr", aliases=[])
    async def set_debt_attr(self, ctx, debt_name, attr_name, value):
        _, debt = self.session_data.company().debts().get_item(debt_name)
        debt.set_attr(attr_name, value)

        await self.money(ctx)

    @commands.command(name="set_wish_attr", aliases=[])
    async def set_wish_attr(self, ctx, item_name, attr_name, value):
        _, item = self.session_data.wishlist().get_item(item_name)
        item.set_attr(attr_name, value)

        await self.wishlist(ctx)

    @commands.command(name="container", aliases=[])
    async def container(self, ctx, container_name):
        cs = self.session_data.get_ship_curr()
        container = cs.get_container(container_name)
        await self.send(ctx, container.__str__(False))

    @commands.command(name="add_person", aliases=[])
    async def add_person(
        self, ctx, container_name, name, role, upp=None, salary_ticket=None, capacity=None, reinvest=False, count=1
    ):
        cs = self.session_data.get_ship_curr()
        container = cs.get_container(container_name)

        new_person = BbwPerson(
            name=name,
            count=count,
            role=role,
            salary_ticket=salary_ticket,
            capacity=capacity,
            reinvest=reinvest,
            upp=upp,
        )
        container.add_item(new_person)

        await self.container(ctx, container.name())

    @commands.command(name="add_item", aliases=[])
    async def add_item(self, ctx, container_name, name, count=1, capacity=1.0, TL=0, value=0, size=None):
        """add item to container"""
        cs = self.session_data.get_ship_curr()
        container = cs.get_container(container_name)

        new_item = BbwItem(name=name, count=count, capacity=capacity, TL=TL, value=value, size=size)
        container.add_item(new_item)

        await self.container(ctx, container.name())

    @commands.command(name="del_person", aliases=["del_item", "del"])
    async def del_item(self, ctx, container_name, name, count=1):
        cs = self.session_data.get_ship_curr()
        container = cs.get_container(container_name)

        _, item = container.get_item(name)
        container.del_item(item.name(), count)

        await self.container(ctx, container.name())

    @commands.command(name="rename_person", aliases=["rename_item", "rename"])
    async def rename_item(self, ctx, container_name, name, new_name):
        cs = self.session_data.get_ship_curr()
        container = cs.get_container(container_name)

        container.rename_item(name, new_name)

        await self.container(ctx, container.name())

    @commands.command(name="set_person_attr", aliases=["set_item_attr"])
    async def set_item_attr(self, ctx, container_name, item_name, attr_name, value):
        cs = self.session_data.get_ship_curr()
        container = cs.get_container(container_name)

        _, item = container.get_item(item_name)

        item.set_attr(attr_name, value)

        await self.container(ctx, container.name())

    @commands.command(name="pay_salaries", aliases=[])
    async def pay_salaries(self, ctx):
        cs = self.session_data.get_ship_curr()
        self.session_data.company().pay_salaries(cs.get_people(), self.session_data.calendar().t())

        await self.money(ctx, 10)

    @commands.command(name="flight_time_m_drive", aliases=["m_drive_t", "m_drive"])
    async def flight_time_m_drive(self, ctx, d_km):
        cs = self.session_data.get_ship_curr()

        t = conv_days_2_time(cs.flight_time_m_drive(d_km))

        await ctx.send(f"{hrline}the m drive {cs.drive_m()} travel time to cover {d_km} km is: {t}")

    @commands.command(name="flight_time_j_drive", aliases=["j_drive_t", "j_drive"])
    async def flight_time_j_drive(self, ctx, n_jumps=1):
        cs = self.session_data.get_ship_curr()

        t = conv_days_2_time(cs.flight_time_j_drive(n_jumps))

        await ctx.send(f"{hrline}the j drive {cs.j_drive()} travel time to do {n_jumps} jumps is: {t}")

    @commands.command(name="flight_time_p2p", aliases=["flight_p2p", "p2p"])
    async def flight_time_planet_2_planet(self, ctx, d1_km, d2_km, n_jumps=1):
        cs = self.session_data.get_ship_curr()

        t1, t2, t3 = cs.flight_time_planet_2_planet(d1_km, d2_km, n_jumps)

        tab = [
            [f"m drive ({round(100 * float(d1_km))} km)", conv_days_2_time(t1)],
            [f"j drive ({n_jumps} jumps)", conv_days_2_time(t2)],
            [f"m drive ({round(100 * float(d2_km))} km)", conv_days_2_time(t3)],
        ]

        await self.send(ctx, f"{hrline}the total travel time is:\n{print_table(tab)}\n= {conv_days_2_time(t1+t2+t3)}")

        return t1 + t2 + t3

    @commands.command(name="trip_accounting_life_support", aliases=[])
    async def trip_accounting_life_support(self, ctx, t):
        cs = self.session_data.get_ship_curr()
        life_support_costs = cs.var_life_support(t)
        self.session_data.company().add_log_entry(
            -life_support_costs, f"variable life support", self.session_data.calendar().t()
        )

        await ctx.send(f"{hrline}variable life support costs: {life_support_costs} Cr")

    @commands.command(name="trip_accounting_payback", aliases=[])
    async def trip_accounting_payback(self, ctx, t):
        cs = self.session_data.get_ship_curr()

        msg = f"{hrline}"
        crew = [i for i in cs.get_people() if i.is_crew()]
        for i in crew:
            payback = i.trip_payback(t)

            if payback is None:
                msg += f"I do not know {i.name()} upp. I cannot calculate his/her/their payback!\n"
            else:
                if i.reinvest():
                    self.session_data.company().add_log_entry(
                        payback, f"{i.name()} reinvested the payback", self.session_data.calendar().t()
                    )
                msg += f"{i.name()} gets back {payback} Cr {'' if i.reinvest() else '(reinvested)'}\n"

        await self.send(ctx, msg)

    @commands.command(name="find_passengers", aliases=[])
    async def find_passengers(self, ctx, carouse_or_broker_or_streetwise_mod, SOC_mod, n_sectors, w0, w1):
        cs = self.session_data.get_ship_curr()
        if type(w0) is str:
            w0 = eval(w0)
        if type(w1) is str:
            w1 = eval(w1)

        header = ("high", "middle", "basic", "low")
        np = [cs.find_passengers(carouse_or_broker_or_streetwise_mod, SOC_mod, i, n_sectors, w0, w1) for i in header]

        await self.send(ctx, f"{hrline}passengers:\n{print_table(np, headers=header)}")

    @commands.command(name="find_mail_and_cargo", aliases=[])
    async def find_mail_and_cargo(
        self,
        ctx,
        brocker_or_streetwise_mod,
        SOC_mod,
        max_naval_or_scout_rank,
        max_SOC_mod,
        n_sectors,
        w0,
        w1,
    ):
        cs = self.session_data.get_ship_curr()
        if type(w0) is str:
            w0 = eval(w0)
        if type(w1) is str:
            w1 = eval(w1)

        header = ("mail", "major", "minor", "incidental")
        mail = cs.find_mail(brocker_or_streetwise_mod, SOC_mod, max_naval_or_scout_rank, max_SOC_mod, n_sectors, w0, w1)
        np = [mail, *[cs.find_cargo(brocker_or_streetwise_mod, SOC_mod, i, n_sectors, w0, w1) for i in header[1:]]]

        await self.send(ctx, f"{hrline}mail and cargo:\n{print_table(np, headers=header)}")

    @commands.command(name="unload_passengers", aliases=[])
    async def unload_passengers(self, ctx):
        cs = self.session_data.get_ship_curr()

        passengers = [i for i in cs.get_people() if not i.is_crew()]
        tot = 0
        for p in passengers:
            container = cs.get_main_stateroom() if "low" not in p.name() else cs.get_main_lowberth()
            container.del_item(p.name(), c=p.count())
            cargo = cs.get_main_cargo()
            cargo.del_item(p.name())
            tot += p.salary_ticket()

        self.session_data.company().add_log_entry(tot, f"passenger tickets", self.session_data.calendar().t())

        await self.send(ctx, f"{hrline}passenger tickets: {int(tot)} Cr")

    @commands.command(name="unload_mail_and_cargo", aliases=["unload_mail"])
    async def unload_mail_and_cargo(self, ctx):
        cs = self.session_data.get_ship_curr()

        tot = 0
        for container in cs.get_all_cargo_containers():
            cargo_items = [i for i in container.values() if "cargo" in i.name()]
            for item in cargo_items:
                tot += item.value()
                container.del_item(item.name(), c=item.count())
        self.session_data.company().add_log_entry(tot, f"mail and cargo", self.session_data.calendar().t())

        await self.send(ctx, f"{hrline}mail and cargo: {int(tot)} Cr")

    @commands.command(name="unload_ship", aliases=[])
    async def unload(self, ctx):
        await self.unload_passengers(ctx)
        await self.unload_mail_and_cargo(ctx)

    @commands.command(name="fly", aliases=[])
    async def fly(self, ctx, d1_km, d2_km, n_jumps=1, save=True):
        # save
        if int(save):
            await self.save_session_data(ctx)

        # jump time
        t = await self.flight_time_planet_2_planet(ctx, d1_km, d2_km, n_jumps)

        # life support
        await self.trip_accounting_life_support(ctx, t)

        # payback
        await self.trip_accounting_payback(ctx, t)

        await self.newday(ctx, math.floor(t))

    @commands.command(name="auto_fly", aliases=[])
    async def auto_fly(
        self,
        ctx,
        carouse_or_broker_or_streetwise_mod,
        brocker_or_streetwise_mod,
        SOC_mod,
        max_naval_or_scout_rank,
        max_SOC_mod,
        n_sectors,
        n_jumps,
        w0,
        w1,
    ):
        if type(w0) is str:
            w0 = eval(w0)
        if type(w1) is str:
            w1 = eval(w1)

        # save
        await self.save_session_data(ctx)

        # load passengers
        await self.find_passengers(ctx, carouse_or_broker_or_streetwise_mod, SOC_mod, n_sectors, w0, w1)

        # load mail and cargo
        await self.find_mail_and_cargo(
            ctx,
            brocker_or_streetwise_mod,
            SOC_mod,
            max_naval_or_scout_rank,
            max_SOC_mod,
            n_sectors,
            w0,
            w1,
        )

        # fly
        await self.fly(ctx, d1_km=w0["d"], d2_km=w1["d"], n_jumps=n_jumps, save=False)

        # unload
        await self.unload(ctx)
