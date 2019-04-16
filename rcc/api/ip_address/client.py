from rcc.api.http import BaseHttpClient


class PublicIPAddress(BaseHttpClient):
    def __init__(self, base_url, ip_address_endpoint, **kwargs):
        self.ip_address_endpoint = ip_address_endpoint
        super().__init__(base_url=base_url, **kwargs)

    def get_public_ip_address(self):
        return self.get_data(self.ip_address_endpoint).text
