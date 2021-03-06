import os
import re
import stat
from rcc.parsers.temp_parser import parse_conf


class BootParser:
    re_netflow_server = re.compile(
        r"(system[\s*]\{[\n\t\r\s]*flow-accounting[\s*]\{[\n\t\r\s\w\W]*netflow[\s*]\{[\n\t\r\s\w\W]*server[\s*])(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
    )

    def __init__(self, filepath):
        self.filepath = filepath
        self.raw_data = self.load_file(self.filepath)
        self.conf_obj = self.parse_conf(self.raw_data)

    def load_file(self, filepath):
        with open(filepath, "r") as c:
            return c.read()

    def parse_conf(self, raw_data):
        return parse_conf(raw_data)

    def find_netflow_server(self):
        res = re.search(self.re_netflow_server, self.raw_data)
        if res:
            return res.group(2)
        return None

    def set_netflow_server(self, ip_address):
        if ip_address != self.find_netflow_server():
            self.raw_data = re.sub(
                self.re_netflow_server, r"\g<1>{}".format(ip_address), self.raw_data
            )
            self.conf_obj = self.parse_conf(self.raw_data)

    def dump(self, path=None):
        path = path or self.filepath
        if os.path.exists(path):
            os.chmod(path, stat.S_IWUSR | stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
        with open(path or self.filepath, "w") as c:
            c.write(self.raw_data)
