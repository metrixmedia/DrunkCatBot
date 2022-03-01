import os
import io
import datetime
import json
from aiohttp import ClientSession
import ksoftapi
import keep_alive
import discord
from discord.ext import commands
from os import environ, listdir

from utils import default
from utils.data import Bot, HelpFormat

keep_alive.keep_alive()
config = default.config()

bot = Bot(
    command_prefix=config["prefix"], prefix=config["prefix"],
    owner_ids=config["owners"], command_attrs=dict(hidden=True), help_command=HelpFormat(),
    allowed_mentions=discord.AllowedMentions(roles=False, users=True, everyone=False),
    intents=discord.Intents(  # kwargs found at https://discordpy.readthedocs.io/en/latest/api.html?highlight=intents#discord.Intents
        guilds=True, members=True, messages=True, reactions=True, presences=True
    ),
	description='DrunkCat, a Discord bot created by @hugofnm#8066 with ❤️ in Nice, France. Status : status.hugofnm.fr'
)

bot.remove_command('help')

bot.uptime = datetime.datetime.now()
bot.messages_in = bot.messages_out = 0
bot.region = 'Nice, FR'

@bot.event
async def on_ready():
	print('Connecté comme {0} ({0.id})'.format(bot.user))
	bot.kclient = ksoftapi.Client(os.environ['KSoft_Token'])
	bot.client = ClientSession()

	# Load Modules
	modules = ['music', 'alexfun', 'moderator', 'debug', 'games', 'media', 'misc']
	try:
		for module in modules:
			bot.load_extension('cogs.' + module)
			print('Loaded: ' + module)
	except Exception as e:
		print(f'Error loading {module}: {e}')

	print('The bot is now ACTIVE')

@bot.event
async def on_message(message):
	# Sent message
	if message.author.id == bot.user.id:
		if hasattr(bot, 'messages_out'):
			bot.messages_out += 1
	# Received message (Count only commands messages)
	elif message.content.startswith('&'):
		if hasattr(bot, 'messages_in'):
			bot.messages_in += 1

	await bot.process_commands(message)

@bot.command(name='help', aliases=['h'])
async def help(ctx, arg: str=''):
	"""Montre l'écran d'aide"""
	embed = discord.Embed(title="DrunkCat, a Discord bot created by @hugofnm#8066 with ❤️ in Nice, France. Status : status.hugofnm.fr", colour=discord.Colour(0x7f20a0))

	avatar_url = str(bot.user.avatar_url)
	embed.set_thumbnail(url=avatar_url)
	embed.set_author(name="DrunkCat Bot Help", url="https://discord.com/oauth2/authorize?client_id=948326406369210368&scope=bot&permissions=8", icon_url=avatar_url)
	embed.set_footer(text="Drunk Bot by @hugofnm#8066")

	if arg.strip().lower() == '-a':
		# Full version
		embed.description = 'Use `&` to talk to me !'
		with open('help.json', 'r') as help_file:
			data = json.load(help_file)
		data = data['full']
		for key in data:
			value = '\n'.join(x for x in data[key])
			embed.add_field(name=key, value=f"```{value}```", inline=False)
	else:
		# Short version
		embed.description = 'Use `&` to talk to me , and type &help -a for more informations about the commands'
		with open('help.json', 'r') as help_file:
			data = json.load(help_file)
		data = data['short']
		for key in data:
			embed.add_field(name=key, value=data[key])
	try:
		await ctx.send(embed=embed)
	except Exception:
		await ctx.send("I cannot send embeds here !\'('")


# All good ready to start!
print('Starting Bot...')
bot.run(os.environ['TOKEN'])