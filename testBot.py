from discord.ext import commands
from dotenv import load_dotenv

import os


if __name__ == "__main__":
    bot = commands.Bot(command_prefix='!')
    bot.load_extension("cogst5.cog")
    load_dotenv()
    token = os.getenv("DISCORD_TOKEN")

    @bot.event
    async def on_command_error(ctx, error):
        """ We catch the errors and print them in the chat """
        print(error)
        return await ctx.send(str(error))

    bot.run(token)