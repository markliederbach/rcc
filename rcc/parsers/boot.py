import os

from rcc.parsers.temp_parser import parse_conf


class BootParser:
    def __init__(self, filepath):
        self.filepath = filepath
        self.raw_data = self.load_file(self.filepath)

    def load_file(self, filepath):
        with open(filepath, "r") as c:
            return c.read()


if __name__ == "__main__":
    filepath = os.environ["RCC_CONFIG_FILE"]
    b = BootParser(filepath)
