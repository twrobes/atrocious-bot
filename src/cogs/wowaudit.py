import json

import discord
from discord import app_commands
from discord.ext import commands

from services.wowaudit_service import post_wishlist

# Constants
wowaudit_json_path = 'resources/wowaudit_character_list.json'


class Wowaudit(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print('Wowaudit cog loaded.')

    @commands.command()
    async def sync(self, ctx):
        fmt = await ctx.bot.tree.sync(guild=ctx.guild)
        await ctx.send(f'Synced {len(fmt)} commands.')

    @app_commands.command(
        name='update-wishlist',
        description='Updates a character wishlist in wowaudit',
    )
    # @app_commands.guilds(discord.Object(id='238145730982838272'))
    async def update_wishlist(self, interaction: discord.Interaction, character_name: str, link: str):
        await interaction.response.send_message('Request received...')

        if link.find('raidbots') != -1:  # Raidbots
            report_id = link[-22:]
        else:  # QE Live
            report_id = link[-12:]

        print(report_id)
        character_list = self.get_character_list_dict()

        if character_list is None or len(character_list) == 0:
            await interaction.followup.send(
                'An internal error has occurred. Please DM Foe a screenshot of the command and this response. '
                'The character_list was None or empty.')
            return

        name_found = False
        is_success = False
        error = ''

        for item in character_list:
            if item['name'].lower() == character_name.lower():
                name_found = True
                is_success, error = await post_wishlist(character_name, report_id)
                break

        if name_found:
            if is_success:
                await interaction.followup.send('Wishlist updated successfully!', ephemeral=True)
            else:
                await interaction.followup.send(
                    f'Something went wrong and your wishlist was not updated. Please check your report id and '
                    f'character id are valid.\n\nWowaudit had an issue accepting the report: ```{error}```', ephemeral=True)
        else:
            await interaction.followup.send(
                f'`{character_name}` was not found. Please try again with a different name or use the '
                f'`!character_list` command to see a list of valid character names.', ephemeral=True)

    @app_commands.command(name='character-list', description='Get the list of valid characters from wowaudit')
    async def _character_list(self, interaction: discord.Interaction):
        character_string = '```'
        character_list = self.get_character_list_dict()

        if character_list is None:
            await interaction.response.send_message(
                'Could not retrieve character list. Please DM Foe a screenshot of the command and this response.',
                ephemeral=True
            )
            return

        for item_idx, item in enumerate(character_list):
            item_name = item['name']

            if item_idx % 4 == 3 and item_idx != len(character_list) - 1:

                character_string += f'{item_name},\n'
            elif item_idx == len(character_list) - 1:
                character_string += f'{item_name}'
            else:
                character_string += f'{item_name}, '

        character_string += '```'

        await interaction.response.send_message(character_string, ephemeral=True)

    @staticmethod
    def get_character_list_dict():
        try:
            file = open(wowaudit_json_path)
            character_dict = json.load(file)
            file.close()

            return character_dict
        except FileNotFoundError as fnf:
            print(f'ERROR - Character JSON file not found: {fnf}')
            return None


async def setup(bot):
    await bot.add_cog(Wowaudit(bot), guilds=[
        discord.Object(id=238145730982838272),
        discord.Object(id=699611111066042409)
    ])
