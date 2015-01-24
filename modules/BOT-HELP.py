from modules import _BaseModule

class Module(_BaseModule.BaseModule):

    cmd = ".help"

    def __init__(self, msg, share):
        super(Module, self).__init__(msg, share)

    def main(self):
        self.sendpm(".mei [url] [, *] - upload an image to AB's Image Uploader. Allows ImageMagick commands.")
        self.sendpm(".random [anime | manga | visual_novels] - return a random anime, manga, or visual novel from the site.")
        self.sendpm(".poll [name | url] - get results of a poll on AB - even if you didn't vote! (set name with .poll [url] [name]).")
        self.sendpm(".pick [arg] [, ...] - pick from a list of choices separated by spaces.")
        self.sendpm(".8ball [question] - ask the mystical 8ball, ridiculously accurate.")
        return
