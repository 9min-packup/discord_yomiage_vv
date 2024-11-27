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
import markovify
import MeCab
from datetime import datetime, timedelta

VV_TUMUGI = 8
VV_HIMARI = 14
VV_ZUNDAMOM = 3 
VV_TYPE_T = 47
VV_SAYO = 46

os.makedirs("out", exist_ok=True)
os.makedirs("dict", exist_ok=True)
os.makedirs("models", exist_ok=True)
os.makedirs("play", exist_ok=True)

CONFIG_FILE = "config.json"
WORD_DICT_FILE = "dict/word_dict.npy"
TALK_DICT_FILE = "dict/talk_dict.npy"
TALKGEN_MODEL_FILE = "models/talkgen_model.npy"
PLAY_DICT_FILE = "dict/play_dict.npy"

TALKGEN_MODEL_LEN_DEFAULT = 10000
TALKGEN_MODEL_TRIES_MIN_DEFAULT = 10
TALKGEN_MODEL_TRIES_MAX_DEFAULT = 100
TALKGEN_FAILURE_TEXT = '喋ることない'
TALKGEN_STATESIZE_MIN_DEFAULT = 2
TALKGEN_STATESIZE_MAX_DEFAULT = 6

intents=discord.Intents.all()
queue_dict = defaultdict(deque)
tokenizer = MeCab.Tagger('-Owakati')

# config ファイルのロード
try :
    with open(CONFIG_FILE) as f:
        config = json.load(f)
except FileNotFoundError:
    print(f"{CONFIG_FILE}ファイルがありません")
    exit()

TOKEN = config['token']
COMMAND_PREFIX = config["command_prefix"] if "command_prefix" in config else "$"
BOTNAME = config["botname"] if "botname" in config else "読み上げちゃん"
BOTNAME_VC = config["botname_vc"] if "botname_vc" in config else "読み上げちゃん"
TALK_DETECTION_RE = config["talk_detection_re"] if "talk_detection_re" in config else NONE
TALK_MODEL_LEN = config["talk_model_len"] if "talk_model_len" in config else TALKGEN_MODEL_LEN_DEFAULT
TALKGEN_MODEL_TRIES_MIN = config["tries_min"] if "tries_min" in config else TALKGEN_MODEL_TRIES_MIN_DEFAULT
TALKGEN_MODEL_TRIES_MAX = config["tries_max"] if "tries_max" in config else TALKGEN_MODEL_TRIES_MAX_DEFAULT
TALKGEN_STATESIZE_MIN = config["statesize_min"] if "statesize_min" in config else TALKGEN_STATESIZE_MIN_DEFAULT
TALKGEN_STATESIZE_MAX = config["statesize_max"] if "statesize_max" in config else TALKGEN_STATESIZE_MAX_DEFAULT

# 正規表現のメタ文字をエスケープ
COMMAND_PREFIX_ESCAPED = re.sub(r'([\*|\\|\.|\+|\?|\{|\}|\(|\)|\[|\]|\^|\$|\|])', r'\\\1', COMMAND_PREFIX)

bot = commands.Bot(intents=intents, command_prefix=COMMAND_PREFIX)
client = discord.Client(intents=intents)
eniaIsIn = False

# ボイスの種類を指定できる
vv_character = VV_TUMUGI

voiceChannel: VoiceChannel = None
text_channel_id=-1

def escape_emoji(text):
    return re.sub(r'<:([-_.!~*a-zA-Z0-9;\/?\@&=+\$,%#]+):([0-9]+)>', r':\1:', text)

def remove_mention_channel(text):
    return re.sub(r'<[@|#][-_.!~*a-zA-Z0-9;\/?\@&=+\$,%#]+>', '', text)

def remove_url(text):
    return re.sub(r'(https?|ftp)(:\/\/[-_.!~*\'()a-zA-Z0-9;\/?:\@&=+\$,%#]+)','', text)

def restore_emoji(match, emojis):
    emoji_name = match.group(1) 
    search_result_list = list(filter(lambda x: x.name == emoji_name, emojis))
    if len(search_result_list) <= 0 :
        return f':{emoji_name}:'

    return str(search_result_list[0])

def enqueue_talkgen_model(queue, tokenizer, text) :
    s = escape_emoji(remove_url(remove_mention_channel(text)))
    if len(s) <= 0 or re.fullmatch(r'[ 　]*', s) :
        return
    queue.append(tokenizer.parse(s))
    # len が長い場合は削る
    while len(queue) > TALK_MODEL_LEN :
        queue.popleft()

#辞書機能
if not os.path.isfile(WORD_DICT_FILE) :
    dict = {}
    np.save(WORD_DICT_FILE, dict)
word_dict = np.load(WORD_DICT_FILE, allow_pickle=True).item()

# おはなし機能
if not os.path.isfile(TALK_DICT_FILE) :
    dict = {}
    np.save(TALK_DICT_FILE, dict)
talk_dict = np.load(TALK_DICT_FILE, allow_pickle=True).item()

# おはなし（マルコフ連鎖）機能
if not os.path.isfile(TALKGEN_MODEL_FILE) :
    queue = deque()
    np.save(TALKGEN_MODEL_FILE, queue)
talkgen_model_queue = deque(np.load(TALKGEN_MODEL_FILE, allow_pickle=True).tolist())

# mp3 再生機能
if not os.path.isfile(PLAY_DICT_FILE) :
    dict = {}
    np.save(PLAY_DICT_FILE, dict)
play_dict = np.load(PLAY_DICT_FILE, allow_pickle=True).item()


fs = 24000
seed = 4183
count = 0

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

    if message.content[0] == '/' :
        return

    if re.match(rf'^{COMMAND_PREFIX_ESCAPED}', message.content):
        await bot.process_commands(message)
        return

    # モデルに保存
    enqueue_talkgen_model(talkgen_model_queue, tokenizer, message.content) 
    np.save(TALKGEN_MODEL_FILE, talkgen_model_queue)

    # 読み上げる
    await yomiage(message, message.author.display_name, 'さん')

    # 反応してお喋りする
    if bot.user in message.mentions :
        await _talk_m(message, message.reply)
    elif TALK_DETECTION_RE is not None and re.search(TALK_DETECTION_RE, message.content) :
        await _talk_m(message, message.channel.send)

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
    args['text'] = re.sub(r'<:([-_.!~*a-zA-Z0-9;\/?\@&=+\$,%#]+):([0-9]+)>', r' \1 ', remove_mention_channel(args['text']))


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
    wav.export(f"out/out_{message.guild.id}_{count}.wav",format='wav')
    sound = pydub.AudioSegment.from_wav(f"out/out_{message.guild.id}_{count}.wav")
    sound.export(f"out/out_{message.guild.id}_{count}.mp3", format="mp3")
    os.remove(f"out/out_{message.guild.id}_{count}.wav") 
    enqueue(message.guild, FFmpegPCMAudio(f"out/out_{message.guild.id}_{count}.mp3"))

def enqueue(guild, source):
    global voiceChannel
    queue = queue_dict[guild.id]
    queue.append(source)

    if not voiceChannel.is_playing():
        play_queue(queue)

def play_queue(queue):
    global voiceChannel
    if not queue or voiceChannel.is_playing():
        return
    source = queue.popleft()
    voiceChannel.play(source, after=lambda e:play_queue(queue))

@bot.command()
async def c(ctx) :
        global eniaIsIn
        global voiceChannel
        global text_channel_id

        if voiceChannel is not None :
            await ctx.send('もういますよ。')
            return

        if ctx.message.author.voice is None :
            await ctx.send('ボイスチャットで呼んでください。')
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
        queue = queue_dict[ctx.message.guild.id]
        queue.clear()
        return

@bot.command()
async def next(ctx) :
        global eniaIsIn
        global voiceChannel
        global text_channel_id
        if voiceChannel is None :
            await ctx.send('ボイスチャットで呼んでください。')
            return
        if ctx.message.channel.id != text_channel_id :
            await ctx.send('ボイスチャットで呼んでください。')
            return
 
        if voiceChannel.is_playing():
            voiceChannel.stop()
            queue = queue_dict[ctx.message.guild.id]
            if len(queue) >=1 :
                play_queue(queue)
            await ctx.message.add_reaction('👍')
        else :
            await ctx.message.add_reaction('💤')
 
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
    await _talk_m(ctx.message, ctx.send) 

@bot.command()
async def talk_d(ctx) :
    await _talk_d(ctx.message, ctx.send) 

async def _talk_d(message, send) :
    global word_dict, talk_dict, text_channel_id
    EMOJI_TOKEN = '{emoji}'
    DICT_TOKEN = '{dict}'
    DICT_YOMI_TOKEN = '{dict_yomi}'

    keys = list(talk_dict.keys())
    if len(keys) <= 0 :
        await send(TALKGEN_FAILURE_TEXT)
        return

    key = random.choice(keys)
    talk_text = talk_dict[key]

    # {dict}を辞書に登録された単語（ランダム）に置換する
    talk_text = re.sub(DICT_TOKEN, lambda match: random.choice(list(word_dict.keys())), talk_text)

    # {dict_yomi}を辞書に登録された単語（ランダム）の読みに置換する
    talk_text = re.sub(DICT_YOMI_TOKEN, lambda match: word_dict[random.choice(list(word_dict.keys()))], talk_text)

    # {emoji}をランダムな絵文字に置換する
    talk_text = re.sub(EMOJI_TOKEN, lambda match: str(random.choice(message.guild.emojis)), talk_text)

    await send(talk_text)
    
    if voiceChannel is None :
        return

    if eniaIsIn and (message.channel.id == text_channel_id) :
        await play_voice_vox(message, BOTNAME_VC, '', talk_text, vv_character)

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

@bot.command()
async def play(ctx, arg : str) :
        global eniaIsIn
        global voiceChannel
        global text_channel_id
        global play_dict
        if voiceChannel is None :
            await ctx.send('ボイスチャットで呼んでください。')
            return
        if ctx.message.channel.id != text_channel_id :
            await ctx.send('ボイスチャットで呼んでください。')
            return

        if arg in play_dict :
            filename = play_dict[arg]
            filepath = 'play/' + filename
            if os.path.isfile(filepath) :
                enqueue(ctx.message.guild, FFmpegPCMAudio(filepath))
                await ctx.send('再生: ' + filename)
            else :
                await ctx.send('ファイルがありません: ' + filename)
  
        else :
            await ctx.send('登録されていません。 : ' + arg)

        return

@bot.command()
async def play_add(ctx) :
        global play_dict

        if ctx.message.attachments is None :
             await ctx.send('添付ファイルを確認できません。')
             return

        if len(ctx.message.attachments) <= 0 :
             await ctx.send('添付ファイルがありません。1つの音声ファイル(.mp3)を添付してください。')
             return

        if len(ctx.message.attachments) >= 2 :
             await ctx.send('添付ファイルが多すぎます。1つの音声ファイル(.mp3)を添付してください')
             return

        attachment = ctx.message.attachments[0]
        if attachment.content_type is None or attachment.content_type != 'audio/mpeg' :
             await ctx.send('添付ファイルが音声ファイル(.mp3)ではありません。音声ファイル(.mp3)を添付してください')
             return

        filename = attachment.filename
        tagname = filename.replace('.mp3', '')

        await attachment.save("play/" + filename)

        play_dict[tagname] = filename
        np.save(PLAY_DICT_FILE, play_dict)
        await ctx.send('音声を登録しました。 : ' + tagname + ' -> ' + filename)
        return

@bot.command()
async def play_check(ctx, arg : str) :
        global play_dict
        if arg in play_dict :
            await ctx.send('登録されています。 : ' + arg + ' -> ' + play_dict[arg])
        else :
            await ctx.send('登録されていません。 : ' + arg)

@bot.command()
async def play_list(ctx) :
        global play_dict
        str_data = json.dumps(play_dict, indent=2, ensure_ascii=False)
        await ctx.send('音声の一覧はこちらです。\n```\n' + str_data + '\n```')

@bot.command()
async def play_rm(ctx, arg : str) :
        global play_dict
        if arg in play_dict :
            target = play_dict.pop(arg)
            np.save(PLAY_DICT_FILE, play_dict)
            filepath = 'play/' + target
            if os.path.isfile(filepath) :
                os.remove(filepath) 

            await ctx.send('音声を削除しました。 : ' + arg + ' -> ' + target)
        else :
            await ctx.send('登録されていません。 : ' + arg)

@bot.command()
async def talk_m(ctx) :
    await _talk_m(ctx.message, ctx.send, tries=TALKGEN_MODEL_TRIES_MIN) 

async def _talk_m(message, send, state_size=None, tries=None) :
    if len(talkgen_model_queue) <= 0 :
        await _talk_d(message, send)
        return

    s_size = random.randint(TALKGEN_STATESIZE_MIN, TALKGEN_STATESIZE_MAX) if state_size is None else state_size

    # learn model from text.
    text_model = markovify.NewlineText(''.join(talkgen_model_queue), state_size=s_size)

    t = random.randint(TALKGEN_MODEL_TRIES_MIN, TALKGEN_MODEL_TRIES_MAX) if tries is None else tries

    # ... and generate from model.
    talk_text = text_model.make_sentence(tries=t)
    if talk_text is None : 
       await _talk_d(message, send)
       return
    
    # 文章の整形
    talk_text = talk_text_parse(talk_text)

    # 絵文字を復元する
    talk_text = re.sub(r':([a-zA-Z0-9_]+):', lambda m: restore_emoji(m, message.guild.emojis), talk_text)

    await send(talk_text)
    
    if voiceChannel is None :
        return

    if eniaIsIn and (message.channel.id == text_channel_id) :
        await play_voice_vox(message, BOTNAME_VC, '', talk_text, vv_character)

def talk_text_parse(text):
    talk_text_array = text.split()

    emoji_flag = False
    after_alphabet_flag = False
    for i in range(len(talk_text_array)):
        if talk_text_array[i] == ':' :
            emoji_flag = True if not emoji_flag else False
            after_alphabet_flag = False
            continue

        m_period = re.match(r'[.!;,\?]', talk_text_array[i])
        if m_period:
            if not emoji_flag:
                talk_text_array[i] = m_period.group(0) + ' '
            after_alphabet_flag = False
            continue

        m_alphabet_word = re.match(r'[a-zA-Z0-9-_.!~*\(\);?\@&=+\$,%#\"\'\`\<\>]+', talk_text_array[i])
        if m_alphabet_word:
            if not emoji_flag and after_alphabet_flag:
                talk_text_array[i] = ' ' + m_alphabet_word.group(0)
            after_alphabet_flag = True
            continue

        after_alphabet_flag = False

    return ''.join(talk_text_array)

@bot.command()
async def learn_history(ctx, arg : str) :
    limit = int(arg)
    limit = limit if limit else 0
    limit = limit if limit >= 0 else 0
    limit = limit if limit <= TALK_MODEL_LEN else TALK_MODEL_LEN
    async for message in ctx.channel.history(
        limit=limit,
        oldest_first=True,
    ):
        if message.author.bot:
            continue

        if len(message.content) <= 0 :
            continue

        if message.content[0] == '/' :
            continue

        if re.match(rf'^{COMMAND_PREFIX_ESCAPED}', message.content) :
            continue

        enqueue_talkgen_model(talkgen_model_queue, tokenizer, message.content) 
    
    np.save(TALKGEN_MODEL_FILE, talkgen_model_queue)
    await ctx.message.add_reaction('👍')

@bot.command()
async def learn_forget(ctx) :
    global talkgen_model_queue
    talkgen_model_queue = deque()
    np.save(TALKGEN_MODEL_FILE, talkgen_model_queue)
    await ctx.message.add_reaction('👍')

bot.run(TOKEN)
