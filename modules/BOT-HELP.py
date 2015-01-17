from modules import _BaseModule

class Module(_BaseModule.BaseModule):

    cmd = ".help"

    def __init__(self, msg, share):
        super(Module, self).__init__(msg, share)

    def main(self):
        self.sendpm(".mei [url] - upload a image to AB")
        self.sendpm(".8ball [question] - ask the mystical 8ball")
        self.sendpm(".poll <url/opt> <opt> - display poll results on AB")
        self.sendpm(".pick [args ...] - pick from list of choices separated by spaces")
        self.sendpm(".random <anime/manga/visual_novels> - randomize stuff")
        return
