class CustomEmoji :

    def __init__(self, dict):
        self.id = dict["id"]
        self.aliases = dict["aliases"]
        self.name = dict["name"]
        self.category = dict["category"]
        self.host = dict["host"]
        self.publicUrl = dict["publicUrl"]
        self.originalUrl = dict["originalUrl"]
        self.license = dict["license"]
        self.isSensitive = dict["isSensitive"]
        self.localOnly = dict["localOnly"]
        self.roleIdsThatCanBeUsedThisEmojiAsReaction = dict["roleIdsThatCanBeUsedThisEmojiAsReaction"]

