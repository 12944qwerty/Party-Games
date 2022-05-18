import discord
from discord.ext import commands
from discord import app_commands
from .utils.constants import GROUP_GUILDS

class Bot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_group(name='info')
    @app_commands.guilds(*GROUP_GUILDS)
    async def info(self, ctx):
        """Info of bot through application_info"""
        app_info = await self.bot.application_info()
        em = discord.Embed(title=f"Info of {self.bot.user.display_name}", description=app_info.description)

        em.set_author(name=self.bot.user.display_name, icon_url=self.bot.user.display_avatar)
        await ctx.send(embed=em)

    @info.command(name='ping', aliases=['latency', 'shards'])
    async def ping(self, ctx):
        """Gets the latency of bot or shard latency"""
        em = discord.Embed(title='Pong!:ping_pong:')
        em.add_field(name='Bot Latency',value=f'{self.bot.latency}')
        for id, shard in self.bot.shards.items():
            em.add_field(name=f'Shard #{id} Latency', value=shard.latency)

        await ctx.send(embed=em)

    @info.command(name='status', aliases=['bot'])
    async def status(self, ctx):
        em = discord.Embed(title="__***Status***__ <a:online:512174327899226123>")
        em.add_field(name='Guild Count', value=len(self.bot.guilds))
        em.add_field(name='Shard Count', value=len(self.bot.shards))
        em.add_field(name='Shard ID', value=ctx.guild.shard_id)
        users = sum(len(guild.members)for guild in self.bot.guilds if guild.shard_id == ctx.guild.shard_id)
        em.add_field(name='Serving # of Users in Shard', value=users)
        await ctx.send(embed=em)


async def setup(bot):
    await bot.add_cog(Bot(bot))