import socket

from rcc.api.http import BaseHttpClient


class PublicIPAddress(BaseHttpClient):
    def __init__(self, base_url, ip_address_endpoint, **kwargs):
        self.ip_address_endpoint = ip_address_endpoint
        super().__init__(base_url=base_url, **kwargs)

    def get_public_ip_address(self):
        return self.get_data(self.ip_address_endpoint).text

    def dns_lookup(self, hostname=None, ip_address=None):
        assert bool(hostname) != bool(ip_address), "Must pass either a hostname or ip_address"
        if hostname:
            return socket.gethostbyname(hostname)
        return socket.gethostbyaddr(ip_address)
