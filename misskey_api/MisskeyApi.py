from .model import *
from .exception import *
import json
import aiohttp
import asyncio

class MisskeyApi:

    def __init__(self, host, token):
        self.host = host
        self.base_url = f"https://{host}"
        self.base_url_webhook = f"wss://{host}"
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



