import asyncio
import datetime
import logging
import os

import discord
import psycopg2

from discord.ext import commands, tasks

from cogs.attendance import Attendance
from env import BOT_TOKEN, POSTGRESQL_SECRET, ATROCIOUS_ATTENDANCE_CHANNEL_ID, ATROCIOUS_GENERAL_CHANNEL_ID
from services.wow_server_status import update_area_52_server_status

DATE_FORMAT = '%Y-%m-%d'
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
    check_and_update_bot_attendance_msg.start()
    remove_past_absences.start()


async def load():
    for file in os.listdir('./cogs'):
        if file.endswith('.py'):
            await bot.load_extension(f'cogs.{file[:-3]}')


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if 'o7' in message.content.lower():
        await message.channel.send('o7')

    if 'bruh' in message.content.lower():
        await message.channel.send('bruh')

    await bot.process_commands(message)


@tasks.loop(minutes=1)
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


@tasks.loop(minutes=60)
async def check_and_update_bot_attendance_msg():
    attendance_channel = bot.get_channel(ATROCIOUS_ATTENDANCE_CHANNEL_ID)
    messages = [message async for message in attendance_channel.history(limit=1)]
    message = messages[0]

    if message.author.id != bot.user.id:
        attendance = Attendance(bot)
        await attendance.update_absences_table()


@tasks.loop(hours=24)
async def remove_past_absences():
    conn = psycopg2.connect(
        f'postgres://avnadmin:{POSTGRESQL_SECRET}@atrocious-bot-db-atrocious-bot.l.aivencloud.com:12047/defaultdb?sslmode=require'
    )
    current_date = datetime.datetime.now().strftime(DATE_FORMAT)

    try:
        with conn.cursor() as cursor:
            delete_record_query = """DELETE FROM attendance WHERE absence_date < %s"""
            cursor.execute(delete_record_query, (current_date,))
            conn.commit()
            logging.info('Removed past absence records successfully')
    except (Exception, psycopg2.Error) as e:
        logging.error(e)
        conn.close()


async def main():
    # DB Connection
    conn = psycopg2.connect(
        f'postgres://avnadmin:{POSTGRESQL_SECRET}@atrocious-bot-db-atrocious-bot.l.aivencloud.com:12047/defaultdb?sslmode=require'
    )

    query_sql = 'SELECT VERSION()'

    cur = conn.cursor()
    cur.execute(query_sql)

    version = cur.fetchone()[0]
    print(version)

    await load()
    await bot.start(BOT_TOKEN)


asyncio.run(main())
