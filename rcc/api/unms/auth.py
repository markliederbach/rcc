from requests.auth import AuthBase


class HeaderAuth(AuthBase):

    def __init__(self, client):
        self.client = client

    def __call__(self, r):
        self.client.check_token()
        r.headers[self.client.token_header] = self.client.token
        return r
