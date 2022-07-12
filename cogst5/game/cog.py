import discord
from discord.ext import commands
from cogst5.library import Library
import json
from os.path import basename
import time

from .starship import Starship

from ..models.errors import *

from .session_data import SessionData


class ToJson(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, "__to_json__"):
            return obj.__to_json__()
        return json.JSONEncoder.default(self, obj)



class Game(commands.Cog):
    """Traveller 5 commands."""

    def __init__(self, bot):
        self.bot = bot
        self.library = Library()
        self.session_data = SessionData()

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
        """*Query Starship Library Database*

        In a universe with no faster-than-light communication, there is no Galactic Internet. Every Starship therefore carries its own database of information about a wide variety of subjects: worlds, lifeforms, corporations, politics, history, *etc.* Almost all Starships in Traveller have this database in the form of the **Library/0** program. The Library database is periodically updated, when the ship is in port at a Class A or Class B starport.

        `<search_term>` can be a single word, or a phrase. If there is an unambiguous partial match with an entry in the database, the Library Data for that entry will be returned. If there are multiple matching terms, a list of possible matches will be returned (try again with a more specific term from the list)."""
        for arg in args:
            search_term = f"{search_term} {arg}"
        await self.print_long_message(ctx, self.library.search(search_term))

    @commands.command(name="save")
    async def save_json(self, ctx, filename: str = "session_data.json"):
        """Save session data to a file in JSON format."""
        with open(f"/save/{basename(filename)}", "w") as f:
            json.dump(self.session_data.__to_json__(), f, cls=ToJson, indent=2, ensure_ascii=False)
        ts = time.gmtime()
        timestamp = time.strftime("%Y%m%d%H%M%S", ts)
        filename_backup = f"{basename(filename)}.{timestamp}"
        with open(f"/save/{filename_backup}", "w") as f:
            json.dump(self.session_data.__to_json__(), f, cls=ToJson)
        await ctx.send(f"Session data saved as: {filename}. Backup in: {filename_backup}")

    @commands.command(name="load")
    async def load_json(self, ctx, filename: str = "session_data.json"):
        """Load session data from a JSON-formatted file."""
        with open(f"/save/{basename(filename)}", "r") as f:
            self.session_data = self.session_data.__from_dict__(json.load(f))

        await ctx.send(f"Session data loaded from {filename}.")

    @commands.command(name="add_starship", aliases=["add_spaceship", "add_starcraft", "add_ship"])
    async def add_starship(self, ctx, name):
        """Add a starship to the fleet"""

        if name in self.session_data.fleet:
            raise NotAllowed("A starship with that name already exists! You need to remove it first")

        self.session_data.fleet[name] = Starship(name)
        self.session_data.starship_current = name
        await ctx.send(f"The starship {name} was successfully added to the fleet.")
        await self.current_starship(ctx)

    @commands.command(name="remove_starship", aliases=["remove_spaceship", "remove_starcraft", "remove_ship"])
    async def remove_starship(self, ctx, name):
        """Remove a starship to the fleet"""

        if name not in self.session_data.fleet:
            await self.fleet(ctx)
            raise InvalidArgument(f"Starship {name} not found.")

        del self.session_data.fleet[name]
        self.session_data.starship_current = ""

        await ctx.send(f"The starship {name} was successfully added to the fleet.")
        await self.current_starship(ctx)

    @commands.command(
        name="current_starship", aliases=["current_spaceship", "current_starcraft", "current_ship", "ship"]
    )
    async def current_starship(self, ctx):
        """Current starship summary"""

        cs = self.session_data.get_current_starship()

        await ctx.send(cs.__str__())

    @commands.command(name="set_current_starship", aliases=["set_ship", "set_curr_ship"])
    async def set_current_starship(self, ctx, name):
        """Current starship summary"""
        if name not in self.session_data.fleet:
            await self.fleet(ctx)
            raise InvalidArgument(f"Starship {name} not found.")

        self.session_data.starship_current = name

        await self.current_starship(ctx)

    @commands.command(name="fleet", aliases=["get_fleet"])
    async def fleet(self, ctx):
        """Fleet summary"""

        await ctx.send(f"Starships in the fleet ({len(self.session_data.fleet)}): {', '.join(self.session_data.fleet)}")

    @commands.command(name="set_current_starship_attribute", aliases=["set_ship_att", "set_ship_attribute"])
    async def set_current_starship_attribute(self, ctx, key, value):
        """Set current starship attribute"""
        cs = self.session_data.get_current_starship()

        cs.set_attribute(key, value)

        await ctx.send(f"Attribute {key} successfully set to {value}")
