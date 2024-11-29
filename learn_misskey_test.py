import markovify
import MeCab
import numpy as np
from collections import defaultdict, deque
import os
import re
import json

os.makedirs("models", exist_ok=True)

CONFIG_FILE = "config.json"
INPUT_FILE = "notes.json"

TALKGEN_MODEL_FILE = "models/talkgen_model.npy"
TALKGEN_MODEL_LEN_DEFAULT = 10000

tokenizer = MeCab.Tagger('-Owakati')

# config ファイルのロード
try :
    with open(CONFIG_FILE) as f:
        config = json.load(f)
except FileNotFoundError:
    print(f"{CONFIG_FILE}ファイルがありません")
    exit()

TALK_MODEL_LEN = config["talk_model_len"] if "talk_model_len" in config else TALKGEN_MODEL_LEN_DEFAULT

def remove_misskey_hashtag(text):
    return re.sub(r'#[^\t\n\r\f\v ]+', '', text)

def remove_misskey_mention(text):
    return re.sub(r'@[-_.!~*a-zA-Z0-9;\/?\@&=+\$,%#]+', '', text)

def remove_url(text):
    return re.sub(r'(https?|ftp)(:\/\/[-_.!~*\'()a-zA-Z0-9;\/?:\@&=+\$,%#]+)','', text)

def remove_misskey_MFM(text):
    s = text
    # $[] 系を削除する
    s = re.sub(r'\$\[.*\]','', text)
    s = re.sub(r'\$\[.*?','', s)
    # リンクを削除する
    s = re.sub(r'\??\[.*\]\((.*\))',r'\1', s)
    s = remove_url(s)
    # 太字を削除する
    s = re.sub(r'\*\*(.*?)\*\*',r'\1', s)
    # イタリックを削除する
    s = re.sub(r'_(.*?)_',r'\1', s)
    # <small> <center> <plain>を削除
    s = re.sub(r'<center>|</center>|<\\center>|<¥center>|<small>|</small>|<\\small>|<¥small>|<plain>|</plain>|<\\plain>|<¥plain>','', s)
    # コードを削除
    s = re.sub(r'`(.*?)`',r' \1 ', s)
    s = re.sub(r'```(.*?)```',r' \1 ', s)
    s = re.sub(r'\*\*(.*?)\*\*',r'\1', s)
    # 絵文字を削除
    s = re.sub(r':.*?:', '', s)

    return s


def enqueue_talkgen_model(queue, tokenizer, text) :
    s = remove_misskey_MFM(remove_misskey_hashtag(remove_misskey_mention(text)))
    if len(s) <= 0 or re.fullmatch(r'[ 　]*', s) :
        return
    queue.append(tokenizer.parse(s))
    # len が長い場合は削る
    while len(queue) > TALK_MODEL_LEN :
        queue.popleft()

talkgen_model_queue = deque()
# おはなし（マルコフ連鎖）機能
if os.path.isfile(TALKGEN_MODEL_FILE) :
    talkgen_model_queue = deque(np.load(TALKGEN_MODEL_FILE, allow_pickle=True).tolist())


# 字句解析
try :
    with open(INPUT_FILE) as f:
        note_list = json.load(f)
        for note in note_list:
            if  note["cw"] is not None:
                 enqueue_talkgen_model(talkgen_model_queue, tokenizer, note["cw"])
            if  note["text"] is not None:
                 enqueue_talkgen_model(talkgen_model_queue, tokenizer, note["text"])        
    np.save(TALKGEN_MODEL_FILE, talkgen_model_queue)
except FileNotFoundError:
    print(f"{INPUT_FILE}ファイルがありません")
    exit()