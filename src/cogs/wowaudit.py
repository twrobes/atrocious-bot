import json
import logging

import discord
from discord import app_commands
from discord.ext import commands

from services.wowaudit_service import post_wishlist, get_character_list

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
        name='roster',
        description='WIP. Displays the current roster for the week.'
    )
    async def roster(self, interaction: discord.Interaction):
        await interaction.response.send_message(file=discord.File('resources/yam_roster.png'))

    @app_commands.command(
        name='update-wishlist',
        description='Updates a character wishlist in wowaudit',
    )
    async def update_wishlist(self, interaction: discord.Interaction, character_name: str, link: str):
        await interaction.response.send_message('Request received...')

        if link.find('raidbots') != -1:  # Raidbots
            report_id = link[-22:]
        else:  # QE Live
            report_id = link[-12:]

        is_populated, character_list = await get_character_list()

        if not is_populated:
            await interaction.followup.send(
                'An internal error has occurred. Please DM Foe a screenshot of the command and this response. '
                'The character_list was None or empty.', ephemeral=True)
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
                await interaction.followup.send('Request processed successfully.')
            else:
                logging.error(f"Attempt to update {character_name}'s wishlist was not successful using link: {link}, "
                              f"error: {error}")
                await interaction.followup.send(
                    f'Something went wrong and your wishlist was not updated. Please check your report link and '
                    f'character id are valid.\n\nWowaudit had an issue accepting the report: ```{error}```',
                    ephemeral=True)
        else:
            await interaction.followup.send(
                f'`{character_name}` was not found. Please try again with a different name or use the '
                f'`/character_list` command to see a list of valid character names.', ephemeral=True)

    @app_commands.command(name='character-list', description='Get the list of valid characters from wowaudit')
    async def _character_list(self, interaction: discord.Interaction):
        character_string = '```'
        is_populated, character_list = await get_character_list()

        if not is_populated:
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


async def setup(bot):
    await bot.add_cog(Wowaudit(bot), guilds=[
        discord.Object(id=238145730982838272),
        discord.Object(id=699611111066042409)
    ])
