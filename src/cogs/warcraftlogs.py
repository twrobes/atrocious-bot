import aiohttp
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

    @app_commands.command(
        name='rank',
        description='Shows the rank of the guild in the current raid tier'
    )
    async def rank(self, interaction: discord.Interaction):
        url = 'https://raider.io/api/v1/guilds/profile'
        params = {
            'region': 'us',
            'realm': 'Area 52',
            'name': 'Atrocious',
            'fields': 'raid_rankings'
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                rank_json = await response.json()

        if response.ok and rank_json is not None:
            await interaction.response.send_message(
                f'__Awakened Vault of the Incarnates__\n'
                f'```World  - {rank_json["raid_rankings"]["awakened-vault-of-the-incarnates"]["mythic"]["world"]}\n'
                f'Region - {rank_json["raid_rankings"]["awakened-vault-of-the-incarnates"]["mythic"]["region"]}\n'
                f'Realm  - {rank_json["raid_rankings"]["awakened-vault-of-the-incarnates"]["mythic"]["realm"]}```\n'

                f'__Awakened Aberrus, the Shadowed Crucible__\n'
                f'```World  - {rank_json["raid_rankings"]["awakened-aberrus-the-shadowed-crucible"]["mythic"]["world"]}\n'
                f'Region - {rank_json["raid_rankings"]["awakened-aberrus-the-shadowed-crucible"]["mythic"]["region"]}\n'
                f'Realm  - {rank_json["raid_rankings"]["awakened-aberrus-the-shadowed-crucible"]["mythic"]["realm"]}```\n'

                f'__Awakened Amirdrassil, the Dream\'s Hope__\n'
                f'```World  - {rank_json["raid_rankings"]["awakened-amirdrassil-the-dreams-hope"]["mythic"]["world"]}\n'
                f'Region - {rank_json["raid_rankings"]["awakened-amirdrassil-the-dreams-hope"]["mythic"]["region"]}\n'
                f'Realm  - {rank_json["raid_rankings"]["awakened-amirdrassil-the-dreams-hope"]["mythic"]["realm"]}```'
            )
        else:
            await interaction.response.send_message(
                'An error has occurred. Please DM Foe a screenshot of the command and this response.'
            )


async def setup(bot):
    await bot.add_cog(Warcraftlogs(bot), guilds=[
        discord.Object(id=238145730982838272),
        discord.Object(id=699611111066042409)
    ])
