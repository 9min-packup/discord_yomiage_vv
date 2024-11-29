from .User import *

class DriveFile :

    def __init__(self, dict):
        self.id = dict["id"]
        self.createdAt = dict["createdAt"]
        self.name = dict["name"]
        self.type = dict["type"]
        self.md5 = dict["md5"]
        self.size = dict["size"]
        self.isSensitive = dict["isSensitive"]
        self.blurhash = dict["blurhash"]
        self.properties = dict["properties"]
        self.url = dict["url"]
        self.thumbnailUrl = dict["thumbnailUrl"]
        self.comment = dict["comment"]
        self.folderId = dict["folderId"]
        self.folder = dict["folder"]
        self.userId = dict["userId"]
        self.user = User(dict["user"]) if dict["user"] is not None else None

