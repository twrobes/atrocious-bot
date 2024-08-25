import logging
from datetime import datetime
import calendar
from typing import Tuple

import discord
import psycopg2
from discord import app_commands
from discord.ext import commands

from env import POSTGRESQL_SECRET, ATROCIOUS_ATTENDANCE_CHANNEL_ID

USER_ID_COL = 0
ABSENCE_DATE_COL = 1
START_DATE_COL = 1
END_DATE_COL = 2
DATE_FORMAT = '%Y-%m-%d'
USER_INPUT_DATE_FORMAT = '%m/%d/%Y'


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
    async def add_absence(self, interaction: discord.Interaction, month: int, day: int, user: discord.Member = None):
        is_officer = False
        user_id = interaction.user.id

        if user:
            for role in interaction.user.roles:
                if role.name == 'Officer':
                    is_officer = True

            if not is_officer:
                await interaction.response.send_message('You are not allowed to add an absence for another user. Please'
                                                        ' leave the optional "user" argument blank', ephemeral=True)
                return
            else:
                user_id = user.id

        year = datetime.now().year
        error_string = Attendance.validate_date(month, day, year)

        if error_string:
            await interaction.response.send_message(error_string, ephemeral=True)
            return

        standard_date = Attendance.get_standardized_date_string(month, day, year)

        conn = psycopg2.connect(
            f'postgres://avnadmin:{POSTGRESQL_SECRET}@atrocious-bot-db-atrocious-bot.l.aivencloud.com:12047/defaultdb?sslmode=require'
        )

        try:
            with conn.cursor() as cursor:
                get_record_query = """SELECT * FROM attendance WHERE user_id=%s AND absence_date=%s"""
                cursor.execute(get_record_query, (user_id, standard_date))
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
                absence_record = (user_id, date_obj)
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

        year_month_day = (standard_date.split('-')[0], standard_date.split('-')[1], standard_date.split('-')[2])
        await interaction.response.send_message(
            f'Successfully added absence for {(await self.bot.fetch_user(user_id)).display_name} '
            f'on {year_month_day[1]}/{year_month_day[2]}/{year_month_day[0]}', ephemeral=True)

        attendance_channel = self.bot.get_channel(ATROCIOUS_ATTENDANCE_CHANNEL_ID)
        messages = [message async for message in attendance_channel.history()]

        await attendance_channel.delete_messages(messages)
        await Attendance.update_embed(self, interaction)

        return

    @app_commands.command(
        name='remove',
        description='Remove a date that you previously added as an absence'
    )
    async def remove_absence(self, interaction: discord.Interaction, month: int, day: int, user: discord.Member = None):
        is_officer = False
        user_id = interaction.user.id

        if user:
            for role in interaction.user.roles:
                if role.name == 'Officer':
                    is_officer = True

            if not is_officer:
                await interaction.response.send_message(
                    'You are not allowed to remove an absence for another user. Please'
                    ' leave the optional "user" argument blank', ephemeral=True)
                return
            else:
                user_id = user.id

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
                cursor.execute(get_record_query, (user_id, standard_date))
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
                cursor.execute(delete_query, (user_id, standard_date))
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
            f'Successfully removed absence for {(await self.bot.fetch_user(user_id)).display_name} '
            f'on {year_month_day[1]}/{year_month_day[2]}/{year_month_day[0]}', ephemeral=True)

        attendance_channel = self.bot.get_channel(ATROCIOUS_ATTENDANCE_CHANNEL_ID)
        messages = [message async for message in attendance_channel.history()]

        await attendance_channel.delete_messages(messages)
        await Attendance.update_embed(self, interaction)

        return

    @app_commands.command(
        name='add_vacation',
        description='Add a date range when you will not be attending raid (ex: start=4/20/2024, end=6/9/2024)'
    )
    async def add_vacation(self, interaction: discord.Interaction, start: str, end: str):
        error_string = Attendance.validate_date_input(start)

        if error_string:
            await interaction.response.send_message(error_string, ephemeral=True)

        error_string = Attendance.validate_date_input(end)

        if error_string:
            await interaction.response.send_message(error_string, ephemeral=True)

        start_date = datetime.strptime(start, USER_INPUT_DATE_FORMAT)
        end_date = datetime.strptime(end, USER_INPUT_DATE_FORMAT)

        start_error_string = Attendance.validate_date(start_date.month, start_date.day, start_date.year)
        end_error_string = Attendance.validate_date(end_date.month, end_date.day, end_date.year)

        if start_error_string and end_error_string:
            await interaction.response.send_message(
                f'start and end both are invalid dates: '
                f'start - {start_error_string}, end - {end_error_string}', ephemeral=True)
            return
        if start_error_string:
            await interaction.response.send_message(f'start is an invalid date: {start_error_string}', ephemeral=True)
            return
        if end_error_string:
            await interaction.response.send_message(f'end is an invalid date: {end_error_string}', ephemeral=True)
            return

        conn = psycopg2.connect(
            f'postgres://avnadmin:{POSTGRESQL_SECRET}@atrocious-bot-db-atrocious-bot.l.aivencloud.com:12047/defaultdb?sslmode=require'
        )

        try:
            with conn.cursor() as cursor:
                cursor.execute("""SELECT * FROM vacation WHERE user_id=%s""", (interaction.user.id,))
                vacation_records = cursor.fetchall()
        except (Exception, psycopg2.Error) as e:
            logging.error(e)
            await interaction.response.send_message(
                'Something went wrong while trying to retrieve data from the database. Please contact Foe for assistance.',
                ephemeral=True)
            conn.close()
            return

        for record in vacation_records:
            if record[START_DATE_COL] <= start_date <= record[END_DATE_COL]:
                await interaction.response.send_message(
                    'Your start date cannot be within the range of an existing absence.', ephemeral=True)
                return

            if record[START_DATE_COL] <= end_date <= record[END_DATE_COL]:
                await interaction.response.send_message(
                    'Your end date cannot be within the range of an existing absence.', ephemeral=True)
                return

            if (start_date <= record[START_DATE_COL] <= end_date) or (start_date <= record[END_DATE_COL] <= end_date):
                await interaction.response.send_message(
                    'You cannot create an absence range that intersects an existing '
                    'absence.', ephemeral=True)
                return

        try:
            with conn.cursor() as cursor:
                insert_absence_query = """INSERT INTO vacation (user_id, start_date, end_date) VALUES (%s, %s, %s)"""
                vacation_record = (interaction.user.id, start_date, end_date)
                cursor.execute(insert_absence_query, vacation_record)
                conn.commit()
                logging.info(f'Successfully inserted {cursor.rowcount} vacation record into the attendance table')
        except (Exception, psycopg2.Error) as e:
            logging.error(e)
            await interaction.response.send_message(
                'Something went wrong while trying to add the vacation to the database. Please contact Foe for assistance.',
                ephemeral=True)
            return
        finally:
            conn.close()

        await interaction.response.send_message(
            f'Successfully added vacation between the dates of {start_date} - {end_date}', ephemeral=True)

    @app_commands.command(
        name='remove_vacation',
        description='Remove a date range when you will not be attending raid (ex: start=4/20/2024, end=6/9/2024)'
    )
    async def remove_vacation(self, interaction: discord.Interaction, start: str, end: str):
        error_string = Attendance.validate_date_input(start)

        if error_string:
            await interaction.response.send_message(error_string, ephemeral=True)

        error_string = Attendance.validate_date_input(end)

        if error_string:
            await interaction.response.send_message(error_string, ephemeral=True)

        start_date = datetime.strptime(start, USER_INPUT_DATE_FORMAT)
        end_date = datetime.strptime(end, USER_INPUT_DATE_FORMAT)

        start_error_string = Attendance.validate_date(start_date.month, start_date.day, start_date.year)
        end_error_string = Attendance.validate_date(end_date.month, end_date.day, end_date.year)

        if start_error_string and end_error_string:
            await interaction.response.send_message(
                f'start and end both are invalid dates: '
                f'start - {start_error_string}, end - {end_error_string}', ephemeral=True)
            return
        if start_error_string:
            await interaction.response.send_message(f'start is an invalid date: {start_error_string}', ephemeral=True)
            return
        if end_error_string:
            await interaction.response.send_message(f'end is an invalid date: {end_error_string}', ephemeral=True)
            return

        conn = psycopg2.connect(
            f'postgres://avnadmin:{POSTGRESQL_SECRET}@atrocious-bot-db-atrocious-bot.l.aivencloud.com:12047/defaultdb?sslmode=require'
        )

        try:
            with conn.cursor() as cursor:
                get_record_query = """SELECT * FROM vacation WHERE user_id=%s AND start_date=%s and end_date=%s"""
                cursor.execute(get_record_query, (interaction.user.id, start_date, end_date))
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
                f'You have not added a vacation from {start_date.month}/{start_date.day}/{start_date.year} to '
                f'{end_date.month}/{end_date.day}/{end_date.year}.'
                f'Please input a date with an existing absence.', ephemeral=True)
            conn.close()
            return

        try:
            with conn.cursor() as cursor:
                delete_query = """DELETE FROM vacation WHERE user_id=%s AND start_date=%s AND end_date=%s"""
                cursor.execute(delete_query, (interaction.user.id, start_date, end_date))
                conn.commit()
                logging.info(f'Successfully deleted {cursor.rowcount} vacation record from the attendance table')
        except (Exception, psycopg2.Error) as e:
            logging.error(e)
            await interaction.response.send_message(
                'Something went wrong while trying to delete the vacation from the database. Please contact Foe for assistance.',
                ephemeral=True)
            return
        finally:
            conn.close()

        await interaction.response.send_message(
            f'Successfully removed vacation for {interaction.user.display_name} '
            f'from {start_date.month}/{start_date.day}/{start_date.year} '
            f'to {end_date.month}/{end_date.day}/{end_date.year}.', ephemeral=True)

        attendance_channel = self.bot.get_channel(ATROCIOUS_ATTENDANCE_CHANNEL_ID)
        messages = [message async for message in attendance_channel.history()]

        await attendance_channel.delete_messages(messages)
        await Attendance.update_embed(self, interaction)

    @staticmethod
    def validate_date_input(date):
        if '/' not in date:
            return 'No "/" found in entered date.'

        date_parts = date.split('/')

        if len(date_parts) != 3:
            return 'You must enter month, day, and year only.'

        try:
            if int(date_parts[0]) < 1 or int(date_parts[0]) > 12:
                return 'You must enter a number between 1 and 12 for the month.'
        except ValueError:
            return 'You must enter a number between 1 and 12 for the month.'

        try:
            if int(date_parts[1]) < 1 or int(date_parts[1]) > 31:
                return 'You must enter a number between 1 and 31 for the day.'
        except ValueError:
            return 'You must enter a number between 1 and 12 for the day.'

        try:
            if int(date_parts[0]) < datetime.now().year or int(date_parts[0]) > datetime.now().year + 1:
                return f'You must enter a number between {datetime.now().year} and {datetime.now().year + 1} for the year.'
        except ValueError:
            return f'You must enter a number between {datetime.now().year} and {datetime.now().year + 1} for the year.'

        return ''

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

    async def update_embed(self, interaction: discord.Interaction):
        conn = psycopg2.connect(
            f'postgres://avnadmin:{POSTGRESQL_SECRET}@atrocious-bot-db-atrocious-bot.l.aivencloud.com:12047/defaultdb?sslmode=require'
        )

        try:
            with (conn.cursor() as cursor):
                cursor.execute("""SELECT * FROM attendance ORDER BY absence_date ASC""")
                attendance_records = cursor.fetchall()
                cursor.execute("""SELECT * FROM vacation ORDER BY start_date ASC""")
                vacation_records = cursor.fetchall()
        except (Exception, psycopg2.Error):
            logging.error("Could not fetch all records from the attendance table")
            await interaction.followup.send('An error occurred when trying to update the attendance message, please'
                                            'let Foe know about this error', ephemeral=True)
        finally:
            conn.close()

        if not attendance_records:
            logging.info('There are no absences, so not updating the embed')

        attendance_channel = self.bot.get_channel(ATROCIOUS_ATTENDANCE_CHANNEL_ID)
        sticky_msg = discord.Embed(
            color=discord.Color.dark_embed(),
            title='Absences'
        )
        is_empty, attendance_dates_dict, vacation_dates_list = await Attendance.get_user_date_list(
            self, attendance_records, vacation_records
        )

        if is_empty:
            sticky_msg.add_field(name='*There are no upcoming absences*', value='')
            await attendance_channel.send(embed=sticky_msg)
            return

        for month, absence_list in attendance_dates_dict.items():
            if not absence_list:
                continue

            value = ''

            for absence in absence_list:
                value += f'{absence}\n'

            sticky_msg.add_field(name=f'__{month}__', value=value)

        await attendance_channel.send(embed=sticky_msg)
        return

    async def get_user_date_list(self, attendance_records: list, vacation_records: list) -> Tuple[bool, dict, list]:
        absence_date_dict = {
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

        vacation_date_list = []
        attendance_is_empty = False

        if len(attendance_records) == 0 and len(vacation_records) == 0:
            attendance_is_empty = True

        for user_id, absence_date in attendance_records:
            standard_date = Attendance.get_standardized_date_string(
                absence_date.month, absence_date.day, absence_date.year
            )

            if datetime.strptime(standard_date, DATE_FORMAT) < datetime.now():
                continue

            display_name = (await self.bot.fetch_user(user_id)).display_name

            match absence_date.month:
                case 1:
                    absence_date_dict['January'].append(
                        f'{display_name}: ' +
                        f'{absence_date.strftime("%a")}, {absence_date.day}{Attendance.get_day_suffix(absence_date.day)}'
                    )
                case 2:
                    absence_date_dict['February'].append(
                        f'{display_name}: ' +
                        f'{absence_date.strftime("%a")}, {absence_date.day}{Attendance.get_day_suffix(absence_date.day)}'
                    )
                case 3:
                    absence_date_dict['March'].append(
                        f'{display_name}: ' +
                        f'{absence_date.strftime("%a")}, {absence_date.day}{Attendance.get_day_suffix(absence_date.day)}'
                    )
                case 4:
                    absence_date_dict['April'].append(
                        f'{display_name}: ' +
                        f'{absence_date.strftime("%a")}, {absence_date.day}{Attendance.get_day_suffix(absence_date.day)}'
                    )
                case 5:
                    absence_date_dict['May'].append(
                        f'{display_name}: ' +
                        f'{absence_date.strftime("%a")}, {absence_date.day}{Attendance.get_day_suffix(absence_date.day)}'
                    )
                case 6:
                    absence_date_dict['June'].append(
                        f'{display_name}: ' +
                        f'{absence_date.strftime("%a")}, {absence_date.day}{Attendance.get_day_suffix(absence_date.day)}'
                    )
                case 7:
                    absence_date_dict['July'].append(
                        f'{display_name}: ' +
                        f'{absence_date.strftime("%a")}, {absence_date.day}{Attendance.get_day_suffix(absence_date.day)}'
                    )
                case 8:
                    absence_date_dict['August'].append(
                        f'{display_name}: ' +
                        f'{absence_date.strftime("%a")}, {absence_date.day}{Attendance.get_day_suffix(absence_date.day)}'
                    )
                case 9:
                    absence_date_dict['September'].append(
                        f'{display_name}: ' +
                        f'{absence_date.strftime("%a")}, {absence_date.day}{Attendance.get_day_suffix(absence_date.day)}'
                    )
                case 10:
                    absence_date_dict['October'].append(
                        f'{display_name}: ' +
                        f'{absence_date.strftime("%a")}, {absence_date.day}{Attendance.get_day_suffix(absence_date.day)}'
                    )
                case 11:
                    absence_date_dict['November'].append(
                        f'{display_name}: ' +
                        f'{absence_date.strftime("%a")}, {absence_date.day}{Attendance.get_day_suffix(absence_date.day)}'
                    )
                case 12:
                    absence_date_dict['December'].append(
                        f'{display_name}: ' +
                        f'{absence_date.strftime("%a")}, {absence_date.day}{Attendance.get_day_suffix(absence_date.day)}'
                    )
                case _:
                    logging.error(f'Month was not a valid date in class {self.__class__} in function update')

        for user_id, start_date, end_date in vacation_records:
            display_name = (await self.bot.fetch_user(user_id)).display_name
            vacation_date_list.append(f'{display_name}: {start_date.month}/{start_date.day}/{start_date.year} to '
                                      f'{end_date.month}/{end_date.day}/{end_date.year}')

        return attendance_is_empty, absence_date_dict, vacation_date_list

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
