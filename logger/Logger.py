from .Color import *

class Logger:
    def log(self, message, color = Color.DEFAULT):
        print(color + message + Color.RESET)