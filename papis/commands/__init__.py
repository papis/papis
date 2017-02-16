
class Command(object):

    def __init__(self, parser):
        self.parser = parser
        self.args = None

    def initialize_parser(self):
        pass

    def main(self, args=None):
        if not args:
            self.args = args
