from .cog import Game


def setup(bot):
    bot.add_cog(Game(bot))
