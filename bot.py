import os
import sys
import discord
# import pafy
import yt_dlp
import asyncio
import json
import requests
from asgiref.sync import async_to_sync
from discord.ext import commands
from search_youtube import youtubeQuery
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env')

# Get the Discord token from the environment variables
TOKEN = os.getenv('DISCORD_TOKEN')

# ydl_opts = {'format': 'bestaudio/best', 'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}], 'outtmpl': 'downloads/%(title)s.%(ext)s'}
ydl_opts = {
        'format': 'bestaudio/best',
        'extractaudio': True,
        'audioformat': 'mp3',
        'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
        'restrictfilenames': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'quiet': True,
        'no_warnings': True,
        'default_search': 'auto',
        'source_address': '0.0.0.0',
    }   
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5','options': '-vn'}


# BOT
intents = discord.Intents.all()  # bot-side limiters
client = discord.Client(intents=intents)
bot = commands.Bot(command_prefix='$', intents=intents)


song_dict = dict()
counter = {'count': 0}


"""
################################################################################
#                            --- SUPPORT FUNCTIONS ---                         #
################################################################################
"""

# ctx = context of discord message


@bot.command(name='res', help="Restart the bot")
async def restart(ctx):
    await ctx.send("Bot Restarted.")  # actually not yet
    restart_bot()


def restart_bot():
    '''Restarts the bot.'''
    os.execv(sys.executable, ['python'] + sys.argv)


# def is_connected(ctx):
#     voice_client = get(ctx.bot.voice_clients, guild=ctx.guild)
#     return voice_client and voice_client.is_connected()


async def author_in_voice(ctx):
    """
    Validates if the author of the command is in a voice channel.
        if True: channel.connect()
    """
    if ctx.message.author.voice:
        channel = discord.utils.get(
            ctx.guild.voice_channels, name=ctx.message.author.voice.channel.name)
        voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    else:
        await ctx.send("{} is not connected to a voice channel".format(ctx.message.author.name))
        return
    if not ctx.message.guild.voice_client:
        if voice is not None:  # test if voice is None
            if not voice.is_connected():
                await channel.connect()
            else:
                pass
        else:
            await channel.connect()


async def get_guild_dict(ctx):
    # guild == server; this is to enable multiple servers to use the bot
    guild = ctx.guild
    if not guild.name in song_dict.keys():
        song_dict[guild.name] = {}

    guild_dict = song_dict[guild.name]
    return guild_dict


async def player(ctx, stream_url, stream_title):
    voice_client = ctx.message.guild.voice_client

    # if not is_connected(ctx):
    #     voice_client = ctx.message.guild.voice_client
    #     voice_client.connect()
    try:
        if voice_client.is_playing():
            voice_client.pause()
    except:
        pass
    source = discord.FFmpegPCMAudio(
        stream_url, **FFMPEG_OPTIONS)
    source = discord.PCMVolumeTransformer(source, 0.2)
    msg = await ctx.send('**Now playing:** {}'.format(stream_title))
    voice_client.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(
        play_next(ctx, msg=msg, bot_action=True), bot.loop))


"""
################################################################################
#                          --- SIMPLE BOT COMMANDS ---                         #
################################################################################
"""


@bot.command(name='join', help='Tells the bot to join the voice channel')
async def join(ctx):
    if not ctx.message.author.voice:
        await ctx.send("{} is not connected to a voice channel".format(ctx.message.author.name))
        return
    else:
        channel = ctx.message.author.voice.channel
    await channel.connect()


@bot.command(name='leave', help='To make the bot leave the voice channel')
async def leave(ctx):
    if not ctx.message.author.voice:
        await ctx.send("{} is not connected to a voice channel".format(ctx.message.author.name))
        return
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_connected():
        await voice_client.disconnect()
    else:
        await ctx.send("The bot is not connected to a voice channel.")


@bot.command(name='pause', help='This command pauses the song')
async def pause(ctx, by_user=True):
    if not ctx.message.author.voice:
        await ctx.send("{} is not connected to a voice channel".format(ctx.message.author.name))
        return
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_playing():
        voice_client.pause() #await 
    else:
        if by_user:
            await ctx.send("The bot is not playing anything at the moment.")
        return


@bot.command(name='resume', help='Resumes the song')
async def resume(ctx):
    if not ctx.message.author.voice:
        await ctx.send("{} is not connected to a voice channel".format(ctx.message.author.name))
        return
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_paused():
        voice_client.resume() #await 
    else:
        await ctx.send("The bot was not playing anything before this. Use play_song command")


@bot.command(name='stop', help='Stops the song')
async def stop(ctx):
    if not ctx.message.author.voice:
        await ctx.send("{} is not connected to a voice channel".format(ctx.message.author.name))
        return
    guild_dict = await get_guild_dict(ctx)
    guild_dict.clear()
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_playing():
        voice_client.stop()
    else:
        await ctx.send("The bot is not playing anything at the moment.")


"""
################################################################################
#                          --- PLAYER FUNCTIONS ---                            #
################################################################################
"""


@bot.command(name='r/', help='[cmd][sub]')
async def rlist(ctx, subreddit):
    if not ctx.message.author.voice:
        await ctx.send("{} is not connected to a voice channel".format(ctx.message.author.name))
        return
    guild_dict = await get_guild_dict(ctx)
    url = "http://localhost:9000/api/r/{}/playlist".format(subreddit)

    data = requests.get(url).json()

    for song in data:
        guild_dict[len(guild_dict)] = {
            'title': data[song]['title'], 'url': data[song]['url']}
    print(song_dict)
    print(guild_dict)
    await play(ctx, by_user=False)


@bot.command(name='play', help='To play song, [command_prefix]play [song name]')
async def play(ctx, *terms, by_user=True):
    await asyncio.sleep(1)

    try:
        await author_in_voice(ctx)
    except:
        return

    voice_client = ctx.message.guild.voice_client
    
    print(voice_client.source)    

    guild_dict = await get_guild_dict(ctx)

    async with ctx.typing():

        # if called by user: url from yt query. else: url from dict
        if by_user:
            print(*terms)
            # try:
            await asyncio.sleep(1)
            print("slept")
            
            url = await youtubeQuery(terms)
            print(url)
            # except:
            #     await ctx.send("No results found for {}".format(*terms))
            #     return
        else:
            url = guild_dict[counter['count']]['url']

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                song = ydl.extract_info(url, download=False)
                print(song)
                # print(song_info)
            # song = pafy.new(url).getbestaudio()
        except:
            if by_user:
                await ctx.send("Cannot get streaming data for {}".format(*terms))
            return

        # guild_dict[len(guild_dict)] = {'title': song.title, 'url': url}

        try:
            if voice_client.is_playing():
                await ctx.send('**Queued:** {}'.format(song.title))
                return
        except AttributeError:
            return

        # try:
        #     guild_dict[len(guild_dict)] = {
        #         'title': song.title, 'url': url}
        # except AttributeError:
        #     await ctx.send('No song found.')
        #     return

        # song = guild_dict[counter['count']]
        # print(song_dict)
        # print(guild_dict)
        await player(ctx, song['url'], song['title'])


@bot.command(name='next', help='Next song!')
async def play_next(ctx, msg=None, bot_action=None):
    await asyncio.sleep(2)
    voice_client = ctx.message.guild.voice_client
    # guild = ctx.guild
    guild_dict = await get_guild_dict(ctx)

    try:
        guild_dict[counter['count'] + 1]
        counter['count'] += 1
        song = guild_dict[counter['count']]

        if len(song['url']) < 100:
            song_pafy = pafy.new(song['url']).getbestaudio()
            song['url'] = song_pafy.url
            song['title'] = song_pafy.title

    except KeyError:
        if bot_action is None:
            await ctx.send('End of List! Use --play to add more songs..')
            return
        else:
            await asyncio.sleep(2)
            guild_dict.clear()
            await msg.delete()
            counter['count'] = 0
            return

    if msg:
        await msg.delete()
    await player(ctx, song['url'], song['title'])


@bot.command(name='back', help='Previous song!')
async def play_prev(ctx, msg=None):
    if not ctx.message.author.voice:
        await ctx.send("{} is not connected to a voice channel".format(ctx.message.author.name))
        return
    await asyncio.sleep(2)
    guild_dict = await get_guild_dict(ctx)
    voice_client = ctx.message.guild.voice_client
    # voice_channel.stop()
    if counter['count'] != 0:
        counter['count'] -= 1
    else:
        await ctx.send('This is the first song in the list!')
        return
    try:
        song = guild_dict[counter['count']]
    except:
        print('Error, maybe do ExceptKeyError?')
    if msg:
        await msg.delete()
    await player(ctx, song['url'], song['title'])


bot.run(TOKEN)
