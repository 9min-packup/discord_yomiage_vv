from misskey_api import *
import re
import os
import json

CONFIG_FILE = "config.json"

# config ファイルのロード
try :
    with open(CONFIG_FILE) as f:
        config = json.load(f)
except FileNotFoundError:
    print(f"{CONFIG_FILE}ファイルがありません")
    exit()

# Misskey
MISSKEY_CONFIG = config['misskey'] if "misskey" in config else None
MISSKEY_HOST = MISSKEY_CONFIG['host']
MISSKEY_TOKEN = MISSKEY_CONFIG['token']
MISSEKY_TIMELINE = MISSKEY_CONFIG['timeline']
MISSEKY_LIST_ID = MISSKEY_CONFIG['list_id'] if "list_id" in MISSKEY_CONFIG else None

api = MisskeyApi(MISSKEY_HOST, MISSKEY_TOKEN)

async def my_loop():
    try:
        r = await api.show_user()
        print(r)
    except Exception as e:
        print(e)
    await start_misskey_streaming(api, MISSEKY_TIMELINE,listId=MISSEKY_LIST_ID, onReceive=on_note_recieved)

async def start_misskey_streaming(api, timeline, listId=None, onReceive=None):
    if timeline == "home":
        await api.htl_streaming(withRenotes=False, onReceive=onReceive)
    elif timeline == "local":
        await api.ltl_streaming(withRenotes=False, onReceive=onReceive)
    elif timeline == "global":
       await api.gtl_streaming(withRenotes=False, onReceive=onReceive)
    elif timeline == "list" and listId is not None:
        await api.list_streaming(listId, withRenotes=False, onReceive=onReceive)
    else:
        print(f"timeline の指定に誤りがあります。: {timeline}")

def on_note_recieved(data):
    note = Note(data["body"]["body"])
    print(note.id)
    print(note.text)


asyncio.run(my_loop())


