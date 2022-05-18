from discord.ext import commands
import discord


class MyCtx(commands.Context):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

	async def em(self, *, title, description=None, bot=None, **kwargs):
		"""Quick embed sending."""
		kwargs.pop('title', None)
		kwargs.pop('description', None)
		color = kwargs.pop('color', None)
		em = discord.Embed(title=title, description=description, color=color if color else discord.Color.blue())
		if bot is not None:
			em.set_author(name=bot.user.display_name, icon_url=bot.user.display_avatar)
		return await super().send(embed=em, **kwargs)