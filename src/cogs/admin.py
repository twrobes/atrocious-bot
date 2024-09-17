import discord
from discord import app_commands
from discord.ext import commands

ADMIN_USER_ID = 104797389373599744


class Admin(commands.GroupCog, name='admin'):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print('Admin cog loaded.')

    @app_commands.command(
        name='server_message',
        description='Sends a message to a specified guild channel'
    )
    async def send_server_message(self, interaction: discord.Interaction, channel_id: str, message: str):
        if interaction.user.id != ADMIN_USER_ID:
            await interaction.response.send_message('You are not allowed to use this command', ephemeral=True)
            return

        channel = self.bot.get_channel(int(channel_id))
        await channel.send(message)
        await interaction.response.send_message('Message sent successfully', ephemeral=True)


async def setup(bot):
    await bot.add_cog(Admin(bot), guilds=[
        discord.Object(id=238145730982838272),
        # discord.Object(id=699611111066042409)
    ])
