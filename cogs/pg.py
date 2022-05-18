import discord
from discord.ext import commands, tasks
from discord import app_commands
from .utils.constants import GROUP_GUILDS
from .utils.views import Confirm

import typing
import random
import json
from datetime import datetime

lb_types = {
    'pb': 'Random Seed PB',
    'pbAny': 'Any Seed PB',
    'dataUse': 'Data Used',
    'games': 'Games Played',
    'timeSpent': 'Time Spent Playing',
    'dataReplayAvg': 'Data Replay Average',
    'avg': 'Average Time',
    'stddev': 'Consistency',
    'lbTime50Unsorted_dev': 'Last 100 Games Consistency',
    'lbTime50Unsorted_avg': 'Last 100 Games Average'
}


class PG(commands.Cog, name="Party Games"):
    def __init__(self, bot):
        self.bot = bot
        self.data = {}
        self.last_updated = datetime.now()

        with open("pair.json", "r") as f:
            self.pair = json.load(f)

        with open("users.json", "r") as f:
            self.users = json.load(f)

        self.get_data.start()
        self.backup.start()

    async def cog_unload(self):
        with open("pair.json", "w") as f:
            json.dump(self.pair, f)
        with open("users.json", "w") as f:
            json.dump(self.users, f)

    @tasks.loop(minutes=1)
    async def get_data(self):
        await self.bot.wait_until_ready()
        async with self.bot.session.get("https://mc.semisol.dev/lb.json") as resp:
            if resp.status != 200:
                return False

            self.data = await resp.json()
            self.last_updated = datetime.now()

            return True

    @commands.is_owner()
    @commands.command('force_update')
    async def force_update(self, ctx):
        check = await self.get_data()

        msg = await ctx.send("Updating...")

        skipped = []

        for i, person in enumerate(self.data['pbAny']):
            self.users[person['name']] = {
                'uuid': person['player'],
                'avatar': "https://crafthead.net/avatar/"+person['player'].replace("-", "")
            }
            # await msg.edit(content="Updated " + json['username'] + f" {i}/{len(self.data['pbAny'])}")

        for user, stuff in self.users.items():
            if type(stuff) != dict:
                self.users[user] = {
                    'uuid': stuff,
                    'avatar': "https://crafthead.net/avatar/"+stuff.replace("-", "")
                }

        await msg.edit(content="Updated", delete_after=3.0)

        await self.backup()

        await ctx.send(check)

    @tasks.loop(seconds=60)
    async def backup(self):
        await self.bot.wait_until_ready()
        with open("pair.json", "w") as f:
            json.dump(self.pair, f)
        with open("users.json", "w") as f:
            json.dump(self.users, f)

    @commands.hybrid_command('unpair', aliases=['unlink'])
    @app_commands.guilds(*GROUP_GUILDS)
    async def unpair_user(self, ctx):
        """Unlink your discord account with MC account"""
        if str(ctx.author.id) not in self.pair:
            return await ctx.send("You aren't currently linked with a minecraft user.")

        confirm = Confirm(self.bot, ctx)

        current = self.pair[str(ctx.author.id)]

        msg = await ctx.send(f"Please confirm you want to unlink your account with `{current['user']}`", view=confirm)

        await confirm.wait()

        if confirm.value:
            check = self.pair.pop(str(ctx.author.id), None)
            await msg.edit(content="Confirmed! You are now unlinked" if check else "Something went wrong. Please try again later.", view=None)
        else:
            await msg.edit(content="Cancelled!", view=None)

    @commands.hybrid_command('pair', aliases=['link'])
    @app_commands.guilds(*GROUP_GUILDS)
    async def pair_user(self, ctx, mc_user=None):
        """Link your discord account with MC account
        No verification needed."""
        if mc_user is None:
            return await ctx.send(f"Please send a valid minecraft user as an argument\n`{ctx.clean_prefix}pair <mc_user>`")
        if str(ctx.author.id) in self.pair:
            return await ctx.send(f"You are already paired with minecraft user `{self.pair[str(ctx.author.id)]['user']}`")

        if mc_user in [a['user'] for a in self.pair.values()]:
            return await ctx.send(f"Someone is already paired with the minecraft user `{mc_user}`")

        async with self.bot.session.get("https://playerdb.co/api/player/minecraft/" + mc_user) as resp:
            if resp.status == 200:
                json = await resp.json()

                if json['success']:
                    json = json['data']['player']
                    confirm = Confirm(self.bot, ctx)
                    em = discord.Embed(
                        description=f"Please confirm you want to pair your account with {json['username']}'s account.", color=discord.Color.green())
                    em.set_thumbnail(url=json['avatar'])
                    msg = await ctx.send(embed=em, view=confirm)

                    await confirm.wait()

                    if confirm.value:
                        await msg.edit(embed=discord.Embed(title="Paired!", color=discord.Color.green()), view=None)

                        self.pair[str(ctx.author.id)] = {
                            'id': json['id'], 'user': json['username'], 'avatar': json['avatar']}

                    else:
                        await msg.edit(embed=discord.Embed(title="Cancelled!", color=discord.Color.red()), view=None)
                else:
                    return await ctx.send(f"Couldn't find minecraft user {mc_user}")
            else:
                return await ctx.send(f"Couldn't find minecraft user {mc_user}")

    @commands.hybrid_command('stats')
    @app_commands.guilds(*GROUP_GUILDS)
    async def stats(self, ctx, mc_user: typing.Optional[str]):
        """Provides the stats for a user"""
        embed = discord.Embed(title=f"{mc_user}'s Stats")
        if mc_user is None:
            if str(ctx.author.id) in self.pair:
                mc_user = self.pair[str(ctx.author.id)]['id'].replace("-", "")
                embed = discord.Embed(
                    title=f"{self.pair[str(ctx.author.id)]['user']}'s Stats")
            else:
                return await ctx.send("Please provide a minecraft user.")
        else:
            if mc_user in self.users:
                mc_user = self.users[mc_user]['uuid'].replace("-", "")
            else:
                async with self.bot.session.get(f"https://playerdb.co/api/player/minecraft/{mc_user}") as resp:
                    if resp.status == 200:
                        json = await resp.json()
                        if json['success']:
                            mc_user = json['data']['player']['id'].replace(
                                "-", "")
                        else:
                            return await ctx.send("User not found.")
                    else:
                        return await ctx.send("User not found.")

        for i, person in enumerate(self.data['pb']):
            if person['player'].replace("-", "") == mc_user:
                embed.add_field(name='Rank (Random Seed)', value='#' +
                                str(i+1) + ' - ' + str(round(person['pb'], 3)) + 's')
                break
        else:
            embed.add_field(name='Rank (Random Seed)', value='N/A')

        for i, person in enumerate(self.data['pbAny']):
            if person['player'].replace("-", "") == mc_user:
                embed.add_field(name='Rank (Any)', value='#' +
                                str(i+1) + ' - ' + str(round(person['pb'], 3)) + 's')
                break
        else:
            embed.add_field(name='Rank (Any)', value='N/A')

        for i, person in enumerate(self.data['games']):
            if person['player'].replace("-", "") == mc_user:
                embed.add_field(name='# of Games', value='#' + str(i+1) +
                                ' - ' + str(round(person['games'], 3)) + ' games played')
                break
        else:
            embed.add_field(name='# of Games', value='N/A')

        for i, person in enumerate(self.data['timeSpent']):
            if person['player'].replace("-", "") == mc_user:
                embed.add_field(name='Time Spent', value='#' + str(i+1) +
                                ' - ' + str(round(person['time_spent']/60, 3)) + ' minutes')
                break
        else:
            embed.add_field(name='Time Spent', value='N/A')

        for i, person in enumerate(self.data['avg']):
            if person['player'].replace("-", "") == mc_user:
                embed.add_field(name='Average Time', value='#' + str(i+1) +
                                ' - ' + str(round(person['avg_time'], 3)) + 's')
                break
        else:
            embed.add_field(name='Average Time', value='N/A')

        for i, person in enumerate(self.data['stddev']):
            if person['player'].replace("-", "") == mc_user:
                embed.add_field(name='Consistency', value='#' +
                                str(i+1) + ' - ' + str(round(person['dev'], 3)) + 's')
                break
        else:
            embed.add_field(name='Consistency', value='N/A')

        for person in self.data['lbTime50Unsorted']:
            if person['player'].replace("-", "") == mc_user:
                avg_sorted = sorted(
                    self.data['lbTime50Unsorted'], key=lambda a: a['avg'])
                dev_sorted = sorted(
                    self.data['lbTime50Unsorted'], key=lambda a: a['dev'])

                embed.add_field(name='Last 100 Games Average Time',
                                value=f'#{avg_sorted.index(person)+1} - {round(person["avg"], 3)}s')
                embed.add_field(name='Last 100 Games Consistency',
                                value=f'#{dev_sorted.index(person)+1} - {round(person["dev"], 3)}s')
                break
        else:
            embed.add_field(name='Last 100 Games Average Time', value='N/A')
            embed.add_field(name='Last 100 Games Consistency', value='N/A')

        for i, person in enumerate(self.data['dataUse']):
            if person['player'].replace("-", "") == mc_user:
                embed.add_field(name='Data Used', value='#' + str(i+1) +
                                ' - ' + str(round(person['data_used']/1000, 3)) + ' kb')
                break
        else:
            embed.add_field(name='Data Used', value='N/A')

        for i, person in enumerate(self.data['dataReplayAvg']):
            if person['player'].replace("-", "") == mc_user:
                embed.add_field(name='Average Replay Size', value='#' + str(i+1) +
                                ' - ' + str(round(person['data_replay_avg'], 3)) + ' bytes')
                break
        else:
            embed.add_field(name='Average Replay Size', value='N/A')

        embed.color = discord.Color.blue()
        embed.description = "Jigsaw Rush statistics on mc.semisol.dev"
        embed.set_footer(text="Last updated at")
        embed.timestamp = self.last_updated

        for m, stuff in self.users.items():
            if type(stuff) == str:
                self.users[m] = {
                    'uuid': stuff.replace("-", ""),
                    'avatar': "https://crafthead.net/avatar/"+stuff.replace("-", "")
                }
                stuff = self.users[m]
            if stuff['uuid'].replace("-", "") == mc_user:
                user = m, stuff
                break
        else:
            print("huh")
        
        embed.title = f"{user[0]}'s Stats"
        embed.set_thumbnail(url=user[1]['avatar'])

        await ctx.send(embed=embed)

    async def lb_autocomplete(self, ctx, current):
        return [
            app_commands.Choice(name=lb_types[t], value=t)
            for t in lb_types if current.lower() in t.lower()
        ]

    @commands.hybrid_command('leaderboard', aliases=['lb'])
    @app_commands.guilds(*GROUP_GUILDS)
    @app_commands.autocomplete(lb_type=lb_autocomplete)
    async def leaderboards(self, ctx, *, lb_type: typing.Optional[str]):
        """Shows the leaderboards."""
        if lb_type is None or lb_type not in [*lb_types.keys(), *lb_types.values()]:
            return await ctx.send("Please pick a lb type from the following:\n`" + '`, `'.join(lb_types.values()) + "`")

        if lb_type in lb_types.values():
            lb_type = {v: k for k, v in lb_types.items()}[lb_type]

        embed = discord.Embed(title=lb_types[lb_type] + " Leaderboard", description="", color=discord.Color.blue(), timestamp=self.last_updated)

        if "lbTime50Unsorted" in lb_type:
            lb_type = lb_type.replace('lbTime50Unsorted_', '')
            avg_sorted = sorted(
                self.data['lbTime50Unsorted'], key=lambda a: a['avg'])[:10]
            dev_sorted = sorted(
                self.data['lbTime50Unsorted'], key=lambda a: a['dev'])[:10]
            for i, person in enumerate(avg_sorted if lb_type == 'avg' else dev_sorted):
                if person['name'] is None:
                    for m, stuff in self.users.items():
                        if stuff == person['player'] or type(stuff) == str:
                            person['name'] = m
                        else:
                            if stuff['uuid'].replace("-", "") == person['player']:
                                person['name'] = m
                                break
                    else:
                        print("huh")

                embed.description += f"{i+1}. {person['name']} - {round(person[lb_type], 3)}s\n"

        else:
            keys = {
                'pb': 'pb',
                'pbAny': 'pb',
                'games': 'games',
                'dataUse': 'data_used',
                'timeSpent': 'time_spent',
                'dataReplayAvg': 'data_replay_avg',
                'avg': 'avg_time',
                'stddev': 'dev'
            }
            suffix = {
                'pb': 's',
                'pbAny': 's',
                'games': ' games played',
                'dataUse': ' kb',
                'timeSpent': ' minutes',
                'dataReplayAvg': ' bytes',
                'avg': 's',
                'stddev': 's'
            }
            divide = {
                'pb': 1,
                'pbAny': 1,
                'games': 1,
                'dataUse': 1000,
                'timeSpent': 60,
                'dataReplayAvg': 1,
                'avg': 1,
                'stddev': 1
            }
            for i, person in enumerate(self.data[lb_type][:10]):
                if person['name'] is None:
                    for m, stuff in self.users.items():
                        if stuff == person['player'] or type(stuff) == str:
                            person['name'] = m
                        else:
                            if stuff['uuid'].replace("-", "") == person['player']:
                                person['name'] = m
                                break
                    else:
                        print("huh")
                        
                embed.description += f"{i+1}. {person['name']} - {round(person[keys[lb_type]]/divide[lb_type], 3)}{suffix[lb_type]}\n"

        embed.set_footer(text="Last updated at")
        await ctx.send(embed=embed)

    @commands.hybrid_command('pbgame')
    @app_commands.guilds(*GROUP_GUILDS)
    async def pbgame(self, ctx, mc_user: typing.Optional[str]):
        """Gets your personal best game replay code"""
        embed = discord.Embed(title=f"{mc_user}'s Personal Best")
        if mc_user is None:
            if str(ctx.author.id) in self.pair:
                mc_user = self.pair[str(ctx.author.id)]['id'].replace("-", "")
                embed = discord.Embed(
                    title=f"{self.pair[str(ctx.author.id)]['user']}'s Personal Best")
            else:
                return await ctx.send("Please provide a minecraft user.")
        else:
            if mc_user in self.users:
                mc_user = self.users[mc_user]['uuid'].replace("-", "")
            else:
                async with self.bot.session.get(f"https://playerdb.co/api/player/minecraft/{mc_user}") as resp:
                    if resp.status == 200:
                        json = await resp.json()
                        if json['success']:
                            mc_user = json['data']['player']['id'].replace(
                                "-", "")
                        else:
                            return await ctx.send("User not found.")
                    else:
                        return await ctx.send("User not found.")

        for person in self.data['pb']:
            if person['player'].replace("-", "") == mc_user.replace("-", ""):
                embed.add_field(name="Personal Best (Random Seed)", value=f"{round(person['pb'], 3)}s\n`/analyze {person['pbgame']}`", inline=False)
                break
        for person in self.data['pbAny']:
            if person['player'].replace("-", "") == mc_user.replace("-", ""):
                embed.add_field(name="Personal Best (Any Seed)", value=f"{round(person['pb'], 3)}s\n`/analyze {person['pbgame']}`", inline=False)
                break

        embed.color = discord.Color.blue()
        embed.description = "Jigsaw Rush personal best on mc.semisol.dev"
        embed.set_footer(text="Last updated at")
        embed.timestamp = self.last_updated

        for m, stuff in self.users.items():
            if type(stuff) == str:
                self.users[m] = {
                    'uuid': stuff.replace("-", ""),
                    'avatar': "https://crafthead.net/avatar/"+stuff.replace("-", "")
                }
                stuff = self.users[m]
            if stuff['uuid'].replace("-", "") == mc_user:
                user = m, stuff
                break
        else:
            print("huh")
        
        embed.title = f"{user[0]}'s Personal Best"
        embed.set_thumbnail(url=user[1]['avatar'])

        await ctx.send(embed=embed)

    @commands.hybrid_command('seed')
    @app_commands.guilds(*GROUP_GUILDS)
    async def seed(self, ctx, seed: int = None):
        """Shows the board of a certain seed"""
        if seed is None or not isinstance(seed, int):
            return await ctx.send(f"Please send a valid seed. Must be an integer\n`{ctx.clean_prefix}seed <seed>`")

        random.seed(seed)

        allblocks = ["dirt", "stone", "cobblestone", "log", "planks", "bricks", "gold", "nether", "endstone"]

        blocks = []
        for i in [0]*9:
            blocks.append(allblocks.pop(random.randint(0,len(allblocks))))

        await ctx.send(f'{", ".join(blocks[:3])}\n{", ".join(blocks[3:6])}\n{", ".join(blocks[6:])}\n')


async def setup(bot):
    await bot.add_cog(PG(bot))