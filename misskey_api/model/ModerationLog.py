from .User import *

class ModerationLog :

    def __init__(self, dict):
        self.id = dict["id"]
        self.createdAt = dict["createdAt"]
        self.type = dict["type"]
        self.info = dict["info"]
        self.userId = dict["userId"]
        self.user = User(dict["user"])

