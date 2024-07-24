import asyncio
import random

import discord
from discord import app_commands
from discord.ext import commands

from utilities.sorting_algorithms import bubble_sort_dict

JOIN_TIME_LIMIT = 2
GAME_TIME_LIMIT = 30
REQUEST_ROLL_TIME = 8


class Gambling(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print('Gambling cog loaded.')

    @app_commands.command(
        name='gamble',
        description='Start a gambling session.'
    )
    async def gamble(self, interaction: discord.Interaction, amount: int):
        if amount < 1000:
            await interaction.response.send_message('Please enter an amount of at least 1000')
            return

        lobby_view = Lobby(interaction.user)
        await interaction.response.send_message(f'{interaction.user.display_name} has started a game of gambling!',
                                                view=lobby_view)

        loop = asyncio.get_event_loop()
        loop.call_later(JOIN_TIME_LIMIT, lambda: asyncio.ensure_future(
            self.start_game(interaction, lobby_view['player_list'], amount, lobby_view)
        ))

    async def start_game(self, interaction: discord.Interaction, player_list, roll_amount, lobby_view):
        # if len(player_list) < 2:
        #     await interaction.followup.send('Yikes, no one joined... Ending session.')
        #     lobby_view.stop()
        #     await interaction.delete_original_response()
        #
        #     return

        lobby_view.stop()
        await interaction.delete_original_response()
        game_display = await interaction.followup.send(content=f'```Rolls:```', wait=True)
        game_session_view = Game(player_list, roll_amount, game_display)
        await interaction.followup.send(view=game_session_view)

        game_time = 0

        while game_time < GAME_TIME_LIMIT:
            wait_time = REQUEST_ROLL_TIME

            if ((game_time + REQUEST_ROLL_TIME) - GAME_TIME_LIMIT) > 0:
                wait_time = (game_time + REQUEST_ROLL_TIME) % GAME_TIME_LIMIT
                await asyncio.sleep(wait_time)

                if len(game_session_view['player_list']) == 1:
                    await interaction.followup.send(
                        f'LAST CALL!\n{await self.get_remaining_rolls_string(game_session_view['player_list'])} '
                        f'still needs to roll!')
                else:
                    await interaction.followup.send(
                        f'LAST CALL!\n{await self.get_remaining_rolls_string(game_session_view['player_list'])} '
                        f'still need to roll!')

                await asyncio.sleep(10)
                await game_session_view.auto_roll()
                await self.display_result(game_session_view, interaction)
            else:
                await asyncio.sleep(wait_time)

                if len(game_session_view['player_list']) == 1:
                    await interaction.followup.send(
                        f'{await self.get_remaining_rolls_string(game_session_view['player_list'])}'
                        f'still needs to roll!')
                else:
                    await interaction.followup.send(
                        f'{await self.get_remaining_rolls_string(game_session_view['player_list'])}still need to roll!')

            game_time += REQUEST_ROLL_TIME

    @staticmethod
    async def get_remaining_rolls_string(player_list):
        result = '```\n'

        for player in player_list:
            result += f'{player.display_name}\n'

        result += '```'
        print(result)
        return result

    @staticmethod
    async def display_result(game_session_view, interaction: discord.Interaction):
        rolls_dict = game_session_view['rolls_dict']
        sorted_rolls_dict = bubble_sort_dict(rolls_dict)

        loser_roll = next(iter(sorted_rolls_dict[0].values()))
        winner_roll = next(iter(sorted_rolls_dict[len(sorted_rolls_dict) - 1].values()))
        roll_difference = winner_roll - loser_roll
        loser_name = next(iter(sorted_rolls_dict[0].keys())).display_name
        winner_name = next(iter(sorted_rolls_dict[len(sorted_rolls_dict) - 1])).display_name

        await interaction.followup.send(f'{loser_name} owes {winner_name} {roll_difference} gold.')
        game_session_view.stop()

        return


class Lobby(discord.ui.View):
    def __init__(self, user: discord.Member):
        super().__init__()
        self.value = None
        self.user = user
        self.player_list = [user]

    def __getitem__(self, item):
        return getattr(self, item)

    @discord.ui.button(label='Join', style=discord.ButtonStyle.green)
    async def join_test(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id in self.player_list:
            await interaction.response.send_message('You have already joined!')
        else:
            self.player_list.append(interaction.user)
            await interaction.response.send_message('You have joined the session.')

    @discord.ui.button(label='Leave', style=discord.ButtonStyle.red)
    async def leave(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id == self.user.id:
            await interaction.response.send_message('You cannot leave a session you started!')
        elif interaction.user.id in self.player_list:
            self.player_list.remove(interaction.user)
            await interaction.response.send_message('You have left the session.')
        else:
            await interaction.response.send_message('You never joined the session.')


class Game(discord.ui.View):
    def __init__(self, player_list, roll_amount, game_display):
        super().__init__()
        self.game_display = game_display
        self.player_list = player_list
        self.rolls_dict = []
        self.roll_amount = roll_amount + 1
        self.roll_msg = 'Rolls:\n'
        self.rolled = []

    def __getitem__(self, item):
        return getattr(self, item)

    async def auto_roll(self):
        for player in self.player_list:
            roll = random.randrange(0, self.roll_amount)
            self.rolls_dict.append({player: roll})
            self.roll_msg += f'\n{player.display_name} rolled {roll}'
            self.player_list.remove(player)
            await self.game_display.edit(content=f'```{self.roll_msg}```')

    @discord.ui.button(label='Roll', style=discord.ButtonStyle.blurple)
    async def roll(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user not in self.player_list and interaction.user not in self.rolled:
            await interaction.response.send_message('You cannot roll since you did not join this session.',
                                                    ephemeral=True)
        elif interaction.user in self.player_list:
            roll = random.randrange(0, self.roll_amount)
            self.rolls_dict.append({interaction.user: roll})
            self.roll_msg += f'\n{interaction.user.display_name} rolled {roll}'
            self.player_list.remove(interaction.user)
            self.rolled.append(interaction.user)

            await interaction.response.send_message(f'You rolled {roll}.', ephemeral=True)
            await self.game_display.edit(content=f'```{self.roll_msg}```')
        else:
            await interaction.response.send_message('You have already rolled!')


async def setup(bot):
    await bot.add_cog(Gambling(bot), guilds=[
        discord.Object(id=238145730982838272),
        discord.Object(id=699611111066042409)
    ])
