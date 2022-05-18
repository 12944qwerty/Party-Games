import discord
from discord.ext import commands
import asyncio
from datetime import datetime as dt
import typing

DESC = """A discord bot.
Use `.help "cog name"` for more info on a cog.
"""

def make_embed(cog_chosen, bot, ctx):
    embed = discord.Embed(
        title=f"{cog_chosen.__cog_name__} Help",
        description=cog_chosen.description,
        timestamp=dt.utcnow()
    )

    embed.set_author(name=bot.user.display_name, icon_url=bot.user.display_avatar)

    for cmd in cog_chosen.walk_commands():
        if y:=isinstance(cmd, discord.app_commands.Command):
            continue
        else:
            desc = cmd.help
            pre = ctx.clean_prefix
            sign = cmd.signature
            
        embed.add_field(
            name=f"{pre}{cmd.qualified_name} {sign}{' | ' + ', '.join(cmd.aliases) if (not y) and cmd.aliases else ''}",
            value=desc or "_No Description Found_",
            # inline=False
        )
        
    return embed

class Dropdown(discord.ui.Select):
    def __init__(self, bot, ctx, default_cog):
        options = []
        for name, cog in bot.cogs.items():
            cog_settings = cog.__cog_settings__

            if not ("hidden" in cog_settings and cog_settings["hidden"]) and name not in ("Jishaku", "CommandErrorHandler") and len(cog.get_commands()) > 0:
                options.append(
                    discord.SelectOption(label=name, description=cog.description)
                )
        
        super().__init__(
            placeholder="Choose a cog to get help on",
            min_values=1,
            max_values=1,
            options=options,
        )
        self.bot = bot
        self.ctx = ctx

    async def callback(self, interaction: discord.Interaction):
        cog_chosen = self.bot.cogs[self.values[0]]
        
        embed = make_embed(cog_chosen, self.bot, self.ctx)
        
        await interaction.message.edit(embed=embed)


class DropdownView(discord.ui.View):
    def __init__(self, bot, ctx, default_cog):
        super().__init__()

        # Adds the dropdown to our view object.
        self.bot = bot
        self.ctx = ctx
        self.add_item(Dropdown(self.bot, self.ctx, default_cog))

class HelpCommand(commands.Cog, name="Help Command"):
    """This help command you're using!"""
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help")
    async def send_help(self, ctx, *, default_cog:typing.Optional[str]):
        """Shows this message"""        
        embed = discord.Embed(
            title=f"General Help",
            description=DESC,
            timestamp=dt.utcnow()
        )
        
        for name, cog in self.bot.cogs.items():
            cog_settings = cog.__cog_settings__

            if not ("hidden" in cog_settings and cog_settings["hidden"]) and name not in ("Jishaku", "CommandErrorHandler") and len(cog.get_commands()) > 0:
                embed.add_field(
                    name=name,
                    value=cog.description or "_No Description Found_",
                    # inline=False
                )

        embed.set_author(name=self.bot.user.display_name, icon_url=self.bot.user.display_avatar)

        if default_cog:
            if default_cog in self.bot.cogs:
                embed = make_embed(self.bot.cogs[default_cog], self.bot, ctx)
            else:
                embed.description += f"`{default_cog}` was not found. Please try again with one of the following."
        await ctx.send(embed=embed, view=DropdownView(self.bot, ctx, default_cog))


async def setup(bot):
    await bot.add_cog(HelpCommand(bot))