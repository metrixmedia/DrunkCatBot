import os
import time
import random
import requests
import discord
from discord.ext import commands
import ksoftapi

class Misc(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.kclient = bot.kclient
		self.client = bot.client

	@commands.command(name='list')
	async def listusers(self, ctx):
		"""Displays the list of connected users"""
		members = ctx.author.voice.channel.members
		memnames = []
		for member in members:
			memnames.append(member.name)
		await ctx.send(f"Members in {ctx.author.voice.channel.name}:\n```\n" + "\n".join(memnames) +"\n```")
	
	@commands.command(name='teams', aliases=['team'])
	async def teams(self, ctx, num=2):
		"""Makes random teams with specified number(def. 2)"""
		members = ctx.author.voice.channel.members
		memnames = []
		for member in members:
			memnames.append(member.name)
		
		remaining = memnames
		if len(memnames)>=num:
			for i in range(num):
				team = random.sample(remaining,len(memnames)//num)
				remaining = [x for x in remaining if x not in team]
				await ctx.send(f"Team {chr(65+i)}\n" + "```CSS\n" + '\n'.join(team) + "\n```")
		if len(remaining)> 0:
			await ctx.send("Remaining\n```diff\n- " + '\n- '.join(remaining) + "\n```")


	@commands.command(name='clear', aliases=['cls'])
	async def clear(self, ctx, limit=20):
		"""Delete the messages sent in current text-channel"""
		if 1>limit>100:
			limit = 20
		messages = []
		try:
			await ctx.message.channel.purge(limit=limit)
		except discord.Forbidden:
			await ctx.send("I don't have permission to `Manage Messages`:disappointed_relieved:")

	@commands.command(name='ping', aliases=['latency'])
	async def ping(self, ctx):
		""" Pong! """
		message = await ctx.send(":ping_pong: Pong!")
		ping = (message.created_at.timestamp() - ctx.message.created_at.timestamp()) * 1000
		await message.edit(content=f":ping_pong: Pong!\nTook `{int(ping)}ms`\nLatency: `{int(self.bot.latency*1000)}ms`")

	@commands.command(name='weather')
	async def weather(self, ctx, *, city: str):
		city_name = city
		api_key = os.environ['WeatherAPI']
		base_url = "http://api.openweathermap.org/data/2.5/weather?"
		complete_url = base_url + "appid=" + api_key + "&q=" + city_name
		response = requests.get(complete_url)
		x = response.json()
		channel = ctx.message.channel
		if x["cod"] != "404":
			async with channel.typing():
				y = x["main"]
				current_temperature = y["temp"]
				current_temperature_celsius = str(round(current_temperature - 273.15))
				current_temperature_fahrenheit = str(round((current_temperature - 273.15) * (9/5) + 32))
				current_pressure = y["pressure"]
				current_humidity = y["humidity"]
				z = x["weather"]
				weather_description = z[0]["description"]
				embed = discord.Embed(title=f"Weather in  {city_name}",
          color=ctx.guild.me.top_role.color,
          timestamp=ctx.message.created_at,)
				embed.add_field(name="Weather", value=f"**{weather_description}**", inline=False)
				embed.add_field(name="Temperature(C)", value=f"**{current_temperature_celsius}°C**", inline=False)
				embed.add_field(name="Temperature(F)", value=f"**{current_temperature_fahrenheit}°F**", inline=False)
				embed.add_field(name="Humidity(%)", value=f"**{current_humidity}%**", inline=False)
				embed.add_field(name="Atmospheric Pressure(hPa)", value=f"**{current_pressure}hPa**", inline=False)
				embed.set_thumbnail(url="https://i.ibb.co/CMrsxdX/weather.png")
				embed.set_footer(text=f"Requested by {ctx.author.name}")
			await channel.send(embed=embed)
		else:
			await channel.send("City not found.")

	@commands.command(name='convert', aliases=['currency'])
	async def currency(self, ctx, value: str="", _from: str="", to: str=""):
		"""Currency conversion"""
		if value=="" or _from=="" or to=="":
			return await ctx.send("Please enter values in proper format\n`~convert [value] [from] [to]`\neg: `~convert 16 usd inr`")

		try:
			async with ctx.typing():
				c = await self.kclient.kumo.currency_conversion(_from, to, value)
		except (ksoftapi.NoResults, ksoftapi.errors.APIError):
			await ctx.send('Conversion Failed :x:')
		else:
			await ctx.send(f":currency_exchange: Conversion:\n`{value} {_from.upper()}` = `{c.pretty}`")
	
	@commands.command(name='owner', aliases=['support', 'contact'])
	async def support(self, ctx, *, msg: str = ""):
		"""Contact bot owner"""
		if msg == "":
			return await ctx.send("Please enter a message to send towards Bot Owner", delete_after=5.0)

		embed = discord.Embed(colour=discord.Colour(0x5dadec), description=msg)
		embed.set_author(name=ctx.author, icon_url=ctx.author.avatar_url)
		embed.set_footer(text=f"{ctx.guild} : {ctx.guild.id}", icon_url=ctx.guild.icon_url)

		info = await self.bot.application_info()
		await info.owner.send(embed=embed)
		await ctx.send("Bot owner notified!")

	@commands.command(name='tts')
	async def _tts(self, ctx, *, text=''):
		"""Send tts message"""
		if not text:
			return await ctx.send('Specify message to send')
		await ctx.send(content=text, tts=True)

	@commands.command(name = 'userinfo', aliases=['user', 'uinfo', 'ui'])
	async def userinfo(self, ctx, *, name=""):
		"""Get user info. Ex: ~user @user"""
		if name:
			try:
				user = ctx.message.mentions[0]
			except IndexError:
				user = ctx.guild.get_member_named(name)
			try:
				if not user:
					user = ctx.guild.get_member(int(name))
				if not user:
					user = self.bot.get_user(int(name))
			except ValueError:
				pass
			if not user:
				await ctx.send('User not found :man_frowning_tone1:')
				return
		else:
			user = ctx.message.author

		if isinstance(user, discord.Member):
			role = user.top_role.name
			if role == "@everyone":
				role = "N/A"
			voice_state = None if not user.voice else user.voice.channel

		em = discord.Embed(colour=0x00CC99)
		em.add_field(name='User ID', value=f'`{user.id}`')
		if isinstance(user, discord.Member):
			if isinstance(user.activity, discord.Spotify):
				activity = "Listening " + user.activity.title
			elif user.activity is not None: 
				activity = str(user.activity.type)[13:].title() + ' ' + user.activity.name
			else:
				activity = None

			em.add_field(name='Nick', value=f'`{user.nick}`')
			em.add_field(name='Status', value=f'`{user.status}`')
			em.add_field(name='In Voice', value=f'`{voice_state}`')
			em.add_field(name='Activity', value=f'`{activity}`')
			em.add_field(name='Highest Role', value=f'`{role}`')
		em.add_field(name='Account Created', value=f"`{user.created_at.__format__('%A, %d %B %Y @ %H:%M:%S')}`", inline=False)
		if isinstance(user, discord.Member):
			em.add_field(name='Join Date', value=f"`{user.joined_at.__format__('%A, %d %B %Y @ %H:%M:%S')}`", inline=False)
		em.set_thumbnail(url=user.avatar_url)
		em.set_author(name=user, icon_url=user.avatar_url)
		
		try:
			await ctx.send(embed=em)
		except Exception:
			await ctx.send("I don't have permission to send embeds here :disappointed_relieved:")

	@commands.command(name='sinfo', aliases=['server'])
	async def serverinfo(self, ctx, *, name:str = ""):
		"""Get server info"""
		if name:
			server = None
			try:
				server = self.bot.get_guild(int(name))
				if not server:
					return await ctx.send('Server not found :satellite_orbital:')
			except:
				for i in self.bot.guilds:
					if i.name.lower() == name.lower():
						server = i
						break
				if not server:
					return await ctx.send("Server not found :satellite_orbital: or maybe I'm not in it")
		else:
			server = ctx.guild
		# Count online members
		online = 0
		for i in server.members:
			if str(i.status) == 'online' or str(i.status) == 'idle' or str(i.status) == 'dnd':
				online += 1
		# Count channels
		tchannel_count = len([x for x in server.channels if type(x) == discord.channel.TextChannel])
		vchannel_count = len([x for x in server.channels if type(x) == discord.channel.VoiceChannel])
		# Count roles
		role_count = len(server.roles)

		# Create embed
		em = discord.Embed(color=0x00CC99)
		em.set_author(name='Server Info:', icon_url=server.owner.avatar_url)
		em.add_field(name='Name', value=f'`{server.name}`')
		em.add_field(name='Owner', value=f'`{server.owner}`', inline=False)
		em.add_field(name='Members', value=f'`{server.member_count}`')
		em.add_field(name='Online', value=f'`{online}`')
		em.add_field(name='Text Channels', value=f'`{tchannel_count}`')
		em.add_field(name='Voice Channels', value=f'`{vchannel_count}`')
		em.add_field(name='Verification Level', value=f'`{str(server.verification_level).title()}`')
		em.add_field(name='Number of roles', value=f'`{role_count}`')
		em.add_field(name='Highest role', value=f'`{server.roles[-1]}`')
		em.add_field(name='Created At', value=f"`{server.created_at.__format__('%A, %d. %B %Y @ %H:%M:%S')}`", inline=False)
		em.set_thumbnail(url=server.icon_url)
		em.set_footer(text='Server ID: %s' % server.id)

		try:
			await ctx.send(embed=em)
		except Exception:
			await ctx.send("I don't have permission to send embeds here :disappointed_relieved:")

	@commands.command(name='invite')
	async def invite(self, ctx):
		"""My invite link"""
		await ctx.send("Pour inviter **DrunkCat** dans votre serveur, utilisez le lien suivant : https://link.hugofnm.fr/drunkcat")

	@commands.command(name='analyze', aliases=['predict'])
	async def predict(self, ctx, *, text=None):
		"""Analyze message for inappropriate content"""
		if not text:
			return await ctx.send('Please specify the message to analyze :pager:')
		
		url = os.environ['Predict_API']
		text = text.strip('|')
		payload = {
			'comment': {'text': text},
			'languages': ['en', 'fr'],
			'requestedAttributes': {'TOXICITY': {}, 'IDENTITY_ATTACK': {}, 'INSULT': {}, 'PROFANITY': {}, 'THREAT': {}, 
								'SEXUALLY_EXPLICIT': {}, 'FLIRTATION': {}, 'SPAM': {}, 'OBSCENE': {}, 'INCOHERENT': {}, 'INFLAMMATORY': {}}
			}
		async with self.client.post(url, json=payload) as r:
			if r.status != 200:
				print(r)
				return print('Error')
			data = await r.json()
		data = data['attributeScores']
		result = []
		for i in data:
			result.append([i, data[i]['summaryScore']['value']])
		result.sort(key=lambda x: x[1], reverse=True)
		data = []
		for i in result:
			if i[1] > 0.5:
				data.append(f"+ {i[0].title()} {' '*(20-len(i[0]))}{i[1]:.2%}")
			else:
				data.append(f"- {i[0].title()} {' '*(20-len(i[0]))}{i[1]:.2%}")
		data = '\n'.join(data)
		
		em = discord.Embed(color=discord.Color(0xCCFF00), description=f"||{text}||")
		em.set_author(name=ctx.author.name, icon_url=str(ctx.author.avatar_url_as(size=64)))
		em.add_field(name="Prediction:", value=f"```diff\n{data}\n```")

		await ctx.send(embed=em)

	@listusers.before_invoke
	@teams.before_invoke
	async def ensure_author_voice(self, ctx):
		if not ctx.author.voice:
			await ctx.send("You are not connected to a voice channel :mute:")

def setup(bot):
    bot.add_cog(Misc(bot))