import markovify
import MeCab
import numpy as np
from collections import defaultdict, deque
import os
import re
import json

os.makedirs("models", exist_ok=True)

CONFIG_FILE = "config.json"
INPUT_FILE = "input.txt"

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

def escape_emoji(text):
    return re.sub(r'<:([-_.!~*a-zA-Z0-9;\/?\@&=+\$,%#]+):([0-9]+)>', r':\1:', text)

def remove_mention(text):
    return re.sub(r'<@[-_.!~*a-zA-Z0-9;\/?\@&=+\$,%#]+>', '', text)

def restore_emoji(match, emojis):
    emoji_name = match.group(1) 
    search_result_list = list(filter(lambda x: x.name == emoji_name, emojis))
    if len(search_result_list) <= 0 :
        return f':{emoji_name}:'

    return str(search_result_list[0])

def enqueue_talkgen_model(queue, tokenizer, text) :
    s = escape_emoji(remove_mention(text))
    queue.append(tokenizer.parse(s))
    # len が長い場合は削る
    while len(queue) > TALK_MODEL_LEN :
        queue.popleft()
    np.save(TALKGEN_MODEL_FILE, queue)

talkgen_model_queue = deque()
# おはなし（マルコフ連鎖）機能
if os.path.isfile(TALKGEN_MODEL_FILE) :
    talkgen_model_queue = deque(np.load(TALKGEN_MODEL_FILE, allow_pickle=True).tolist())


# 字句解析
try :
    with open(INPUT_FILE) as f:
        for line in f:
            enqueue_talkgen_model(talkgen_model_queue, tokenizer, line)
            np.save(TALKGEN_MODEL_FILE, talkgen_model_queue)
except FileNotFoundError:
    print(f"{CONFIG_FILE}ファイルがありません")
    exit()