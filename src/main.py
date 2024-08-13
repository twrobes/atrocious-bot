import asyncio
import logging
import os

import discord

from discord.ext import commands, tasks

from env import BOT_TOKEN
from services.wow_server_status import update_area_52_server_status

ATROCIOUS_GENERAL_CHANNEL_ID = 699611111594393613
DOWN = 'DOWN'
UP = 'UP'

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
discord.utils.setup_logging(handler=handler, level=logging.DEBUG)

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents, application_id='1228562180409131009')


@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    update_bot_status.start()


async def load():
    for file in os.listdir('./cogs'):
        if file.endswith('.py'):
            await bot.load_extension(f'cogs.{file[:-3]}')


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if 'hello' in message.content.lower():
        await message.channel.send('Hello!')

    if 'o7' in message.content.lower():
        await message.channel.send('o7')

    if 'bruh' in message.content.lower():
        await message.channel.send('bruh')

    await bot.process_commands(message)


@tasks.loop(minutes=5)
async def update_bot_status():
    server_status = await update_area_52_server_status()
    guild = bot.get_guild(699611111066042409)

    channel_to_msg = bot.get_channel(ATROCIOUS_GENERAL_CHANNEL_ID)
    # TODO: Bring back for opt-in roles
    # raider_role_id = 699622512174301266
    # trial_role_id = 699667525964660826

    if server_status == UP:
        status_msg = 'Area-52 is online'
    else:
        status_msg = 'Area-52 is offline'

    if guild.me.activity is None:
        activity = discord.CustomActivity(name=status_msg)
        await bot.change_presence(activity=activity)
    elif status_msg != guild.me.activity.name:
        activity = discord.CustomActivity(name=status_msg)
        await bot.change_presence(activity=activity)

        # TODO: Create opt-in roles
        # trimmed_status_msg = status_msg.split(' ')[2]
        # await channel_to_ping.send(
        #     f'<@&{raider_role_id}><@&{trial_role_id}> Area-52 is now {trimmed_status_msg}.'
        # )

        trimmed_status_msg = status_msg.split(' ')[2]
        await channel_to_msg.send(
            f'Area-52 is now {trimmed_status_msg}.'
        )


async def main():
    await load()
    await bot.start(BOT_TOKEN)


asyncio.run(main())
