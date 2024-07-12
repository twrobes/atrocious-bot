import random

import discord
from discord import app_commands
from discord.ext import commands


class Games(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name='deathroll',
        description='Start a deathroll with another user'
    )
    async def deathroll(self, interaction: discord.Interaction, opponent: discord.Member, roll: int):
        await interaction.response.send_message(
            f'{interaction.user.display_name} has challenged {opponent.display_name}!'
        )
        challenger = interaction.user
        current_player = challenger

        while roll != 1:
            view = Roll()

            await interaction.followup.send(f'It is your turn to roll {current_player.display_name}.', view=view)
            await view.wait()

            roll = random.randrange(1, roll + 1)
            await interaction.followup.send(f'{current_player.display_name} rolled {roll}')

            if current_player is opponent:
                current_player = challenger
            else:
                current_player = opponent

        print('winner')
        await interaction.followup.send(f'**{current_player.display_name} wins!**')


class Roll(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.value = None
        # self.user = user

    # async def interaction_check(self, user: discord.Member):
    #     # print(f'{user.id} {self.user.id}')
    #     print(f'{user.name} {self.user.name}')
    #     return user.name == self.user.name

    @discord.ui.button(label='Roll', style=discord.ButtonStyle.blurple)
    async def roll(self, interaction: discord.Interaction, button: discord.ui.Button):
        # if await self.interaction_check(user):
        await interaction.response.send_message('Rolling...', ephemeral=True)
        self.value = True
        self.stop()


async def setup(bot):
    await bot.add_cog(Games(bot), guilds=[
        discord.Object(id=238145730982838272),
        discord.Object(id=699611111066042409)
    ])
