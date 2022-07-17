import discord
from discord.ext import commands
from cogst5.library import Library
import json
import jsonpickle
from os.path import basename
import time

from cogst5.models.errors import *

from cogst5.session_data import BbwSessionData
from cogst5.bbw_objects import *

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
    async def set_spaceship(self, ctx, name, capacity, type0, TL, cargo_capacity, seat_capacity, fuel_tank_capacity):
        """Add a ship"""

        self.session_data.set_spaceship(
            name=name,
            capacity=capacity,
            type=type0,
            TL=TL,
            cargo_capacity=cargo_capacity,
            seat_capacity=seat_capacity,
            fuel_tank_capacity=fuel_tank_capacity,
        )

        await ctx.send(f"The ship {name} was successfully added to the fleet.")
        await self.set_ship_curr(ctx, name)

    @commands.command(name="del_ship", aliases=[])
    async def del_spaceship(self, ctx, name):
        """Del ship"""

        self.session_data.del_ship(name=name)

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

        await ctx.send(self.session_data.fleet.__str__(is_compact=False))

    @commands.command(name="fuel", aliases=["add_fuel"])
    async def add_fuel(self, ctx, value):
        cs = self.session_data.get_ship_curr()
        cs.add_fuel(value)

        await self.ship_curr(ctx)

    @commands.command(name="crew", aliases=["add_crew"])
    async def add_crew(self, ctx, value):
        cs = self.session_data.get_ship_curr()
        cs.add_crew(value)

        await self.ship_curr(ctx)

    @commands.command(name="passenger", aliases=["add_passenger", "pass"])
    async def add_passenger(self, ctx, value):
        cs = self.session_data.get_ship_curr()
        cs.add_passenger(value)

        await self.ship_curr(ctx)

    @commands.command(name="add_cargo", aliases=[])
    async def add_cargo(self, ctx, name, count=1, size=0.0, capacity=1.0):
        cs = self.session_data.get_ship_curr()

        new_item = BbwObj(name=name, count=count, size=size, capacity=capacity)
        cs.add_cargo(new_item)

        await self.ship_curr(ctx)

    @commands.command(name="del_cargo", aliases=[])
    async def del_cargo(self, ctx, name, count=1):
        cs = self.session_data.get_ship_curr()
        cs.del_cargo(name=name, count=count)

        await self.ship_curr(ctx)
