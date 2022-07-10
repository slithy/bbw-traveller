import discord
from discord.ext import commands
from cogst5.library import Library

class Game(commands.Cog):
    """Traveller 5 commands."""

    def __init__(self, bot):
        self.bot = bot
        self.library = Library()

    async def print_long_message(self, ctx, msg):
        if len(msg) <= 2000:
            await ctx.send(msg)
        else:
            s = msg.split("\n")
            for i in range(len(s)):
               await ctx.send(s[i])

    # ==== commands ====
    @commands.command(name="library_data", aliases=["library", "lib", "l"])
    async def query_library(self, ctx, search_term: str, *args):
        """*Query Starship Library Database*

        In a universe with no faster-than-light communication, there is no Galactic Internet. Every Starship therefore carries its own database of information about a wide variety of subjects: worlds, lifeforms, corporations, politics, history, *etc.* Almost all Starships in Traveller have this database in the form of the **Library/0** program. The Library database is periodically updated, when the ship is in port at a Class A or Class B starport.

        `<search_term>` can be a single word, or a phrase. If there is an unambiguous partial match with an entry in the database, the Library Data for that entry will be returned. If there are multiple matching terms, a list of possible matches will be returned (try again with a more specific term from the list)."""
        for arg in args:
            search_term = f"{search_term} {arg}"
        await self.print_long_message(ctx, self.library.search(search_term))

