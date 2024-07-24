import asyncio
import logging
import os

import discord

from discord.ext import commands, tasks

from env import BOT_TOKEN
from services.wow_server_status import update_area_52_server_status

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


@tasks.loop(seconds=5)
async def update_bot_status():
    await update_area_52_server_status(bot)


async def main():
    await load()
    await bot.start(BOT_TOKEN)


asyncio.run(main())
