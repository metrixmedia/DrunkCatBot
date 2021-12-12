import inspect
import io
import textwrap
import traceback
from contextlib import redirect_stdout
import datetime
from speedtest import Speedtest
from psutil import virtual_memory, cpu_percent, cpu_freq

import aiohttp
import discord
from discord.ext import commands
from io import BytesIO
from utils import default, permissions
client = discord.Client

class Debug(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.config = default.config()

	@commands.command(name='speedtest')
	async def speed_test(self, ctx):		
		"""Speedtest"""
		async with ctx.typing():
			if await self.bot.is_owner(ctx.author):
				s = Speedtest()
				s.get_best_server()
				s.download()
				s.upload()
				s = s.results.dict()
				
				await ctx.send(f"Ping: `{s['ping']}ms`\nDownload: `{round(s['download']/10**6, 3)} Mbits/s`\nUpload: `{round(s['upload']/10**6, 3)} Mbits/s`\nServeur ISP Internet: `{s['server']['sponsor']}, {s['server']['name']}, {s['server']['country']}`\nFournisseur VPS Discord: `{s['client']['isp']} {s['client']['country']} {s['client']['isprating']}`")
			else:
				await ctx.send("Only bot admin can use those debug functions :man_technologist_tone1:")

	@commands.command(name='botinfo' , aliases=['botstats', 'status'])
	async def stats(self, ctx):
		"""Bot stats."""
		# Uptime
		uptime = (datetime.datetime.now() - self.bot.uptime)
		hours, rem = divmod(int(uptime.total_seconds()), 3600)
		minutes, seconds = divmod(rem, 60)
		days, hours = divmod(hours, 24)
		if days:
			time = '%s days, %s hours, %s minutes, and %s seconds' % (days, hours, minutes, seconds)
		else:
			time = '%s hours, %s minutes, and %s seconds' % (hours, minutes, seconds)
		
		# Embed
		em = discord.Embed(color=0x4FFCFA)
		em.set_author(name=f'{self.bot.user} bot status:', icon_url=self.bot.user.avatar_url, url='https://discord.com/oauth2/authorize?client_id=735564887056580640&scope=bot&permissions=8')
		em.add_field(name=':clock3: Uptime', value=f'`{time}`', inline=False)
		em.add_field(name=':outbox_tray: Msgs sent', value=f'`{self.bot.messages_out}`')
		em.add_field(name=':inbox_tray: Msgs received', value=f'`{self.bot.messages_in}`')
		em.add_field(name=':crossed_swords: Servers', value=f'`{len(self.bot.guilds)}`')
		em.add_field(name=':satellite_orbital: Server Region', value=f'`{self.bot.region}`')

		mem = virtual_memory()
		mem_usage = f"{mem.percent} % {mem.used / 1024 ** 2:.2f} MiB"
		em.add_field(name=u':floppy_disk: Memory usage', value=f'`{mem_usage}`')
		cpu_usage = f"{cpu_percent(1)} % {cpu_freq().current / 1000:.2f} Ghz"
		em.add_field(name=':desktop: CPU usage', value=f'`{cpu_usage}`')
		
		try:
			await ctx.send(embed=em)
		except Exception:
			await ctx.send("I don't have permission to send embeds here :disappointed_relieved:")

	@commands.command(name='reload')
	async def reload_module(self, ctx, arg=None):
		"""Reload module"""
		if not await self.bot.is_owner(ctx.author):
			return await ctx.send("Only bot admin can use those debug functions :man_technologist_tone1:")
		
		modules = ['misc', 'games', 'debug', 'media', 'music']
		if not arg:
			return await ctx.send(embed=discord.Embed(title='Vous devez préciser les modules :', description='\n'.join(modules)))
		if arg.lower() == 'all':
			for module in modules:
				msg = await ctx.send(f":arrows_counterclockwise: Chargement en cours de `{module}`...")
				self.bot.unload_extension('cogs.' + module)
				self.bot.load_extension('cogs.' + module)
				await msg.edit(content=f":white_check_mark: Chargé `{module}`")
		elif arg.lower() in modules:
			msg = await ctx.send(f":arrows_counterclockwise: Chargement en cours de `{arg.lower()}`...")
			self.bot.unload_extension('cogs.' + arg.lower())
			self.bot.load_extension('cogs.' + arg.lower())
			await msg.edit(content=f":white_check_mark: Chargé `{arg.lower()}`")

	@commands.command()
	@commands.guild_only()
	async def avatar(self, ctx, *, user: discord.Member = None):
		""" Get the avatar of you or someone else """
		user = user or ctx.author
		await ctx.send(f"Avatar to **{user.name}**\n{user.avatar.with_size(1024)}")

	@commands.command()
	@commands.guild_only()
	async def roles(self, ctx):
		""" Get all roles in current server """
		allroles = ""

		for num, role in enumerate(sorted(ctx.guild.roles, reverse=True), start=1):
			allroles += f"[{str(num).zfill(2)}] {role.id}\t{role.name}\t[ Users: {len(role.members)} ]\r\n"

		data = BytesIO(allroles.encode("utf-8"))
		await ctx.send(content=f"Roles in **{ctx.guild.name}**", file=discord.File(data, filename=f"{default.timetext('Roles')}"))

	@commands.command()
	@commands.guild_only()
	async def joinedat(self, ctx, *, user: discord.Member = None):
		""" Check when a user joined the current server """
		user = user or ctx.author

		embed = discord.Embed(colour=user.top_role.colour.value)
		embed.set_thumbnail(url=user.avatar)
		embed.description = f"**{user}** joined **{ctx.guild.name}**\n{default.date(user.joined_at, ago=True)}"
		await ctx.send(embed=embed)

	@commands.command()
	@commands.guild_only()
	async def mods(self, ctx):
		""" Check which mods are online on current guild """
		message = ""
		all_status = {
            "online": {"users": [], "emoji": "🟢"},
            "idle": {"users": [], "emoji": "🟡"},
            "dnd": {"users": [], "emoji": "🔴"},
            "offline": {"users": [], "emoji": "⚫"}
        }

		for user in ctx.guild.members:
			user_perm = ctx.channel.permissions_for(user)
			if user_perm.kick_members or user_perm.ban_members:
				if not user.bot:
					all_status[str(user.status)]["users"].append(f"**{user}**")

		for g in all_status:
			if all_status[g]["users"]:
				message += f"{all_status[g]['emoji']} {', '.join(all_status[g]['users'])}\n"

		await ctx.send(f"Mods in **{ctx.guild.name}**\n{message}")

	@commands.command()
	async def amiadmin(self, ctx):
		""" Are you an admin? """
		if ctx.author.id in self.config["owners"]:
			return await ctx.send(f"Yes **{ctx.author.name}** you are an admin! ✅")

        # Please do not remove this part.
        # I would love to be credited as the original creator of the source code.
        #   -- AlexFlipnote
		if ctx.author.id == 86477779717066752:
			return await ctx.send(f"Well kinda **{ctx.author.name}**.. you still own the source code")

		await ctx.send(f"no, heck off {ctx.author.name}")

	@commands.command()
	@commands.check(permissions.is_owner)
	async def dm(self, ctx, user: discord.User, *, message: str):
		""" DM the user of your choice """
		try:
			await user.send(message)
			await ctx.send(f"✉️ Sent a DM to **{user}**")
		except discord.Forbidden:
			await ctx.send("This user might be having DMs blocked or it's a bot account...")

	@commands.group()
	@commands.check(permissions.is_owner)
	async def change(self, ctx):
		if ctx.invoked_subcommand is None:
			await ctx.send_help(str(ctx.command))

	@change.command(name="playing")
	@commands.check(permissions.is_owner)
	async def change_playing(self, ctx, *, playing: str):
		""" Change playing status. """
		status = self.config["status_type"].lower()
		status_type = {"idle": discord.Status.idle, "dnd": discord.Status.dnd}

		activity = self.config["activity_type"].lower()
		activity_type = {"listening": 2, "watching": 3, "competing": 5}

		try:
			await self.bot.change_presence(
                activity=discord.Game(
                    type=activity_type.get(activity, 0), name=playing
                ),
                status=status_type.get(status, discord.Status.online)
            )
			self.change_config_value("playing", playing)
			await ctx.send(f"Successfully changed playing status to **{playing}**")
		except discord.InvalidArgument as err:
			await ctx.send(err)
		except Exception as e:
			await ctx.send(e)
	
	@commands.command(name='serversin')
	async def servers(self, ctx):
		activeservers = client.guilds
		for guild in activeservers:
			await ctx.send(guild.name)
			print(guild.name)


def setup(bot):
	bot.add_cog(Debug(bot))
