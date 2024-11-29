from misskey_api import *
from logger import *
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

MISSKEY_CONFIG = config['misskey']
MISSKEY_HOST = MISSKEY_CONFIG['host']
MISSKEY_TOKEN = MISSKEY_CONFIG['token']
MISSEKY_LIST_ID = MISSKEY_CONFIG['list_id']

api = MisskeyApi(MISSKEY_HOST, MISSKEY_TOKEN)
logger = Logger()

async def main():
    try:
        r = await api.show_user()
        print(r)
    except Exception as e:
        print(e)
    await api.list_streaming(MISSKEY_TOKEN, MISSEKY_LIST_ID, withFiles=False, withRenotes=False)
    

asyncio.run(main())


