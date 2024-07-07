import discord
import time

from discord.ext import commands

from env import bot_token

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)


@bot.event
async def on_ready():
    await bot.load_extension('commands')
    print(f'We have logged in as {bot.user}')


@bot.listen()
async def on_message(message):
    if message.author == bot.user:
        return

    if 'hello' in message.content.lower():
        await message.channel.send('Hello!')

    if 'o7' in message.content.lower():
        for i in range(5):
            time.sleep(0.1)
            await message.channel.send('o7')

    if 'bruh' in message.content.lower():
        await message.channel.send('bruh')


bot.run(bot_token)
