import os
import logging
import requests
import datetime
from urllib.parse import urlparse

from rcc.api.http import BaseHttpClient
from rcc.api.unms import auth
from rcc.exceptions import UNMSHTTPException

logger = logging.getLogger(__name__)


class UNMSClient(BaseHttpClient):
    def __init__(
        self,
        base_url,
        username,
        password,
        login_endpoint=None,
        users_endpoint=None,
        devices_endpoint=None,
        create_backup_endpoint=None,
        upload_backup_endpoint=None,
        delete_backup_endpoint=None,
        get_backup_endpoint=None,
        apply_backup_endpoint=None,
        reboot_device_endpoint=None,
        session_timeout=None,
        token_header=None,
        **kwargs,
    ):

        self.login_endpoint = login_endpoint or "/user/login"
        self.users_endpoint = users_endpoint or "/users"
        self.devices_endpoint = devices_endpoint
        self.create_backup_endpoint = (
            create_backup_endpoint or "/devices/{device_id}/backups"
        )
        self.upload_backup_endpoint = (
            upload_backup_endpoint or "/devices/{device_id}/backups"
        )
        self.delete_backup_endpoint = (
            delete_backup_endpoint or "/devices/{device_id}/backups/{backup_id}"
        )
        self.get_backup_endpoint = (
            get_backup_endpoint or "/devices/{device_id}/backups/{backup_id}"
        )
        self.apply_backup_endpoint = (
            apply_backup_endpoint or "/devices/{device_id}/backups/{backup_id}/apply"
        )
        self.reboot_device_endpoint = reboot_device_endpoint or "/devices/{device_id}"
        self.token_header = token_header or "x-auth-token"
        self.session_timeout = session_timeout or 3_600_000

        super().__init__(
            base_url=base_url, username=username, password=password, **kwargs
        )

        self.token, self.expire_time = self.get_token()

    def get_domain(self):
        parsed_uri = urlparse(self.base_url)
        return parsed_uri.netloc

    def get_session(self, use_auth=True):
        """Configure a requests session to use."""
        assert self.base_url is not None
        s = self.requests.Session()
        s.trust_env = False
        s.mount(self.base_url, self._get_adapter())
        if use_auth:
            s.auth = self.get_auth()
        return s

    def get_auth(self):
        if self.username and self.password:
            self.check_token()
            return auth.HeaderAuth(self)
        return self.username, self.password

    def get_token(self):
        token_url = f"{self.base_url}/{self.login_endpoint.lstrip('/')}"
        try:
            sess = self.get_session(use_auth=False)
            response = self.get_auth_token(sess, token_url)
            token = response.headers[self.token_header]
            sess.close()
            session_timeout_sec = self.session_timeout / 1000 / 60
            expire_time = datetime.datetime.now() + datetime.timedelta(
                seconds=session_timeout_sec / 2
            )
            return token, expire_time

        except requests.exceptions.ConnectionError as exc:
            raise UNMSHTTPException from exc
        except Exception as exc:
            logger.exception("Error while getting authentication token")
            raise UNMSHTTPException from exc

    def get_auth_token(self, session, token_url) -> requests.Response:
        return session.post(
            url=token_url,
            data={
                "password": self.password,
                "username": self.username,
                "sessionTimeout": self.session_timeout,
            },
            timeout=self.timeout,
        )

    def token_expired(self):
        if self.expire_time < datetime.datetime.now():
            return True
        return False

    def check_token(self):
        if self.token_expired():
            self.token, self.expire_time = self.get_token()

    def create_backup(self, device_id):
        endpoint = self.create_backup_endpoint.format(device_id=device_id)
        response = self.post_data(endpoint)
        response_body = response.json()
        return response_body["id"]

    def delete_backup(self, device_id, backup_id):
        endpoint = self.delete_backup_endpoint.format(
            device_id=device_id, backup_id=backup_id
        )
        response = self.delete_data(endpoint)
        return response.json()["result"]

    def get_backup(self, device_id, backup_id, filepath=None, replace_umns_key=False):
        endpoint = self.get_backup_endpoint.format(
            device_id=device_id, backup_id=backup_id
        )
        response = self.get_data(
            endpoint, params={"replaceUnmsKey": str(replace_umns_key).lower()}
        )
        if filepath:
            with open(filepath, "wb") as f:
                f.write(response.content)
            return filepath
        return response.content

    def upload_backup(self, device_id, filepath):
        endpoint = self.upload_backup_endpoint.format(device_id=device_id)
        files = {"file": (os.path.basename(filepath), open(filepath, "rb"))}
        response = self.put_data(endpoint, files=files)
        return response.json()["id"]

    def apply_backup(self, device_id, backup_id):
        endpoint = self.apply_backup_endpoint.format(
            device_id=device_id, backup_id=backup_id
        )
        response = self.post_data(endpoint)
        return response.json()

    def reboot_device(self, device_id):
        endpoint = self.reboot_device_endpoint.format(device_id)
        response = self.post_data(endpoint)
        return response.json()


if __name__ == "__main__":
    c = UNMSClient(
        base_url=os.environ["RCC_UNMS_BASE_URL"],
        username=os.environ["RCC_UNMS_USER"],
        password=os.environ["RCC_UNMS_PASSWORD"],
    )
    domain = c.get_domain()
    device_id = os.environ["RCC_DEVICE_ID"]
    backup_id = c.create_backup(os.environ["RCC_DEVICE_ID"])
    c.get_backup(device_id, backup_id, filepath="/tmp/test.tar.gz")
