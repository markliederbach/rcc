import time
import logging
import threading
import requests
import certifi
from rcc.exceptions import HTTPException


logger = logging.getLogger(__name__)


class BaseHttpClient:
    requests = requests
    certifi = certifi

    def __init__(
        self,
        base_url=None,
        username=None,
        password=None,
        timeout=10,
        verify=True,
        use_ssl3=False,
    ):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.timeout = timeout
        self.verify = verify
        self.use_ssl3 = use_ssl3
        self.threaded_session = {}
        self._cache_limit = 300  # 5 minutes
        self._cache = {}

    def __str__(self):
        return "[{}: {}]".format(self.__class__.__name__, self.base_url)

    def get_session(self):
        """Configure a requests session to use."""
        assert self.base_url is not None
        s = self.requests.Session()
        s.trust_env = False
        # s.verify = self.certifi.where() if self.verify else False
        s.mount(self.base_url, self._get_adapter())
        if self.username and self.password:
            s.auth = (self.username, self.password)
        return s

    def _get_adapter(self):
        """Use logic to determine what Adaptor is required."""
        return self.requests.adapters.HTTPAdapter()

    def __enter__(self):
        """For use as a context statement. You can simply say:
        with self as session:
            session.get(...)

        This will open and provide a session to use for requests,
        then close it when complete, using __exit__."""
        self.threaded_session[threading.currentThread().ident] = self.get_session()
        return self.threaded_session[threading.currentThread().ident]

    def __exit__(self, *exc):
        """Used to close context statement."""
        self.threaded_session[threading.currentThread().ident].close()
        self.threaded_session[threading.currentThread().ident] = None
        return False

    def get_data(self, endpoint, params=None) -> requests.Response:
        response = self._get_data_for_request(endpoint, params)
        return response

    def _get_data_for_request(self, endpoint, params=None):
        response = None
        try:
            target_url = "{}{}".format(self.base_url, endpoint)
            with self as session:
                response = session.get(
                    target_url,
                    timeout=self.timeout,
                    params=params if params is not None else {},
                )
                logger.debug(
                    f"Response[{response.status_code}] for {target_url}:\nHeaders:{response.headers}\nContent:\n{response.text}"
                )
        except requests.exceptions.ConnectionError as e:
            raise HTTPException(e)
        except Exception as e:
            raise HTTPException(e)
        return response

    def post_data(self, endpoint, payload=None) -> requests.Response:
        response = self._post_data_for_request(endpoint, payload)
        return response

    def _post_data_for_request(self, endpoint, payload=None):
        response = None
        try:
            target_url = "{}{}".format(self.base_url, endpoint)
            with self as session:
                response = session.post(
                    target_url,
                    timeout=self.timeout,
                    json=payload or {},
                )
                logger.debug(
                    f"Response[{response.status_code}] for {target_url}:\nHeaders:{response.headers}\nContent:\n{response.text}"
                )
        except requests.exceptions.ConnectionError as e:
            raise HTTPException(e)
        except Exception as e:
            raise HTTPException(e)
        return response

    def delete_data(self, endpoint):
        response = self._delete_for_request(endpoint)
        return response

    def _delete_for_request(self, endpoint):
        response = None
        try:
            target_url = "{}{}".format(self.base_url, endpoint)
            with self as session:
                response = session.delete(
                    target_url, timeout=self.timeout
                )
                logger.debug(
                    f"Response[{response.status_code}] for {target_url}:\nHeaders:{response.headers}\nContent:\n{response.text}"
                )
        except requests.exceptions.ConnectionError as e:
            raise HTTPException(e)
        except Exception as e:
            raise HTTPException(e)
        return response

    def put_data(self, endpoint, params=None, files=None):
        response = self._put_for_request(endpoint, params=params, files=files)
        return response

    def _put_for_request(self, endpoint, params=None, files=None):
        response = None
        try:
            target_url = "{}{}".format(self.base_url, endpoint)
            with self as session:
                response = session.put(
                    target_url,
                    timeout=self.timeout,
                    files=files,
                    params=params or {},
                )
                logger.debug(
                    f"Response[{response.status_code}] for {target_url}:\nHeaders:{response.headers}\nContent:\n{response.text}"
                )
        except requests.exceptions.ConnectionError as e:
            raise HTTPException(e)
        except Exception as e:
            raise HTTPException(e)
        return response

    def get_cache(self, key):
        if key in self._cache and self._cache[key]["expires"] > time.time():
            return self._cache[key]["obj"]
        return None

    def set_cache(self, key, obj):
        self._cache[key] = {"obj": obj, "expires": time.time() + self._cache_limit}

    def clean_cache(self, key=None):
        if key is not None:
            self._cache.pop(key)
        else:
            for key in list(self._cache):
                if self._cache[key]["expires"] <= time.time():
                    self._cache.pop(key)
