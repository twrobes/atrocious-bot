import discord
from discord import app_commands
from discord.ext import commands


class Warcraftlogs(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print('Warcraftlogs cog loaded.')

    @app_commands.command(
        name='prog',
        description='Shows the current raid progress of the guild'
    )
    async def prog(self, interaction: discord.Interaction):
        await interaction.response.send_message('placeholder')


async def setup(bot):
    await bot.add_cog(Warcraftlogs(bot), guilds=[
        discord.Object(id=238145730982838272),
        discord.Object(id=699611111066042409)
    ])
