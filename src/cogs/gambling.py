import asyncio
import random

import discord
from discord import app_commands
from discord.ext import commands

from utilities.sorting_algorithms import bubble_sort_dict

LAST_CALL_DELAY = 10
ROLL_REMINDER_INTERVAL = 15


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
    async def gamble(self, interaction: discord.Interaction, roll_amount: int = 10000, join_time_limit: int = 60,
                     game_time_limit: int = 60):
        if roll_amount < 1000:
            await interaction.response.send_message('Please enter an amount of at least 1000')
            return

        await interaction.response.send_message(f'{interaction.user.display_name} has started a game of gambling!\n')
        lobby_display = await interaction.followup.send(f'**__Players__**\n```{interaction.user.display_name}```')
        lobby_view = Lobby(lobby_display, interaction.user)
        lobby_view_interaction = await interaction.followup.send(view=lobby_view)

        loop = asyncio.get_event_loop()
        loop.call_later(join_time_limit, lambda: asyncio.ensure_future(
            self.start_game(interaction, lobby_view['player_list'], roll_amount, lobby_view, lobby_display,
                            lobby_view_interaction, game_time_limit)
        ))

    async def start_game(self, interaction: discord.Interaction, player_list, roll_amount, lobby_view, lobby_display,
                         lobby_view_interaction, game_time_limit):
        if len(player_list) < 2:
            await interaction.followup.send('Yikes, no one joined... Ending session.')
            lobby_view.stop()
            await lobby_view_interaction.delete()
            await lobby_display.delete()

            return

        lobby_view.stop()
        await lobby_view_interaction.delete()
        game_display = await interaction.followup.send(content=f'**__Rolls__**\n', wait=True)
        game_session_view = Game(player_list, roll_amount, game_display)
        roll_button = await interaction.followup.send(view=game_session_view)

        game_time = 0
        pending_rolls_msg = await interaction.followup.send(
            content=f'Please roll!\n{await self.get_remaining_rolls_string(game_session_view['player_list'])}',
            wait=True
        )

        while game_time < game_time_limit:
            wait_time = ROLL_REMINDER_INTERVAL

            if ((game_time + ROLL_REMINDER_INTERVAL) - game_time_limit) >= 0:
                wait_time = (game_time + ROLL_REMINDER_INTERVAL) % game_time_limit
                await asyncio.sleep(wait_time)

                if len(game_session_view['player_list']) > 0:
                    await pending_rolls_msg.edit(
                        content=f'LAST CALL!\n{await self.get_remaining_rolls_string(game_session_view['player_list'])}'
                    )
                else:
                    break

                await asyncio.sleep(LAST_CALL_DELAY)
                await roll_button.delete()
                await pending_rolls_msg.delete()
                await game_session_view.auto_roll()
            else:
                await asyncio.sleep(wait_time)

                if len(game_session_view['player_list']) > 0:
                    await pending_rolls_msg.edit(
                        content=f'Please Roll!\n{await self.get_remaining_rolls_string(game_session_view['player_list'])}'
                                f''
                    )
                else:
                    break

            if len(game_session_view['player_list']) == 0:
                break

            game_time += ROLL_REMINDER_INTERVAL

        await self.display_result(game_session_view, interaction)

    @staticmethod
    async def get_remaining_rolls_string(player_list):
        result = '```\n'

        for player in player_list:
            result += f'{player.display_name}\n'

        result += '```'

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
    def __init__(self, lobby_display, user: discord.Member):
        super().__init__()
        self.value = None
        self.user = user
        self.player_list = [user]
        self.lobby_players = [f'{user.display_name}']
        self.lobby_display = lobby_display

    def __getitem__(self, item):
        return getattr(self, item)

    @discord.ui.button(label='Join', style=discord.ButtonStyle.green)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        joined = False

        for player in self.player_list:
            if interaction.user.id == player.id:
                await interaction.response.send_message('You have already joined!', ephemeral=True)
                joined = True
                break

        if not joined:
            await interaction.response.send_message('You have joined the session.', ephemeral=True)
            self.player_list.append(interaction.user)
            self.lobby_players.append(f'\n{interaction.user.display_name}')
            lobby_msg = '\n'

            for player_string in self.lobby_players:
                lobby_msg += player_string

            await self.lobby_display.edit(content=f'**__Players__**```{lobby_msg}```')

    @discord.ui.button(label='Leave', style=discord.ButtonStyle.red)
    async def leave(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id == self.user.id:
            await interaction.response.send_message('You cannot leave a session you started!', ephemeral=True)

        joined = False

        for player in self.player_list:
            if player.id == interaction.user.id:
                joined = True
                break

        if joined:
            self.player_list.remove(interaction.user)
            self.lobby_players.remove(f'\n{interaction.user.display_name}')
            lobby_msg = ''

            for player_string in self.lobby_players:
                lobby_msg += player_string

            await self.lobby_display.edit(content=f'**__Players__**\n```{lobby_msg}```')
            await interaction.response.send_message('You have left the session.', ephemeral=True)
        else:
            await interaction.response.send_message('You never joined the session.', ephemeral=True)


class Game(discord.ui.View):
    def __init__(self, player_list, roll_amount, game_display):
        super().__init__()
        self.game_display = game_display
        self.player_list = player_list
        self.rolls_dict = []
        self.roll_amount = roll_amount + 1
        self.roll_msg = ''
        self.rolled = []
        self.left_adjust = 1

    def __getitem__(self, item):
        return getattr(self, item)

    async def auto_roll(self):
        for player in self.player_list:
            if len(player.display_name) > self.left_adjust:
                self.left_adjust = len(player.display_name)

        for player in self.player_list:
            roll = random.randrange(0, self.roll_amount)
            self.rolls_dict.append({player: roll})
            self.roll_msg += '\n' + f'{player.display_name}'.ljust(self.left_adjust) + f' - {roll}'

        await self.game_display.edit(content=f'**__Rolls__**```{self.roll_msg}```')

    @discord.ui.button(label='Roll', style=discord.ButtonStyle.blurple)
    async def roll(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user not in self.player_list and interaction.user not in self.rolled:
            await interaction.response.send_message('You cannot roll since you did not join this session.',
                                                    ephemeral=True)
        elif interaction.user in self.player_list:
            for player in self.player_list:
                if len(player.display_name) > self.left_adjust:
                    self.left_adjust = len(player.display_name)

            roll = random.randrange(0, self.roll_amount)
            self.rolls_dict.append({interaction.user: roll})
            # self.roll_msg = ''
            self.roll_msg += '\n' + f'{interaction.user.display_name}'.ljust(self.left_adjust) + f' - {roll}'
            self.player_list.remove(interaction.user)
            self.rolled.append(interaction.user)

            await interaction.response.send_message(f'You rolled {roll}.', ephemeral=True)
            await self.game_display.edit(content=f'**__Rolls__**```{self.roll_msg}```')
        else:
            await interaction.response.send_message('You have already rolled!', ephemeral=True)


async def setup(bot):
    await bot.add_cog(Gambling(bot), guilds=[
        discord.Object(id=238145730982838272),
        discord.Object(id=699611111066042409)
    ])
