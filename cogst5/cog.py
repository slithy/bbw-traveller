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

jsonpickle.set_encoder_options("json", sort_keys=True)


class Game(commands.Cog):
    """Traveller 5 commands."""

    def __init__(self, bot):
        self.bot = bot
        self.library = Library()
        self.session_data = BbwSessionData()

    async def print_long_message(self, ctx, msg):
        """Split long messages to workaround the discord limit"""
        max_length = 100

        if len(msg) <= max_length:
            await ctx.send(msg)
        else:
            s = msg.split("\n")

            j = 0
            l = 0
            for i in range(len(s)):
                newl = l + len(s[i])
                if newl <= max_length:
                    l = newl
                    continue
                await ctx.send("\n".join(s[j:i]))
                j = i
                l = 0

            await ctx.send("\n".join(s[j:]))

    # ==== commands ====
    @commands.command(name="library_data", aliases=["library", "lib", "l"])
    async def query_library(self, ctx, search_term: str, *args):
        """*Query ship Library Database*

        In a universe with no faster-than-light communication, there is no Galactic Internet. Every ship therefore carries its own database of information about a wide variety of subjects: worlds, lifeforms, corporations, politics, history, *etc.* Almost all ships in Traveller have this database in the form of the **Library/0** program. The Library database is periodically updated, when the ship is in port at a Class A or Class B starport.

        `<search_term>` can be a single word, or a phrase. If there is an unambiguous partial match with an entry in the database, the Library Data for that entry will be returned. If there are multiple matching terms, a list of possible matches will be returned (try again with a more specific term from the list)."""
        for arg in args:
            search_term = f"{search_term} {arg}"
        await self.print_long_message(ctx, self.library.search(search_term))

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

    @commands.command(name="set_spaceship", aliases=["add_spaceship"])
    async def set_spaceship(self, ctx, name, capacity, type0, TL, seat_capacity, cargo_capacity, fuel_tank_capacity):
        """Add a ship"""

        if name in self.session_data.fleet():
            raise InvalidArgument(
                f"A ship with that name: {name} already exists! If you really want to replace it, delete it first"
            )

        s = BbwSpaceShip(
            name=name,
            type=type0,
            TL=TL,
            capacity=capacity,
            cargo_capacity=cargo_capacity,
            seat_capacity=seat_capacity,
            fuel_tank_capacity=fuel_tank_capacity,
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

    @commands.command(name="ship_curr", aliases=["ship"])
    async def ship_curr(self, ctx):
        """Current ship summary"""

        cs = self.session_data.get_ship_curr()

        await ctx.send(cs.__str__(is_compact=False))

    @commands.command(name="set_ship_curr", aliases=[])
    async def set_ship_curr(self, ctx, name):
        """Set current ship"""

        self.session_data.set_ship_curr(name)

        await self.ship_curr(ctx)

    @commands.command(name="fleet", aliases=["ships"])
    async def fleet(self, ctx):
        """Fleet summary"""

        await ctx.send(self.session_data.fleet().__str__(is_compact=False))

    @commands.command(name="fuel", aliases=["add_fuel"])
    async def add_fuel(self, ctx, value):
        cs = self.session_data.get_ship_curr()
        cs.add_fuel(value)

        await self.ship_curr(ctx)

    @commands.command(name="add_person", aliases=[])
    async def add_person(self, ctx, name, count=1, is_crew=0, size=1.0, capacity=1.0):
        cs = self.session_data.get_ship_curr()

        new_person = BbwPerson(name=name, count=count, is_crew=is_crew, size=size, capacity=capacity)
        cs.seats().add_item(new_person)

        await self.ship_curr(ctx)

    @commands.command(name="del_person", aliases=[])
    async def del_person(self, ctx, name, count=1):
        cs = self.session_data.get_ship_curr()
        person = cs.seats().get_item(name)
        cs.seats().del_item(person.name(), count)

        await self.ship_curr(ctx)

    @commands.command(name="add_cargo", aliases=[])
    async def add_cargo(self, ctx, name, count=1, size=0.0, capacity=1.0):
        cs = self.session_data.get_ship_curr()

        new_item = BbwObj(name=name, count=count, size=size, capacity=capacity)
        cs.cargo().add_item(new_item)

        await self.ship_curr(ctx)

    @commands.command(name="del_cargo", aliases=[])
    async def del_cargo(self, ctx, name, count=1):
        cs = self.session_data.get_ship_curr()
        item = cs.cargo().get_item(name)
        cs.cargo().del_item(item.name(), count)

        await self.ship_curr(ctx)


    @commands.command(name="add_debt", aliases=[])
    async def add_debt(self, ctx, name, count, due_day, due_year, period=None, end_day=None, end_year=None, size=0.0,
                       capacity=1.0):

        new_debt = BbwDebt(name=name, count=count, due_t=BbwCalendar.date2t(due_day, due_year), period=period,
                           t_end=BbwCalendar.date2t(end_day, end_year), size=size,
                           capacity=capacity)
        self.session_data.company().debts().add_item(new_debt)

        await self.money(ctx)

    @commands.command(name="del_debt", aliases=[])
    async def del_debt(self, ctx, name, count=1):
        debt = self.session_data.company().debts().get_item(name)
        self.session_data.company().debts().del_item(debt.name(), count)

        await self.money(ctx)

    @commands.command(name="pay_debt", aliases=[])
    async def pay_debt(self, ctx, name):
        debt = self.session_data.company().debts().get_item(name)
        self.session_data.company().pay_debt(debt.name(), self.session_data.calendar().t())

        await self.money(ctx)

    @commands.command(name="pay_debts", aliases=[])
    async def pay_debt(self, ctx):
        self.session_data.company().pay_debts(self.session_data.calendar().t())

        await self.money(ctx)

    @commands.command(name="add_money", aliases=["cr"])
    async def add_money(self, ctx, value=0, description="", time=None):
        if value:
            self.session_data.company().add_log_entry(value, description, time)

        await self.money(ctx, 0)

    @commands.command(name="money_status", aliases=["status", "money", "log"])
    async def money(self, ctx, log_lines=10):
        await ctx.send(self.session_data.company().__str__(log_lines))

    @commands.command(name="date", aliases=[])
    async def date(self, ctx):
        await ctx.send(self.session_data.calendar().__str__(is_compact=False))

    @commands.command(name="set_date", aliases=[])
    async def set_date(self, ctx, day, year):
        self.session_data.calendar().set_date(day, year)
        await ctx.send("Date set successfully")
        await self.date(ctx)

    @commands.command(name="newday", aliases=["advance"])
    async def newday(self, ctx, ndays=1):
        self.session_data.calendar().add_t(ndays)
        await ctx.send(f"Date advanced")
        await self.date(ctx)

    @commands.command(name="rename_ship_curr", aliases=["rename_ship"])
    async def rename_ship(self, ctx, new_name):
        cs = self.session_data.get_ship_curr()
        self.session_data.fleet().rename_item(cs, new_name)

        await self.set_ship_curr(ctx, new_name)

    @commands.command(name="rename_cargo_item", aliases=["rename_item"])
    async def rename_cargo_item(self, ctx, name, new_name):
        cs = self.session_data.get_ship_curr()
        item = cs.cargo().get_item(name)
        cs.cargo().rename_item(item, new_name)

        await self.ship_curr(ctx)

    @commands.command(name="rename_person", aliases=[])
    async def rename_person(self, ctx, name, new_name):
        cs = self.session_data.get_ship_curr()
        item = cs.seats().get_item(name)
        cs.seats().rename_item(item, new_name)

        await self.ship_curr(ctx)

    @commands.command(name="set_ship_attr", aliases=["set_ship_curr_attr"])
    async def set_attr_ship(self, ctx, attr_name, value):
        cs = self.session_data.get_ship_curr()
        cs.set_attr(attr_name, value)

        await self.ship_curr(ctx)

    @commands.command(name="set_cargo_item_attr", aliases=[])
    async def set_cargo_item_attr(self, ctx, item_name, attr_name, value):
        cs = self.session_data.get_ship_curr()
        item = cs.cargo().get_item(item_name)
        item.set_attr(attr_name, value)

        await self.ship_curr(ctx)

    @commands.command(name="set_person_attr", aliases=[])
    async def set_person_attr(self, ctx, person_name, attr_name, value):
        cs = self.session_data.get_ship_curr()
        person = cs.seats().get_item(person_name)
        person.set_attr(attr_name, value)

        await self.ship_curr(ctx)