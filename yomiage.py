import discord
from discord.channel import VoiceChannel
from discord.player import FFmpegPCMAudio
from discord.ext import commands
import pydub
import soundfile
import re
import os
import json
import requests
import wave
import numpy as np
from collections import defaultdict, deque
from pydub import AudioSegment
import random

VV_TUMUGI = 8
VV_HIMARI = 14
VV_ZUNDAMOM = 3 
VV_TYPE_T = 47
VV_SAYO = 46

os.makedirs("out", exist_ok=True)
os.makedirs("dict", exist_ok=True)

CONFIG_FILE = "config.json"
WORD_DICT_FILE = "dict/word_dict.npy"
TALK_DICT_FILE = "dict/talk_dict.npy"

try :
    with open(CONFIG_FILE) as f:
        config = json.load(f)
except FileNotFoundError:
    print(f"{CONFIG_FILE}ファイルがありません")
    exit()

intents=discord.Intents.all()

queue_dict = defaultdict(deque)

if not os.path.isfile(WORD_DICT_FILE) :
    dict = {}
    np.save(WORD_DICT_FILE, dict)

if not os.path.isfile(TALK_DICT_FILE) :
    dict = {}
    np.save(TALK_DICT_FILE, dict)

#辞書機能
word_dict = np.load(WORD_DICT_FILE, allow_pickle=True).item()

# おはなし機能
talk_dict = np.load(TALK_DICT_FILE, allow_pickle=True).item()

fs = 24000
seed = 4183
count = 0

# Bot のトークン
TOKEN = config['token']

bot = commands.Bot(intents=intents, command_prefix='$')
client = discord.Client(intents=intents)
eniaIsIn = False

# ボイスの種類を指定できる
vv_character = VV_TUMUGI

voiceChannel: VoiceChannel = None
text_channel_id=-1


@bot.event
async def on_ready():
    print('サーバーにログインしました')

@bot.event
async def on_message(message):
    global voiceChannel
    global eniaIsIn, mode, text_channel_id

    if message.author.bot:
        return

    if len(message.content) <= 0 :
        return

    if message.content[0] == '$' :
        await bot.process_commands(message)
        return

    if message.content[0] == '/' :
        return

    if message.content[0] == '!' :
        return

    await yomiage(message, message.author.display_name, 'さん')


async def yomiage(message, username, keisyou)  :
    if eniaIsIn and (message.channel.id == text_channel_id) :
        await play_voice_vox(message, username, keisyou, message.content, vv_character)

def word_replace(args) :
    global word_dict
    
    for key in word_dict:
        prog = re.compile(key)
        args['user'] =  re.sub(prog, word_dict[key], args['user'])
        args['text'] =  re.sub(prog, word_dict[key], args['text'])

async def play_voice_vox(message, user, keisyou, text, speaker):
    global count, client
    global voiceChannel

    if voiceChannel is None :
        return 

    count = (count + 1) % 100

    s = re.sub(r'(https?|ftp)(:\/\/[-_.!~*\'()a-zA-Z0-9;\/?:\@&=+\$,%#]+)','ゆーあーるえる', text)
    args = { 'user' : user, 'text' : s }
    word_replace(args)
    args['text'] = re.sub(r'<:([-_.!~*a-zA-Z0-9;\/?\@&=+\$,%#]+):([0-9]+)>', r' \1 ', args['text'])

    if len(args['text']) >= 100 :
        args['text'] = args['text'][:140] + ' いかりゃく '

    host = 'localhost'
    port = 50021
    params = (
        ('text', '' + args['user'] + keisyou + '、    ' +  args['text']),
        ('speaker', speaker),
    )
    response1 = requests.post(
        f'http://{host}:{port}/audio_query',
        params=params
    )
    headers = {'Content-Type': 'application/json',}
    response2 = requests.post(
        f'http://{host}:{port}/synthesis',
        headers=headers,
        params=params,
        data=json.dumps(response1.json())
    )
    wav_a = AudioSegment(
        data=response2.content,
        sample_width=2,
        frame_rate=24000,
        channels=1
    )
    wav_s = AudioSegment.silent(duration=100, frame_rate=24000)
    wav = wav_s + wav_a.fade_in(100).fade_out(100) + wav_s
    wav.export(f"out/out_{count}.wav",format='wav')
    sound = pydub.AudioSegment.from_wav(f"out/out_{count}.wav")
    sound.export(f"out/out_{count}.mp3", format="mp3")
    enqueue(message.guild, FFmpegPCMAudio(f"out/out_{count}.mp3"))

def enqueue(guild, source):
    global voiceChannel
    queue = queue_dict[guild.id]
    queue.append(source)

    if not voiceChannel.is_playing():
        play(queue)

def play(queue):
    global voiceChannel
    if not queue or voiceChannel.is_playing():
        return
    source = queue.popleft()
    voiceChannel.play(source, after=lambda e:play(queue))

# @bot.command()
# async def talk_f(ctx, arg) :
#    if ctx.author.id != KANRI_USER_ID :
#        return
#    channel = discord.utils.get(ctx.guild.channels, id=FREE_CHANNEL_ID)
#    await channel.send(arg)

# @bot.command()
# async def talk_w(ctx, arg) :
#    if ctx.author.id != KANRI_USER_ID :
#        return
#    channel = discord.utils.get(ctx.guild.channels, id=WORK_CHANNEL_ID)
#    await channel.send(arg)    

@bot.command()
async def c(ctx) :
        global eniaIsIn
        global voiceChannel
        global text_channel_id

        if voiceChannel is not None :
            await ctx.send('もういますよ。')
            return

        voiceChannel = await VoiceChannel.connect(ctx.message.author.voice.channel)
        if voiceChannel is None :
            await ctx.send('ボイスチャットで呼んでください。')
            return
        text_channel_id = ctx.message.channel.id
        await ctx.send('読み上げを開始します。')
        eniaIsIn = True
        return

@bot.command()
async def d(ctx) :
        global eniaIsIn
        global voiceChannel
        global text_channel_id
        if voiceChannel is None :
            await ctx.send('ボイスチャットで呼んでください。')
            return
        if ctx.message.channel.id != text_channel_id :
            await ctx.send('ボイスチャットで呼んでください。')
            return
        voiceChannel.stop()
        text_channel_id = -1
        await ctx.send('お疲れ様でした。')
        await voiceChannel.disconnect()
        voiceChannel = None
        eniaIsIn = False
        return


@bot.command()
async def himari(ctx) :
        global vv_character, VV_HIMARI
        vv_character = VV_HIMARI
        await ctx.send('声:冥鳴ひまり')
        return

@bot.command()
async def tumugi(ctx) :
        global vv_character, VV_TUMUGI
        vv_character = VV_TUMUGI
        await ctx.send('声:春日部つむぎ')
        return

@bot.command()
async def zundamon(ctx) :
        global vv_character, VV_ZUNDAMOM
        vv_character = VV_ZUNDAMOM
        await ctx.send('声:ずんだもん')
        return

@bot.command()
async def sayo(ctx) :
        global vv_character, VV_SAYO
        vv_character = VV_SAYO
        await ctx.send('声:小夜')
        return

@bot.command()
async def tt(ctx) :
        global vv_character, VV_TYPE_T
        vv_character = VV_TYPE_T
        await ctx.send('声:ナースロボタイプT')
        return

@bot.command()
async def dict_add(ctx, arg1 : str, arg2 : str) :
        global word_dict
        word_dict[arg1] = arg2
        np.save(WORD_DICT_FILE, word_dict)
        await ctx.send('辞書に登録しました。 : ' + arg1 + ' -> ' + arg2)
        return

@bot.command()
async def dict_check(ctx, arg : str) :
        global word_dict
        if arg in word_dict :
            await ctx.send('辞書に登録されています。 : ' + arg + ' -> ' + word_dict[arg])
        else :
            await ctx.send('辞書に登録されていません。 : ' + arg)

@bot.command()
async def dict_list(ctx) :
        global word_dict
        str_data = json.dumps(word_dict, indent=2, ensure_ascii=False)
        await ctx.send('辞書の一覧はこちらです。\n```\n' + str_data + '\n```')

@bot.command()
async def dict_rm(ctx, arg : str) :
        global word_dict
        if arg in word_dict :
            target = word_dict.pop(arg)
            np.save(WORD_DICT_FILE, word_dict)
            await ctx.send('辞書から削除しました。 : ' + arg + ' -> ' + target)
        else :
            await ctx.send('辞書に登録されていません。 : ' + arg)

@bot.command()
async def talk(ctx) :
    global talk_dict, text_channel_id
    keys = list(talk_dict.keys())
    if len(keys) <= 0 :
        await ctx.send('喋ることない')
        return

    key = random.choice(keys)
    await ctx.send(talk_dict[key])
    
    if voiceChannel is None :
        return

    if eniaIsIn and (ctx.message.channel.id == text_channel_id) :
        await play_voice_vox(ctx.message, '最強かわいい読み上げちゃん', '', talk_dict[key], vv_character)

@bot.command()
async def talk_add(ctx, arg1 : str, arg2 : str) :
        global talk_dict
        talk_dict[arg1] = arg2
        np.save(TALK_DICT_FILE, talk_dict)
        await ctx.send('会話文を登録しました。 : ' + arg1 + ' -> ' + arg2)
        return

@bot.command()
async def talk_check(ctx, arg : str) :
        global talk_dict
        if arg in talk_dict :
            await ctx.send('登録されています。 : ' + arg + ' -> ' + talk_dict[arg])
        else :
            await ctx.send('登録されていません。 : ' + arg)

@bot.command()
async def talk_list(ctx) :
        global talk_dict
        str_data = json.dumps(talk_dict, indent=2, ensure_ascii=False)
        await ctx.send('会話文の一覧はこちらです。\n```\n' + str_data + '\n```')

@bot.command()
async def talk_rm(ctx, arg : str) :
        global talk_dict
        if arg in talk_dict :
            target = talk_dict.pop(arg)
            np.save(TALK_DICT_FILE, talk_dict)
            await ctx.send('会話文を削除しました。 : ' + arg + ' -> ' + target)
        else :
            await ctx.send('登録されていません。 : ' + arg)


bot.run(TOKEN)
