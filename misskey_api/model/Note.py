from .DriveFile import *

class Note :

    def __init__(self, dict):
        self.id = dict["id"]
        self.text = dict["text"]
        self.createdAt = dict["createdAt"]
        self.fileIds = dict["fileIds"]
        self.files = []
        for obj in dict["files"]:
            self.files.appenf(DriveFile(obj))
        dict["files"]
        self.text = dict["text"]
        self.text = dict["text"]
        self.text = dict["text"]
        self.text = dict["text"]
        self.text = dict["text"]
        self.text = dict["text"]
        self.text = dict["text"]
        self.text = dict["text"]
        self.text = dict["text"]
        self.text = dict["text"]
        self.text = dict["text"]
        self.text = dict["text"]
