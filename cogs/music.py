from discord import Embed, FFmpegPCMAudio
from discord.ext import commands
from discord.utils import get
import ksoftapi
import discord
import time
import os
from asyncio import run_coroutine_threadsafe
from tools import get_json, is_url
from re import findall
from pafy import new
from replit import db

class Music(commands.Cog, name='Musique'):
    """
    Module permettant d'écouter des vidéos.
    """
    FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

    def __init__(self, bot):
        self.bot = bot
        self.song_queue = {}
        self.message = {}

    @staticmethod
    async def search(author, arg):
        url = arg if is_url(arg) else f'https://www.youtube.com/results?search_query={arg}'
        resp = await get_json(url, json=False)
        video_id = findall(r"watch\?v=(\S{11})", resp)[0]
        video = new(video_id)

        embed = (Embed(title='🎵 Vidéo en cours:', description=f"[{video.title}](https://www.youtube.com/watch?v={video_id})", color=0x3498db)
                .add_field(name='Durée', value=video.duration)
                .add_field(name='Demandée par', value=author)
                .add_field(name='Chaine', value=video.author)
                .add_field(name="File d'attente", value=f"Pas de vidéos en attente")
                .set_thumbnail(url=video.thumb))
        
        def videotitle():
          videotit = video.title

        return {'embed': embed, 'source': video.getbestaudio().url, 'title': video.title}

    async def edit_message(self, ctx):
        embed = self.song_queue[ctx.guild][0]['embed']
        content = "\n".join([f"({self.song_queue[ctx.guild].index(i)}) {i['title']}" for i in self.song_queue[ctx.guild][1:]]) if len(self.song_queue[ctx.guild]) > 1 else "Pas de vidéos en attente"
        embed.set_field_at(index=3, name="File d'attente:", value=content, inline=False)
        await self.message[ctx.guild].edit(embed=embed)

    def play_next(self, ctx):
        voice = get(self.bot.voice_clients, guild=ctx.guild)
        if len(self.song_queue[ctx.guild]) > 1:
            del self.song_queue[ctx.guild][0]
            run_coroutine_threadsafe(self.edit_message(ctx), self.bot.loop)
            voice.play(FFmpegPCMAudio(self.song_queue[ctx.guild][0]['source'], **Music.FFMPEG_OPTIONS), after=lambda e: self.play_next(ctx))
            voice.is_playing()
        else:
            time.sleep(60)
            run_coroutine_threadsafe(voice.disconnect(), self.bot.loop)
            run_coroutine_threadsafe(self.message[ctx.guild].delete(), self.bot.loop)

    @commands.command(aliases=['p'], brief='play [url/mots]', description='Écouter une vidéo depuis un lien ou une recherche youtube')
    async def play(self, ctx, *, video: str):
        channel = ctx.author.voice.channel
        voice = get(self.bot.voice_clients, guild=ctx.guild)
        song = await Music.search(ctx.author.mention, video)

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

    @commands.command(brief='pause', description='Mettre la vidéo en pause ou la reprendre')
    async def pause(self, ctx):
        voice = get(self.bot.voice_clients, guild=ctx.guild)
        if voice.is_connected():
            await ctx.message.delete()
            if voice.is_playing():
                await ctx.send('⏸️ Vidéo en pause', delete_after=5.0)
                voice.pause()
            else:
                await ctx.send('⏯️ Vidéo reprise', delete_after=5.0)
                voice.resume()

    @commands.command(brief='skip', description='Skipper une vidéo')
    async def skip(self, ctx):
        voice = get(self.bot.voice_clients, guild=ctx.guild)
        if voice.is_playing():
            await ctx.message.delete()
            await ctx.send('⏭️ Musique skippée', delete_after=5.0)
            voice.stop()

    @commands.command(brief='remove [index]', description="Supprimer une vidéo de la file d'attente")
    async def remove(self, ctx, *, num: int):
        voice = get(self.bot.voice_clients, guild=ctx.guild)
        if voice.is_playing():
            del self.song_queue[ctx.guild][num]
            await ctx.message.delete()
            await self.edit_message(ctx)
      
    @commands.command(name='lyrics', aliases=['ly'])
    async def get_lyrics(self, ctx, *, query: str):
        """Get lyrics of current song"""

        kclient = ksoftapi.Client(os.environ['KSoft_Token'])

        try:
            async with ctx.typing():
                results = await kclient.music.lyrics(query)
        except ksoftapi.NoResults:
            await ctx.send(f'No lyrics found for `{query}`')
        else:
            lyrics = results[0].lyrics
            result = results[0]
            embed = discord.Embed(title=f'{result.name} - {result.artist}', color=discord.Color(0xCCFF00), description=lyrics[:2048])
            embed.set_thumbnail(url=result.album_art)
            embed.set_author(name="Lyrics:")
            lyrics = lyrics[2048:]
            embeds = [embed] # create embeds' list for long lyrics
            while len(lyrics) > 0 and len(embeds) < 10: # limiting embeds to 10
                embed = discord.Embed(color=discord.Color(0xCCFF00), description=lyrics[:2048])
                lyrics = lyrics[len(embeds)*2048:]
                embeds.append(embed)
            embeds[-1].set_footer(text="Source: KSoft.Si") # set footer for last embed
            for embed in embeds:
                await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Music(bot))