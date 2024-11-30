from .model import *
from .exception import *
import json
import uuid
import aiohttp
import asyncio

class MisskeyApi:

    def __init__(self, host, token):
        self.host = host
        self.base_url = f"https://{host}"
        self.base_url_ws = f"wss://{host}"
        self.token = token

    async def request_api(self, endpoint, params):
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.base_url}/api/{endpoint}", json=params) as r:
                if r.status != 200:
                    raise BadApiRequestException(r.status, await r.text())
                return await r.text()

    async def show_user(self):
        params ={
            "i": self.token
        }
        text  = await self.request_api("i", params)
        return User(json.loads(text))

    async def search_user_by_id(self, userId):
        params ={
            "userId":  userId 
        }
        text  = await self.request_api("users/show", params)
        return User(json.loads(text))

    async def search_user_by_username(self, username):
        params ={
            "username":  username
        }
        text  = await self.request_api("users/show", params)
        return User(json.loads(text))

    async def create_note(self, text, cw = None, visibility = "public", visibleUserIds = None, localOnly = True, reactionAcceptance = None):
        params ={
            "i": self.token,
            "text": text,
            "cw" : cw,
            "visibility": visibility,
            "localOnly":  localOnly,
            "reactionAcceptance": reactionAcceptance,
        }
        if visibility == "specified" and visibleUserIds is not None and visibleUserIds is not []:
            if isinstance(visibleUserIds, list):
                params["visibleUserIds"] = visibleUserIds
            else:
                params["visibleUserIds"] = [visibleUserIds]
        await self.request_api("notes/create", params)
       
    async def show_moderation_logs(self, limit = 5, type = None, sinceId = None, untilId = None, userId = None):
        params ={
            'i': self.token,
            'limit': limit,
            'type': type,
            'userId': userId
        }
        if sinceId is not None:
            params["sinceId"] = sinceId
        if untilId is not None:
            params["untilId"] = untilId
        text  = await self.request_api("admin/show-moderation-logs", params)
        array = json.loads(text)
        moderation_logs = []
        for i in array:
            moderation_logs.append(ModerationLog(i))
        return moderation_logs

    async def gtl_streaming(self, token, withFiles=False, withRenotes=True, onReceive=None):
        conntection_data = {
            "type": "connect",
            "body": {
                "channel": "globalTimeline",
                "id": str(uuid.uuid4()),
                "params": {
                    "withFiles": withFiles,
                    "withRenotes": withRenotes
                }       
            }
        }
        await self.request_streaming(token, conntection_data, onReceive)

    async def ltl_streaming(self, token, withReplies=False, withFiles=False, withRenotes=True, onReceive=None):
        conntection_data = {
            "type": "connect",
            "body": {
                "channel": "localTimeline",
                "id": str(uuid.uuid4()),
                "params": {
                    "withFiles": withFiles,
                    "withReplies": withReplies,
                    "withRenotes": withRenotes
                }       
            }
        }
        await self.request_streaming(token, conntection_data, onReceive)

    async def htl_streaming(self, token, withFiles=False, withRenotes=True, onReceive=None):
        conntection_data = {
            "type": "connect",
            "body": {
                "channel": "homeTimeline",
                "id": str(uuid.uuid4()),
                "params": {
                    "withFiles": withFiles,
                    "withRenotes": withRenotes
                }       
            }
        }
        await self.request_streaming(token, conntection_data, onReceive)

    async def list_streaming(self, token, listId, withFiles=False, withRenotes=True, onReceive=None):
        conntection_data = {
            "type": "connect",
            "body": {
                "channel": "userList",
                "id": str(uuid.uuid4()),
                "params": {
                    "listId": listId,
                    "withFiles": withFiles,
                    "withRenotes": withRenotes
                }       
            }
        }
        await self.request_streaming(token, conntection_data, onReceive)

    async def request_streaming(self, token, conntection_data, onReceive=None):
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(f"{self.base_url_ws}/streaming?i={token}", method="GET") as ws:
                await ws.send_json(conntection_data)
                async for msg in ws:
                    if msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                        print('close: ', aiohttp.WSMsgType)
                        break
                    if msg.type == aiohttp.WSMsgType.TEXT and onReceive is not None:
                        onReceive(msg.json())


