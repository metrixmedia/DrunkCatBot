from asyncio.tasks import wait_for
from discord import Embed, FFmpegPCMAudio, channel
from discord.ext import commands
from discord.utils import get
from youtube_dl import YoutubeDL
from asyncio import run_coroutine_threadsafe
import requests
import ksoftapi
import discord
import os
import asyncio
import time
import ffmpeg

class Music(commands.Cog, name='Music'):
    """
    Can be used by anyone and allows you to listen to music or videos.
    """
    YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist':'True'}
    FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

    def __init__(self, bot):
        self.bot = bot
        self.song_queue = {}
        self.message = {}
        self.client = bot.client

    @staticmethod
    def parse_duration(duration):
        result = []
        m, s = divmod(duration, 60)
        h, m = divmod(m, 60)
        return f'{h:d}:{m:02d}:{s:02d}'

    @staticmethod
    def search(author, arg):
        with YoutubeDL(Music.YDL_OPTIONS) as ydl:
            try: requests.get(arg)
            except: info = ydl.extract_info(f"ytsearch:{arg}", download=False)['entries'][0]
            else: info = ydl.extract_info(arg, download=False)

        embed = (Embed(title='🎵 Now playing:', description=f"[{info['title']}]({info['webpage_url']})", color=0x3498db)
                .add_field(name='Duration', value=Music.parse_duration(info['duration']))
                .add_field(name='Asked by', value=author)
                .add_field(name='Uploader', value=f"[{info['uploader']}]({info['channel_url']})")
                .add_field(name="Queue", value=f"No queued musics")
                .set_thumbnail(url=info['thumbnail']))

        return {'embed': embed, 'source': info['formats'][0]['url'], 'title': info['title']}

    async def edit_message(self, ctx):
        embed = self.song_queue[ctx.guild][0]['embed']
        content = "\n".join([f"({self.song_queue[ctx.guild].index(i)}) {i['title']}" for i in self.song_queue[ctx.guild][1:]]) if len(self.song_queue[ctx.guild]) > 1 else "Pas de musique en attente"
        embed.set_field_at(index=3, name="Queue:", value=content, inline=False)
        await self.message[ctx.guild].edit(embed=embed)

    def play_next(self, ctx):
        voice = get(self.bot.voice_clients, guild=ctx.guild)
        del self.song_queue[ctx.guild][0]
        run_coroutine_threadsafe(self.edit_message(ctx), self.bot.loop)
        voice.play(FFmpegPCMAudio(self.song_queue[ctx.guild][0]['source'], **Music.FFMPEG_OPTIONS), after=lambda e: self.play_next(ctx))
        voice.is_playing()
    
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
      voice = get(self.bot.voice_clients)
      voice_state = member.guild.voice_client
      if voice_state is not None and len(voice_state.channel.members) == 1:
        time.sleep(2)
        run_coroutine_threadsafe(voice.disconnect(), self.bot.loop)
        run_coroutine_threadsafe(self.bot.loop)

    @commands.command(aliases=['p'], brief='Play [url/words]', description='Listen to a video from an url or from a YouTube search')
    async def play(self, ctx, *, video: str):
        channel = ctx.author.voice.channel
        voice = get(self.bot.voice_clients, guild=ctx.guild)
        song = Music.search(ctx.author.mention, video)

        if voice and voice.is_connected():
            await voice.move_to(channel)
        else:
            voice = await channel.connect()     

        await ctx.message.delete()
        if not voice.is_playing():
            self.song_queue[ctx.guild] = [song]
            self.message[ctx.guild] = await ctx.send(embed=song['embed'])
            voice.play(FFmpegPCMAudio(song['source'], **Music.FFMPEG_OPTIONS), after=lambda e: self.play_next(ctx))
            voice.is_playing()
        else:
            self.song_queue[ctx.guild].append(song)
            await self.edit_message(ctx)

    @commands.command(brief='stop', description='Stops the music and disconnects the bot')
    async def stop(self, ctx):
        voice = get(self.bot.voice_clients, guild=ctx.guild)
        channel = ctx.author.voice.channel
        if voice.is_playing():
            ctx.message.delete()
            voice.pause()
            run_coroutine_threadsafe(voice.disconnect(), self.bot.loop)
            
    @commands.command(brief='pause', description='Pause the current video')
    async def pause(self, ctx):
        voice = get(self.bot.voice_clients, guild=ctx.guild)
        if voice.is_connected():
            await ctx.message.delete()
            if voice.is_playing():
                await ctx.send('⏸️ Music paused')
                voice.pause()
            else:
                await ctx.send('⏯️ Music resumed')
                voice.resume()
    
    @commands.command(aliases=['r'],brief='resume', description='Resumes the current video after a pause')
    async def resume(self, ctx):
        voice = get(self.bot.voice_clients, guild=ctx.guild)
        if voice.is_connected():
            await ctx.message.delete()
            if not voice.is_playing():
                await ctx.send('⏯️ Music resumed')
                voice.resume()
            else:
                await ctx.send('Music is already playing')

    @commands.command(aliases=['s'],brief='skip', description='Skip the current video')
    async def skip(self, ctx):
        voice = get(self.bot.voice_clients, guild=ctx.guild)
        if voice.is_playing():
            await ctx.message.delete()
            await ctx.send('⏭️ Music skipped', delete_after=5.0)
            voice.stop()

    @commands.command(brief='remove [index]', description='Remove a song from the queue')
    async def remove(self, ctx, *, num: int):
        voice = get(self.bot.voice_clients, guild=ctx.guild)
        if voice.is_playing():
            del self.song_queue[ctx.guild][num]
            await ctx.message.delete()
            await self.edit_message(ctx)


    @commands.command(name='lyrics', aliases=['l'])
    async def lyrics(self, ctx, *, title: str=''):
      if not title:
        return await ctx.send("Specify a title of a song :thought_balloon:")

      url=f'https://some-random-api.ml/lyrics?title={title}'
      async with ctx.typing():
        async with self.client.get(url) as r:
          if r.status != 200:
            return ctx.send('Failed to get info :x:')
          data = await r.json()
        lyrics = data['lyrics']
        embed = discord.Embed(color=discord.Color(0x5DADEC))
        embed.set_thumbnail(url=data['thumbnail']['genius'])
        lyrics = lyrics[1024:]
        embeds = [embed]
        while len(lyrics) > 0 and len(embeds) < 10:
          embed = discord.Embed(color=discord.Color(0xCCFF00), description=lyrics[:1024])
          lyrics = lyrics[len(embeds)*1024:]
          embeds.append(embed)
        embeds[-1].set_footer(text="Source: Genius")
        for embed in embeds:
          await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Music(bot))
