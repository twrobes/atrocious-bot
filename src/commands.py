from discord.ext import commands

from wowaudit import post_wishlist


@commands.command()
async def test(ctx, arg):
    await ctx.send(arg)


@commands.command()
async def update_wishlist(ctx, report_id, character_id):
    await ctx.send('Request received...')

    is_success = await post_wishlist(report_id, character_id)

    if is_success:
        await ctx.send('Wishlist updated successfully!')
    else:
        await ctx.send('Something went wrong and your wishlist was not updated. Please check your report id and '
                       'character id are valid')


async def setup(bot):
    print('Commands loaded')
    bot.add_command(test)
    bot.add_command(update_wishlist)
