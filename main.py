import os
from keep_alive import keep_alive
import discord
from discord.ext import commands
import datetime
from cogs.utils.context import MyCtx
from cogs.utils.time import human_timedelta
from cogs.utils.constants import GROUP_GUILDS
from aiohttp import ClientSession
import asyncio
from config import TOKEN

os.environ["JISHAKU_NO_UNDERSCORE"] = "True"
os.environ["JISHAKU_NO_DM_TRACEBACK"] = "True"
os.environ["JISHAKU_HIDE"] = "True"

extensions = [
    'jishaku',
    *['cogs.' + i for i in [
        'owner',
        'bot',
        'errorhandler',
        '_help',
        'pg',
    ]]
]

class MyBot(commands.AutoShardedBot):
    def __init__(self, **kwargs):
        pre = kwargs.pop('command_prefix', '!')
        super().__init__(command_prefix=pre,
                         case_insensitive=True,
                         intents=discord.Intents.all(),
                         activity=discord.Activity(
            type=discord.ActivityType.watching, name=f"{pre}help"),
                         **kwargs)
        self.session = None
        self.start_time = datetime.datetime.utcnow()
        self.owner_ids = [499400512559382538, 833689253996527657]

        # tree = discord.app_commands.CommandTree(self)

    async def on_message(self, message):
        await self.wait_until_ready()
        if message.author.bot:
            return
        if message.guild:
            print(
                f"{message.channel.name}|#{message.channel.id} - @{message.author.name}: {message.clean_content}"
            )
        else:
            print(f"{message.author.name}: {message.clean_content}")
        await self.process_commands(message)

    async def on_connect(self):
        self.session = ClientSession(loop=self.loop)
        await self.wait_until_ready()
        print(f'Successfully logged in as {self.user}\nSharded to {len(self.guilds)} guilds')

        self.remove_command('help')

        for ext in extensions:
            try:
                await self.load_extension(ext)
            except commands.ExtensionFailed as e:
                print(e)
                
        print(
            f'Loaded all extensions after {human_timedelta(self.start_time, brief=True, suffix=False)}'
        )

        await self.get_user(self.owner_ids[1]).send(f'Successfully logged in as {self.user}\nSharded to {len(self.guilds)} guilds\nLoaded all extensions after {human_timedelta(self.start_time, brief=True, suffix=False)}')
        # print([m for m in self.guilds[0].members if not m.bot])
        # channel = self.get_channel(862180361089450066)
        # await channel.send("done")
        # await channel.edit(slowmode_delay=0)
        # await channel.send("changed slowmode too")

        print("Sent messages")        

    async def on_ready(self):
        for guild in GROUP_GUILDS:
            await self.tree.sync(guild=guild)
            
        print("Synced Tree")

    async def get_context(self, origin, *, cls=MyCtx):
        """Implementation of custom context"""
        return await super().get_context(origin, cls=MyCtx)

    async def close(self):
        await super().close()
        await self.session.close()

bot = MyBot()

keep_alive()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(bot.start(TOKEN))
