from discord.ext import commands
import discord
from .utils.constants import GROUP_GUILDS

class DevCommands(commands.Cog, name='Developer Commands', command_attrs=dict(hidden=True)):

    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        is_owner = await self.bot.is_owner(ctx.author)
        return is_owner

    @commands.command(name='sync')
    async def sync_slash(self, ctx):
        """Syncs the slash command tree"""
        for guild in GROUP_GUILDS:
            await self.bot.tree.sync(guild=guild)

        await ctx.send("Synced Slash Command Tree")
        print("Synced Tree")

    @commands.command(name='reload', aliases=['rl'])  
    async def reload(self, ctx, cog):
        '''
        Reloads a cog.
        '''
        extensions = self.bot.extensions
        if cog == 'all':
            for extension in extensions:
                await self.bot.reload_extension(cog)
            await ctx.send('Done')
        if cog in extensions:
            await self.bot.reload_extension(cog)
            await ctx.send('Done')
        elif "cogs."+cog in extensions:
            await self.bot.reload_extension('cogs.'+cog)
            await ctx.send('Done')
        else:
            await ctx.send('Unknown Cog')
    
    @commands.command(name="unload", aliases=['ul']) 
    async def unload(self, ctx, cog):
        '''
        Unload a cog.
        '''
        extensions = self.bot.extensions
        if cog not in extensions:
            await ctx.send("Cog is not loaded!")
            return
        await self.bot.unload_extension(cog)
        await ctx.send(f"`{cog}` has successfully been unloaded.")
    
    @commands.command(name="load")
    async def load(self, ctx, cog):
        '''
        Loads a cog.
        '''
        try:

            await self.bot.load_extension(cog)
            await ctx.send(f"`{cog}` has successfully been loaded.")

        except commands.errors.ExtensionNotFound:
            await ctx.send(f"`{cog}` does not exist!")

    @commands.command(name="listcogs", aliases=['lc'])
    async def listcogs(self, ctx):
        '''
        Returns a list of all enabled commands.
        '''
        base_string = "```css\n" 
        base_string += "\n".join([str(cog) for cog in self.bot.extensions])
        base_string += "\n```"
        await ctx.send(base_string)


async def setup(bot):
    await bot.add_cog(DevCommands(bot))
