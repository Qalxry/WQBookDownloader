import requests
from requests import Response, exceptions

from wqdl.webdriver_manager.core.config import ssl_verify
from wqdl.webdriver_manager.core.logger import log

class HttpClient:
    def get(self, url, params=None, **kwargs) -> Response:
        raise NotImplementedError

    @staticmethod
    def validate_response(resp: requests.Response):
        status_code = resp.status_code
        if status_code == 404:
            raise ValueError(f"There is no such driver by url {resp.url}")
        elif status_code == 401:
            raise ValueError(f"API Rate limit exceeded. You have to add GH_TOKEN!!!")
        elif resp.status_code != 200:
            raise ValueError(
                f"response body:\n{resp.text}\n"
                f"request url:\n{resp.request.url}\n"
                f"response headers:\n{dict(resp.headers)}\n"
            )


class WDMHttpClient(HttpClient):
    def __init__(self):
        self._ssl_verify = ssl_verify()

    def get(self, url, **kwargs) -> Response:
        # try:
        #     resp = requests.get(url=url, verify=self._ssl_verify, stream=True, **kwargs)
        # except exceptions.ConnectionError:
        #     raise exceptions.ConnectionError(f"Could not reach host. Are you offline?")
        # self.validate_response(resp)
        # return resp

        for i in range(3 + 1):
            try:
                resp = requests.get(url=url, timeout=5, stream=True, **kwargs)
                self.validate_response(resp)
                return resp
            except Exception as e:
                log(f"({i+1}/3) Error: {e}")
                if i == 3:
                    raise exceptions.ConnectionError(f"Could not reach host. Are you offline?")


