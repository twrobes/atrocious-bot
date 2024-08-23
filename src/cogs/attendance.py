import logging
from datetime import datetime
import calendar

import discord
import psycopg2
from discord import app_commands
from discord.ext import commands

from env import POSTGRESQL_SECRET

ATROCIOUS_ATTENDANCE_CHANNEL_ID = 1270447537454715001
ABSENCE_DATE_COL = 1
USER_ID_COL = 0
DATE_FORMAT = '%Y-%m-%d'


class Attendance(commands.GroupCog, name='attendance'):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print('Attendance cog loaded.')

    @app_commands.command(
        name='add',
        description='Add a date that you will be absent'
    )
    async def add_absence(self, interaction: discord.Interaction, month: int, day: int):
        year = datetime.now().year
        error_string = Attendance.validate_date(month, day, year)

        if error_string:
            await interaction.response.send_message(error_string, ephemeral=True)
            return

        standard_date = Attendance.get_standardized_date_string(month, day, year)
        year_month_day = (standard_date.split('-')[0], standard_date.split('-')[1], standard_date.split('-')[2])

        conn = psycopg2.connect(
            f'postgres://avnadmin:{POSTGRESQL_SECRET}@atrocious-bot-db-atrocious-bot.l.aivencloud.com:12047/defaultdb?sslmode=require'
        )

        try:
            with conn.cursor() as cursor:
                get_record_query = """SELECT * FROM attendance WHERE user_id=%s AND absence_date=%s"""
                cursor.execute(get_record_query, (interaction.user.id, standard_date))
                attendance_records = cursor.fetchall()
        except (Exception, psycopg2.Error) as e:
            logging.error(e)
            await interaction.response.send_message(
                'Something went wrong while trying to retrieve data from the database. Please contact Foe for assistance.',
                ephemeral=True)
            conn.close()
            return

        if attendance_records:
            await interaction.response.send_message('You already have an absence set for this day.', ephemeral=True)
            conn.close()
            return

        try:
            date_obj = datetime.strptime(standard_date, DATE_FORMAT)
            with conn.cursor() as cursor:
                insert_absence_query = """INSERT INTO attendance (user_id, absence_date) VALUES (%s, %s)"""
                absence_record = (interaction.user.id, date_obj)
                cursor.execute(insert_absence_query, absence_record)
                conn.commit()
                logging.info(f'Successfully inserted {cursor.rowcount} absence record into the attendance table')
        except (Exception, psycopg2.Error) as e:
            logging.error(e)
            await interaction.response.send_message(
                'Something went wrong while trying to add the absence to the database. Please contact Foe for assistance.',
                ephemeral=True)
            return
        finally:
            conn.close()

        await interaction.response.send_message(
            f'Successfully added absence for {interaction.user.display_name} '
            f'on {year_month_day[1]}/{year_month_day[2]}/{year_month_day[0]}', ephemeral=True)

        return

    @app_commands.command(
        name='remove',
        description='Remove a date that you previously added as an absence'
    )
    async def remove_absence(self, interaction: discord.Interaction, month: int, day: int):
        year = datetime.now().year
        error_string = Attendance.validate_date(month, day, year)

        if error_string:
            await interaction.response.send_message(error_string, ephemeral=True)
            return

        standard_date = Attendance.get_standardized_date_string(month, day, year)
        year_month_day = (standard_date.split('-')[0], standard_date.split('-')[1], standard_date.split('-')[2])

        conn = psycopg2.connect(
            f'postgres://avnadmin:{POSTGRESQL_SECRET}@atrocious-bot-db-atrocious-bot.l.aivencloud.com:12047/defaultdb?sslmode=require'
        )

        try:
            with conn.cursor() as cursor:
                get_record_query = """SELECT * FROM attendance WHERE user_id=%s AND absence_date=%s"""
                cursor.execute(get_record_query, (interaction.user.id, standard_date))
                attendance_records = cursor.fetchall()
        except (Exception, psycopg2.Error) as e:
            logging.error(e)
            await interaction.response.send_message(
                'Something went wrong while trying to retrieve data from the database. Please contact Foe for assistance.',
                ephemeral=True)
            conn.close()
            return

        if not attendance_records:
            await interaction.response.send_message(
                f'You have not added an absence on {year_month_day[1]}/{year_month_day[2]}/{year_month_day[0]}. '
                f'Please input a date with an existing absence.', ephemeral=True)
            conn.close()
            return

        try:
            with conn.cursor() as cursor:
                delete_query = """DELETE FROM attendance WHERE user_id=%s AND absence_date=%s"""
                cursor.execute(delete_query, (interaction.user.id, standard_date))
                conn.commit()
                logging.info(f'Successfully deleted {cursor.rowcount} absence record from the attendance table')
        except (Exception, psycopg2.Error) as e:
            logging.error(e)
            await interaction.response.send_message(
                'Something went wrong while trying to delete the absence from the database. Please contact Foe for assistance.',
                ephemeral=True)
            return
        finally:
            conn.close()

        await interaction.response.send_message(
            f'Successfully removed absence for {interaction.user.display_name} '
            f'on {year_month_day[1]}/{year_month_day[2]}/{year_month_day[0]}', ephemeral=True)

        return

    @staticmethod
    def validate_date(month: int, day: int, year):
        # Bring back if command adds back 'year' as an input parameter
        # if year < datetime.now().year:
        #     return f'{year} occurred in the past. Please input a current or future date.'
        # elif year > datetime.now().year:
        #     return f'{year} is too far in the future, please input the current year.'

        if month < 1 or month > 12:
            return 'Month must be between 1-12.'
        elif year == datetime.now().year and month < datetime.now().month:
            return f'{month}/{day}/{year} occurred in the past. Please input a current or future date.'

        if day < 1 or day > 31:
            return 'Day must be between 1-31'
        elif datetime.now().month == 2 and (year % 4 == 0) and day > 29:
            return f'Day must not exceed 29 for February. {year} is a leap year.'
        elif datetime.now().month == 2 and (year % 4 > 0) and day > 28:
            return f'Day must not exceed 28 for February. {year} is not a leap year.'
        elif year == datetime.now().year and month == datetime.now().month and day < datetime.now().day:
            return f'{month}/{day}/{year} occurred in the past. Please input a current or future date.'

        match month:
            case 4, 6, 9, 11:
                if day > 30:
                    month_name = calendar.month_name[month]
                    return f'Day must not exceed 30 for {month_name}.'

        return ''

    @staticmethod
    def get_standardized_date_string(month: int, day: int, year: int):
        if day < 10:
            day_str = f'0{day}'
        else:
            day_str = f'{day}'

        if month < 10:
            month_str = f'0{month}'
        else:
            month_str = f'{month}'

        year_str = f'{year}'

        return f'{year_str}-{month_str}-{day_str}'

    @app_commands.command(name='test')
    async def update_embed(self, interaction: discord.Interaction):
        conn = psycopg2.connect(
            f'postgres://avnadmin:{POSTGRESQL_SECRET}@atrocious-bot-db-atrocious-bot.l.aivencloud.com:12047/defaultdb?sslmode=require'
        )

        try:
            with (conn.cursor() as cursor):
                cursor.execute("""SELECT * FROM attendance ORDER BY absence_date ASC""")
                records = cursor.fetchall()
        except (Exception, psycopg2.Error):
            logging.error("Could not fetch all records from the attendance table")
            await interaction.followup.send('An error occurred when trying to update the attendance message, please'
                                            'let Foe know about this error', ephemeral=True)
        finally:
            conn.close()

        attendance_channel = self.bot.get_channel(ATROCIOUS_ATTENDANCE_CHANNEL_ID)
        sticky_msg = discord.Embed(
            color=discord.Color.dark_embed(),
            title='Absences'
        )
        user_date_list = await Attendance.get_user_date_list(self, records)

        for month, absence_list in user_date_list.items():
            if not absence_list:
                continue

            value = ''

            for absence in absence_list:
                value += f'{absence}\n'

            sticky_msg.add_field(name=f'__{month}__', value=value)

        await attendance_channel.send(embed=sticky_msg)
        await interaction.response.send_message('Done.')

        return

    async def get_user_date_list(self, records: list):
        display_name_padding = await Attendance.get_ljust_dict(self, records)
        user_date_list = {
            'January': [],
            'February': [],
            'March': [],
            'April': [],
            'May': [],
            'June': [],
            'July': [],
            'August': [],
            'September': [],
            'October': [],
            'November': [],
            'December': [],
        }

        for user_id, absence_date in records:
            display_name = (await self.bot.fetch_user(user_id)).display_name

            match absence_date.month:
                case 1:
                    user_date_list['January'].append(
                        f'{display_name}' + ('᲼' * (display_name_padding['January'] - len(display_name))) +
                        f' - {absence_date.strftime("%a")}, {absence_date.day}{Attendance.get_day_suffix(absence_date.day)}'
                    )
                case 2:
                    user_date_list['February'].append(
                        f'{display_name}' + ('᲼' * (display_name_padding['February'] - len(display_name))) +
                        f' - {absence_date.strftime("%a")}, {absence_date.day}{Attendance.get_day_suffix(absence_date.day)}'
                    )
                case 3:
                    user_date_list['March'].append(
                        f'{display_name}' + ('᲼' * (display_name_padding['March'] - len(display_name))) +
                        f' - {absence_date.strftime("%a")}, {absence_date.day}{Attendance.get_day_suffix(absence_date.day)}'
                    )
                case 4:
                    user_date_list['April'].append(
                        f'{display_name}' + ('᲼' * (display_name_padding['April'] - len(display_name))) +
                        f' - {absence_date.strftime("%a")}, {absence_date.day}{Attendance.get_day_suffix(absence_date.day)}'
                    )
                case 5:
                    user_date_list['May'].append(
                        f'{display_name}' + ('᲼' * (display_name_padding['May'] - len(display_name))) +
                        f' - {absence_date.strftime("%a")}, {absence_date.day}{Attendance.get_day_suffix(absence_date.day)}'
                    )
                case 6:
                    user_date_list['June'].append(
                        f'{display_name}' + ('᲼' * (display_name_padding['June'] - len(display_name))) +
                        f' - {absence_date.strftime("%a")}, {absence_date.day}{Attendance.get_day_suffix(absence_date.day)}'
                    )
                case 7:
                    user_date_list['July'].append(
                        f'{display_name}' + ('᲼' * (display_name_padding['July'] - len(display_name))) +
                        f' - {absence_date.strftime("%a")}, {absence_date.day}{Attendance.get_day_suffix(absence_date.day)}'
                    )
                case 8:
                    user_date_list['August'].append(
                        f'{display_name}' + ('᲼' * (display_name_padding['August'] - len(display_name))) +
                        f' - {absence_date.strftime("%a")}, {absence_date.day}{Attendance.get_day_suffix(absence_date.day)}'
                    )
                case 9:
                    user_date_list['September'].append(
                        f'{display_name}' + ('᲼' * (display_name_padding['September'] - len(display_name))) +
                        f' - {absence_date.strftime("%a")}, {absence_date.day}{Attendance.get_day_suffix(absence_date.day)}'
                    )
                case 10:
                    user_date_list['October'].append(
                        f'{display_name}' + ('᲼' * (display_name_padding['October'] - len(display_name))) +
                        f' - {absence_date.strftime("%a")}, {absence_date.day}{Attendance.get_day_suffix(absence_date.day)}'
                    )
                case 11:
                    user_date_list['November'].append(
                        f'{display_name}' + ('᲼' * (display_name_padding['November'] - len(display_name))) +
                        f' - {absence_date.strftime("%a")}, {absence_date.day}{Attendance.get_day_suffix(absence_date.day)}'
                    )
                case 12:
                    user_date_list['December'].append(
                        f'{display_name}' + ('᲼' * (display_name_padding['December'] - len(display_name))) +
                        f' - {absence_date.strftime("%a")}, {absence_date.day}{Attendance.get_day_suffix(absence_date.day)}'
                    )
                case _:
                    logging.error(f'Month was not a valid date in class {self.__class__} in function update')

        return user_date_list

    async def get_ljust_dict(self, records):
        ljust_dict = {
            'January': 0,
            'February': 0,
            'March': 0,
            'April': 0,
            'May': 0,
            'June': 0,
            'July': 0,
            'August': 0,
            'September': 0,
            'October': 0,
            'November': 0,
            'December': 0,
        }

        for user_id, date in records:
            display_name = (await self.bot.fetch_user(user_id)).display_name

            if ljust_dict[date.strftime("%B")] < len(display_name):
                ljust_dict[date.strftime("%B")] = len(display_name)

        return ljust_dict

    @staticmethod
    def get_day_suffix(day: int):
        st = [1, 21, 31]
        nd = [2, 22]
        rd = [3, 23]

        if day in st:
            return 'st'
        elif day in nd:
            return 'nd'
        elif day in rd:
            return 'rd'
        else:
            return 'th'


async def setup(bot):
    await bot.add_cog(Attendance(bot), guilds=[
        discord.Object(id=238145730982838272),
        discord.Object(id=699611111066042409)
    ])
