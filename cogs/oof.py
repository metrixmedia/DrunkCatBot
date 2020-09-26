import discord
from discord.ext import commands


class Oof(commands.Cog):
    def __init__(self, client):
        self.client = client


    @commands.command()
    async def oof(self, ctx): 
        await ctx.send('Big Oof to @Rolguar')

        return



def setup(client):
    client.add_cog(Oof(client))