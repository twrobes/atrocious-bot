import asyncio
import logging
import os

import discord

from discord.ext import commands

from env import bot_token

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
discord.utils.setup_logging(handler=handler, level=logging.DEBUG)

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents, application_id='1228562180409131009')


@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')


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


async def main():
    await load()
    await bot.start(bot_token)


asyncio.run(main())
