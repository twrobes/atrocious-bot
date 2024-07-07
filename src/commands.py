import json

from discord.ext import commands

from wowaudit import post_wishlist

# Constants
wowaudit_json_path = 'resources/wowaudit_character_list.json'


@commands.command()
async def test(ctx, arg):
    await ctx.send(arg)


@commands.command()
async def update_wishlist(ctx, character_name, link):
    await ctx.send('Request received...')

    if link.find('raidbots') != -1:  # Raidbots
        report_id = link[-22:]
    else:  # QE Live
        report_id = link[-12:]

    print(report_id)
    character_list = get_character_list_dict()

    if character_list is None or len(character_list) == 0:
        await ctx.send('An internal error has occurred. Please DM Foe a screenshot of the command and this response. '
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
            await ctx.send('Wishlist updated successfully!')
        else:
            await ctx.send(f'Something went wrong and your wishlist was not updated. Please check your report id and '
                           f'character id are valid.\n\nWowaudit had an issue accepting the report: ```{error}```')
    else:
        await ctx.send(f'`{character_name}` was not found. Please try again with a different name or use the '
                       f'`!character_list` command to see a list of valid character names.')


@commands.command(name='character_list')
async def _character_list(ctx):
    character_string = '```'
    character_list = get_character_list_dict()

    if character_list is None:
        print(character_list)
        await ctx.send(
            'Could not retrieve character list. Please DM Foe a screenshot of the command and this response.'
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

    await ctx.send(character_string)


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
    print('Commands loaded')
    bot.add_command(test)
    bot.add_command(update_wishlist)
    bot.add_command(_character_list)
