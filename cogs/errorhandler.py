from discord.ext import commands
import discord
import asyncio

class CommandErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """The event triggered when an error is raised while invoking a command.
        ctx   : Context
        error : Exception"""

        error = getattr(error, 'original', error)

        # if isinstance(error, ignored):
            # return
        
        msg = None
        if isinstance(error, commands.CommandNotFound):
            if ctx.guild == 862180360610643999:
                msg = await ctx.em(title="Command Not Found", description=str(error), bot=self.bot)
            else:
                return

        elif isinstance(error, commands.DisabledCommand):
            if ctx.guild == 862180360610643999:
                msg = await ctx.em(title="Disabled Command", description=str(error), bot=self.bot)
            else:
                return

        elif isinstance(error, commands.NoPrivateMessage):
            if ctx.guild == 862180360610643999:
                try:
                    em = discord.Embed(title="No Private Message", description=str(error))
                    em.set_author(name=self.bot.user.display_name, icon_url=self.bot.user.avatar_url)

                    msg = await ctx.author.send(embed=em)
                except Exception:
                    pass
            else:
                return

        elif isinstance(error, commands.BadArgument):
            print(error)
            msg = await ctx.em(title='Bad Argument', description=str(error), bot=self.bot)

        elif isinstance(error, commands.BotMissingPermissions):
            return await ctx.send('I am missing these permissions to do this command:'
                                  f'\n{self.lts(error.missing_perms)}')

        elif isinstance(error, commands.MissingPermissions):
            return await ctx.send('You are missing these permissions to do this command:'
                                  f'\n{self.lts(error.missing_perms)}')

        elif isinstance(error, (commands.BotMissingAnyRole, commands.BotMissingRole)):
            return await ctx.send(f'I am missing these roles to do this command:'
                                  f'\n{self.lts(error.missing_roles or [error.missing_role])}')

        elif isinstance(error, (commands.MissingRole, commands.MissingAnyRole)):
            return await ctx.send(f'You are missing these roles to do this command:'
                                  f'\n{self.lts(error.missing_roles or [error.missing_role])}')

        elif isinstance(error, commands.CommandInvokeError):
            if ctx.guild == 862180360610643999:
                await ctx.em(title="Command Invoke Error", description=str(error), bot=self.bot)
            else: return

        elif isinstance(error, commands.CommandOnCooldown):
            after = error.retry_after
            sec = divmod(after, 60)[1]
            min_ = divmod(divmod(after, 60)[0], 60)[1]
            hours = divmod(divmod(after, 60)[0], 60)[0]
            msg = await ctx.em(title="Error", description=f'Please wait another `{hours}` hours and `{min_}` minutes and `{sec}` secs', bot=self.bot)
        
        elif isinstance(error, commands.MissingRequiredArgument):
            arg = error.param

        else:
            await ctx.em(title=str(error.__class__.__name__), description=str(error), bot=self.bot)

        if type(msg) == discord.Message:
            await asyncio.sleep(5.0)
            await msg.delete()

    @staticmethod
    def lts(list_: list):
        """List to string.
           For use in `self.on_command_error`"""
        return ', '.join([obj.name if isinstance(obj, discord.Role) else str(obj).replace('_', ' ') for obj in list_])

async def setup(bot):
    await bot.add_cog(CommandErrorHandler(bot))
