import random

import discord
from discord import app_commands
from discord.ext import commands


class Deathroll(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print('Deathroll cog loaded.')

    @app_commands.command(
        name='deathroll',
        description='Start a deathroll with another user'
    )
    async def deathroll(self, interaction: discord.Interaction, opponent: discord.Member, roll: int):
        if interaction.user.id == opponent.id and interaction.user.id != 104797389373599744:
            await interaction.response.send_message('You tried challenging yourself, how pathetic!')
            return

        starting_msg = \
            f'{interaction.user.display_name} has challenged {opponent.display_name} to a deathroll starting at {roll}.'

        await interaction.response.send_message(starting_msg)
        challenger = interaction.user

        roll = random.randrange(1, roll + 1)
        roll_history = f'{starting_msg}\n\n{challenger.display_name} rolled {roll}\n'
        await interaction.edit_original_response(content=roll_history)
        current_player = opponent

        while roll != 1:
            view = Roll(current_player)
            await interaction.followup.send(f'It is your turn to roll {current_player.display_name}.', view=view)
            await view.wait()

            roll = random.randrange(1, roll + 1)
            roll_history += f'{current_player.display_name} rolled {roll}\n'
            await interaction.edit_original_response(content=roll_history)

            if current_player is opponent:
                current_player = challenger
            else:
                current_player = opponent

        roll_history += f'\n**{current_player.display_name} wins!**'
        await interaction.edit_original_response(content=roll_history)


class Roll(discord.ui.View):
    def __init__(self, user: discord.Member):
        super().__init__()
        self.value = None
        self.user = user

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id == self.user.id:
            return True
        else:
            await interaction.response.send_message('It is not your turn.', ephemeral=True)
            return False

    @discord.ui.button(label='Roll', style=discord.ButtonStyle.blurple)
    async def roll(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(thinking=False)
        await interaction.delete_original_response()
        self.value = True
        self.stop()


async def setup(bot):
    await bot.add_cog(Deathroll(bot), guilds=[
        discord.Object(id=238145730982838272),
        discord.Object(id=699611111066042409)
    ])
