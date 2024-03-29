import os
import discord
from discord.ext import commands
import datetime
from cogs.utils.context import MyCtx
from cogs.utils.time import human_timedelta
from cogs.utils.constants import GROUP_GUILDS
from aiohttp import ClientSession
import asyncio

try:
    from config import TOKEN
except Exception:
    TOKEN = os.environ["TOKEN"]

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
        'jigsaw',
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
        self.owner_id = 499400512559382538

    async def on_message(self, message):
        await self.wait_until_ready()
        if message.author.bot:
            return
        
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
        
        for guild in GROUP_GUILDS:
            await self.tree.sync(guild=guild)
            
        print("Synced Tree")

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

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(bot.start(TOKEN))
